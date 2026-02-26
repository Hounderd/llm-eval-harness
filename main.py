import asyncio
import os
import argparse
from dotenv import load_dotenv

from db import get_db_pool, init_db
from models import PromptSuite, TestCase, ModelProvider
from evaluator import Evaluator
from scorers import CorrectnessScorer, CoherenceScorer, SafetyScorer

load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="LLM Eval Harness")
    parser.add_argument("--test-run", action="store_true", help="Run a sample evaluation suite")
    parser.add_argument("--init-db", action="store_true", help="Initialize the database schema")
    
    args = parser.parse_args()
    
    # Initialize DB connection
    pool = await get_db_pool()
    
    if args.init_db:
        print("Initializing database schema...")
        await init_db(pool)
        print("Database initialized successfully.")
    
    if args.test_run:
        print("Running sample evaluation suite...")
        
        # Example Test Suite
        sample_suite = PromptSuite(
            name="Math and Logic Eval v1",
            description="A simple test suite to verify math and logic capabilities.",
            test_cases=[
                TestCase(
                    prompt="What is 25 * 4? Return only the number.",
                    target_model="llama-3.3-70b-versatile",
                    provider=ModelProvider.GROQ,
                    expected_constraints={"format": "number only", "answer": 100}
                ),
                TestCase(
                    prompt="Explain why the sky is blue in exactly one sentence.",
                    target_model="gemini-2.0-flash",
                    provider=ModelProvider.GEMINI,
                    expected_constraints={"sentences": 1}
                )
            ]
        )
        
        # Setup scorers
        scorers = [
            CorrectnessScorer(judge_model_name="llama-3.3-70b-versatile"),
            CoherenceScorer(judge_model_name="llama-3.3-70b-versatile"),
            SafetyScorer(judge_model_name="llama-3.3-70b-versatile")
        ]
        
        # Initialize evaluator
        evaluator = Evaluator(db_pool=pool, max_concurrency=3)
        
        # Run suite
        results = await evaluator.run_suite(sample_suite, scorers)
        
        print(f"\nCompleted {len(results)} evaluations:\n")
        for res in results:
            print(f"Prompt: {res.test_case.prompt}")
            print(f"Target Model: {res.test_case.target_model}")
            print(f"Response: {res.response.strip()}")
            if res.error:
                print(f"Error: {res.error}")
            for score in res.scores:
                print(f" - {score.rubric_name.capitalize()} Score: {score.score} ({score.reasoning})")
            print("-" * 40)
            
    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
