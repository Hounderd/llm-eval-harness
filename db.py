import asyncpg
import os
import json

async def get_db_pool():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return await asyncpg.create_pool(db_url)

async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_suites (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS evaluations (
                id SERIAL PRIMARY KEY,
                suite_id INTEGER REFERENCES evaluation_suites(id),
                model_name VARCHAR(255) NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS scores (
                id SERIAL PRIMARY KEY,
                evaluation_id INTEGER REFERENCES evaluations(id),
                rubric_name VARCHAR(255) NOT NULL,
                score NUMERIC NOT NULL,
                reasoning TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        ''')

async def save_evaluation(pool, suite_id: int, model_name: str, prompt: str, response: str, scores: dict):
    """
    scores is a dict mapping rubric_name -> dict(score=..., reasoning=...)
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            eval_id = await conn.fetchval('''
                INSERT INTO evaluations (suite_id, model_name, prompt, response)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            ''', suite_id, model_name, prompt, response)
            
            for rubric_name, score_data in scores.items():
                await conn.execute('''
                    INSERT INTO scores (evaluation_id, rubric_name, score, reasoning)
                    VALUES ($1, $2, $3, $4)
                ''', eval_id, rubric_name, score_data.get('score'), score_data.get('reasoning'))
        return eval_id

async def create_suite(pool, name: str):
    async with pool.acquire() as conn:
        return await conn.fetchval('''
            INSERT INTO evaluation_suites (name)
            VALUES ($1)
            RETURNING id
        ''', name)
