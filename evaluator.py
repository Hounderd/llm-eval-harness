import asyncio
from typing import List, Optional
from models import PromptSuite, TestCase, EvaluationResult, ModelProvider
from providers import LLMProvider, AsyncOpenAIProvider, AsyncAnthropicProvider, GroqProvider, GeminiProvider
from scorers import Scorer
import db
from asyncpg import Pool

class Evaluator:
    def __init__(self, db_pool: Pool, max_concurrency: int = 5, judge_provider: Optional[LLMProvider] = None):
        self.db_pool = db_pool
        self.semaphore = asyncio.Semaphore(max_concurrency)
        try:
            self.providers = {}
            # Initialize providers lazily or skip if env vars are missing so we can at least load the module.
            try:
                self.providers[ModelProvider.OPENAI] = AsyncOpenAIProvider()
            except ValueError:
                pass
            try:
                self.providers[ModelProvider.ANTHROPIC] = AsyncAnthropicProvider()
            except ValueError:
                pass
            try:
                self.providers[ModelProvider.GROQ] = GroqProvider()
            except ValueError:
                pass
            try:
                self.providers[ModelProvider.GEMINI] = GeminiProvider()
            except ValueError:
                pass
        except Exception as e:
            print(f"Warning: Failed to init providers directly: {e}")
            self.providers = {}
            
        self.judge_provider = judge_provider

    async def evaluate_test_case(self, suite_id: int, test_case: TestCase, scorers: List[Scorer]) -> EvaluationResult:
        async with self.semaphore:
            provider = self.providers.get(test_case.provider)
            if not provider:
                return EvaluationResult(
                    test_case=test_case, 
                    response="", 
                    scores=[], 
                    error=f"Provider {test_case.provider} not supported or API key missing."
                )

            try:
                # 1. Generate response
                response_text = await provider.generate(test_case.target_model, test_case.prompt)
                
                # 2. Score response
                judge_to_use = self.judge_provider if self.judge_provider else provider
                score_tasks = [
                    scorer.score(test_case, response_text, judge_llm=judge_to_use)
                    for scorer in scorers
                ]
                scores = await asyncio.gather(*score_tasks, return_exceptions=True)
                
                # Filter out exceptions in scoring and format them
                valid_scores = []
                for s in scores:
                    if isinstance(s, Exception):
                        print(f"Scoring error: {s}")
                    else:
                        valid_scores.append(s)
                
                # 3. Save to database
                db_scores = {s.rubric_name: {'score': s.score, 'reasoning': s.reasoning} for s in valid_scores}
                await db.save_evaluation(
                    self.db_pool,
                    suite_id=suite_id,
                    model_name=test_case.target_model,
                    prompt=test_case.prompt,
                    response=response_text,
                    scores=db_scores
                )
                
                return EvaluationResult(test_case=test_case, response=response_text, scores=valid_scores)
            except Exception as e:
                return EvaluationResult(test_case=test_case, response="", scores=[], error=str(e))

    async def run_suite(self, suite: PromptSuite, scorers: List[Scorer]) -> List[EvaluationResult]:
        suite_id = await db.create_suite(self.db_pool, suite.name)
        
        tasks = [
            self.evaluate_test_case(suite_id, test_case, scorers)
            for test_case in suite.test_cases
        ]
        
        results = await asyncio.gather(*tasks)
        return results
