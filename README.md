# LLM Eval Harness

A modern, fast, and extensible evaluation harness for Large Language Models (LLMs). It allows you to run prompts against multiple LLM providers (OpenAI, Anthropic, Google Gemini, Groq), score the responses using a judge model (scoring Correctness, Coherence, and Safety), and view the results in a beautiful React dashboard.

## Features

- **Multi-Provider Support**: Built-in support for OpenAI, Anthropic, Google Gemini, and Groq.
- **Automated LLM Judges**: Uses a configurable judge model to automatically score responses based on specific rubrics.
- **FastAPI Backend**: Asynchronous scoring and database management.
- **React + Vite Frontend**: A sleek, dark-themed, glassmorphic UI for building test cases and analyzing runs.
- **PostgreSQL Database**: Persistent storage of suites, evaluation runs, and scores.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm (for the frontend)
- Docker (for standing up the PostgreSQL database)
- API Keys for the providers you want to use (e.g., Groq, Gemini)

### 1. Database Setup

The easiest way to get the database running is to use Docker:
```bash
docker run --name evaldb -e POSTGRES_PASSWORD=p455word -e POSTGRES_USER=postgres -e POSTGRES_DB=evaldb -p 5432:5432 -d postgres
```

### 2. Backend Setup (FastAPI)

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory (copy the format from `.env.example` if available). 
   ```env
   DATABASE_URL=postgresql://postgres:p455word@localhost:5432/evaldb
   GROQ_API_KEY=your_groq_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   # Add OpenAI and Anthropic keys if using them
   ```

4. **Initialize the Database**:
   ```bash
   python main.py --init-db
   ```

5. **Run the API Server**:
   ```bash
   uvicorn api:app --reload --port 8000
   ```

### 3. Frontend Setup (React)

1. Open a new terminal and navigate to the `frontend` folder.
2. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```
3. **Start the Vite dev server**:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:5173`.

---

## 🎨 UI Overview

- **Dashboard**: View high-level metrics across all your evaluations, and see your recent runs and average scores at a glance.
- **Suite Builder**: Add multiple test cases in a single "suite", pick different target models from different providers to benchmark them against each other, and specify hard JSON constraints.
- **Result Detail**: Dive into a specific response to see the exact scoring breakdown and the judge's rationale.

## 🛠️ Architecture

- `api.py`: FastAPI endpoints serving the frontend.
- `evaluator.py`: The core evaluation engine that dispatches prompts to target models and triggers the scoring pipeline.
- `scorers.py`: The LLM Judges. Defines `CorrectnessScorer`, `CoherenceScorer`, and `SafetyScorer`.
- `providers.py`: API wrappers for `AsyncOpenAI`, `AsyncAnthropic`, `Groq`, and `Google Gemini`.
- `db.py`: Async database setup and queries using `asyncpg`.
- `frontend/`: A React 18 single page application styled with custom CSS variables.
##
Created with ❤️ by [Hounderd](https://github.com/Hounderd).
