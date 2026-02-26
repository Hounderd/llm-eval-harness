import asyncio
import os
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from db import get_db_pool, init_db
from models import PromptSuite, TestCase, ModelProvider
from evaluator import Evaluator
from scorers import CorrectnessScorer, CoherenceScorer, SafetyScorer
from providers import GroqProvider

# ---------------------------------------------------------------------------
# Lifespan – create / close the DB pool once for the app lifetime
# ---------------------------------------------------------------------------
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await get_db_pool()
    yield
    await db_pool.close()

app = FastAPI(title="LLM Eval Harness API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class TestCaseRequest(BaseModel):
    prompt: str
    target_model: str
    provider: str          # "groq" | "gemini" | "openai" | "anthropic"
    expected_constraints: Optional[Dict[str, Any]] = None

class RunSuiteRequest(BaseModel):
    name: str
    description: Optional[str] = None
    judge_model: str = "llama-3.3-70b-versatile"
    test_cases: List[TestCaseRequest]

class ScoreResponse(BaseModel):
    rubric_name: str
    score: float
    reasoning: Optional[str]

class EvaluationResponse(BaseModel):
    id: int
    suite_id: int
    suite_name: str
    model_name: str
    provider: str
    prompt: str
    response: str
    scores: List[ScoreResponse]
    error: Optional[str] = None

class SuiteResponse(BaseModel):
    id: int
    name: str
    created_at: str
    evaluation_count: int

class ProvidersResponse(BaseModel):
    providers: Dict[str, List[str]]
    default_judge: str

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/providers", response_model=ProvidersResponse)
async def get_providers():
    """Return available providers and suggested models."""
    return {
        "providers": {
            "groq": [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "gemma2-9b-it",
                "mixtral-8x7b-32768",
            ],
            "gemini": [
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ],
            "openai": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-3.5-turbo",
            ],
            "anthropic": [
                "claude-3-5-sonnet-20241022",
                "claude-3-haiku-20240307",
            ],
        },
        "default_judge": "llama-3.3-70b-versatile",
    }


@app.get("/api/suites", response_model=List[SuiteResponse])
async def list_suites():
    """Return all evaluation suites with evaluation counts."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                s.id,
                s.name,
                s.created_at,
                COUNT(e.id) AS evaluation_count
            FROM evaluation_suites s
            LEFT JOIN evaluations e ON e.suite_id = s.id
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """)
    return [
        SuiteResponse(
            id=r["id"],
            name=r["name"],
            created_at=r["created_at"].isoformat(),
            evaluation_count=r["evaluation_count"],
        )
        for r in rows
    ]


@app.post("/api/run", response_model=List[EvaluationResponse])
async def run_suite(request: RunSuiteRequest):
    """Create and immediately run an evaluation suite, returning all results."""
    # Map provider strings to enum values
    provider_map = {
        "groq": ModelProvider.GROQ,
        "gemini": ModelProvider.GEMINI,
        "openai": ModelProvider.OPENAI,
        "anthropic": ModelProvider.ANTHROPIC,
    }

    test_cases = []
    for tc in request.test_cases:
        provider_enum = provider_map.get(tc.provider.lower())
        if not provider_enum:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {tc.provider}")
        test_cases.append(TestCase(
            prompt=tc.prompt,
            target_model=tc.target_model,
            provider=provider_enum,
            expected_constraints=tc.expected_constraints,
        ))

    suite = PromptSuite(
        name=request.name,
        description=request.description,
        test_cases=test_cases,
    )

    scorers = [
        CorrectnessScorer(judge_model_name=request.judge_model),
        CoherenceScorer(judge_model_name=request.judge_model),
        SafetyScorer(judge_model_name=request.judge_model),
    ]

    evaluator = Evaluator(db_pool=db_pool, max_concurrency=5)
    results = await evaluator.run_suite(suite, scorers)

    # Fetch the suite_id that was just inserted
    async with db_pool.acquire() as conn:
        suite_row = await conn.fetchrow(
            "SELECT id FROM evaluation_suites WHERE name = $1 ORDER BY created_at DESC LIMIT 1",
            request.name
        )
    suite_id = suite_row["id"] if suite_row else 0

    responses = []
    for i, res in enumerate(results):
        tc = request.test_cases[i]
        responses.append(EvaluationResponse(
            id=i,
            suite_id=suite_id,
            suite_name=request.name,
            model_name=res.test_case.target_model,
            provider=tc.provider,
            prompt=res.test_case.prompt,
            response=res.response,
            scores=[ScoreResponse(rubric_name=s.rubric_name, score=s.score, reasoning=s.reasoning) for s in res.scores],
            error=res.error,
        ))

    return responses


@app.get("/api/results", response_model=List[EvaluationResponse])
async def list_results(limit: int = 50, suite_id: Optional[int] = None):
    """Return recent evaluation results with scores."""
    async with db_pool.acquire() as conn:
        if suite_id:
            rows = await conn.fetch("""
                SELECT e.id, e.suite_id, s.name as suite_name, e.model_name, e.prompt, e.response
                FROM evaluations e
                JOIN evaluation_suites s ON s.id = e.suite_id
                WHERE e.suite_id = $1
                ORDER BY e.created_at DESC
                LIMIT $2
            """, suite_id, limit)
        else:
            rows = await conn.fetch("""
                SELECT e.id, e.suite_id, s.name as suite_name, e.model_name, e.prompt, e.response
                FROM evaluations e
                JOIN evaluation_suites s ON s.id = e.suite_id
                ORDER BY e.created_at DESC
                LIMIT $1
            """, limit)

        results = []
        for r in rows:
            score_rows = await conn.fetch(
                "SELECT rubric_name, score, reasoning FROM scores WHERE evaluation_id = $1",
                r["id"]
            )
            # Try to infer provider from model name
            model = r["model_name"]
            if "llama" in model or "gemma" in model or "mixtral" in model:
                provider = "groq"
            elif "gemini" in model:
                provider = "gemini"
            elif "gpt" in model:
                provider = "openai"
            elif "claude" in model:
                provider = "anthropic"
            else:
                provider = "unknown"

            results.append(EvaluationResponse(
                id=r["id"],
                suite_id=r["suite_id"],
                suite_name=r["suite_name"],
                model_name=r["model_name"],
                provider=provider,
                prompt=r["prompt"],
                response=r["response"],
                scores=[ScoreResponse(rubric_name=s["rubric_name"], score=float(s["score"]), reasoning=s["reasoning"]) for s in score_rows],
            ))
    return results


@app.get("/api/results/{eval_id}", response_model=EvaluationResponse)
async def get_result(eval_id: int):
    """Return a single evaluation by ID."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT e.id, e.suite_id, s.name as suite_name, e.model_name, e.prompt, e.response
            FROM evaluations e
            JOIN evaluation_suites s ON s.id = e.suite_id
            WHERE e.id = $1
        """, eval_id)
        if not row:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        score_rows = await conn.fetch(
            "SELECT rubric_name, score, reasoning FROM scores WHERE evaluation_id = $1",
            eval_id
        )

    model = row["model_name"]
    if "llama" in model or "gemma" in model or "mixtral" in model:
        provider = "groq"
    elif "gemini" in model:
        provider = "gemini"
    elif "gpt" in model:
        provider = "openai"
    elif "claude" in model:
        provider = "anthropic"
    else:
        provider = "unknown"

    return EvaluationResponse(
        id=row["id"],
        suite_id=row["suite_id"],
        suite_name=row["suite_name"],
        model_name=row["model_name"],
        provider=provider,
        prompt=row["prompt"],
        response=row["response"],
        scores=[ScoreResponse(rubric_name=s["rubric_name"], score=float(s["score"]), reasoning=s["reasoning"]) for s in score_rows],
    )


@app.get("/api/stats")
async def get_stats():
    """Dashboard summary stats."""
    async with db_pool.acquire() as conn:
        total_evals = await conn.fetchval("SELECT COUNT(*) FROM evaluations")
        total_suites = await conn.fetchval("SELECT COUNT(*) FROM evaluation_suites")
        avg_scores = await conn.fetch("""
            SELECT rubric_name, ROUND(AVG(score)::numeric, 3) as avg_score
            FROM scores
            GROUP BY rubric_name
        """)
    return {
        "total_evaluations": total_evals,
        "total_suites": total_suites,
        "average_scores": {r["rubric_name"]: float(r["avg_score"]) for r in avg_scores},
    }
