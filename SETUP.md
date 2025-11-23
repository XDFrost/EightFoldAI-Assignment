# Project Setup Guide

This guide will help you set up the EightFold AI project, which consists of three main components:
1.  **Ai-Service**: Python-based AI backend (FastAPI, LangGraph).
2.  **backend**: Node.js business logic backend (Express, Auth).
3.  **frontend**: React-based user interface.

## Prerequisites

-   **Node.js** (v20.19+ recommended)
-   **Python** (v3.11+)
-   **uv** (Python package manager) - [Install uv](https://github.com/astral-sh/uv)
-   **Supabase Account** (for Database & Auth)
-   **Pinecone Account** (for Vector Database)
-   **Google Gemini API Key** (for Embeddings/LLM)
-   **Tavily API Key** (for Search)
-   **Perplexity API Key** (for Search)

---

## 1. Database Setup (Supabase)

1.  Create a new Supabase project.
2.  Note down your `SUPABASE_URL`, `SUPABASE_KEY` and `DATABASE_URL`
3.  Run the ai-service, it'll automatically create the DB tables.

---

## 2. Ai-Service Setup (Python)

Navigate to the `Ai-Service` directory:
```bash
cd Ai-Service
```

### Environment Variables
Create a `.env` file in `Ai-Service/` with the details inside .env.example
### Install Dependencies
```bash
uv sync
```

### Configuration
- **Project Configuration**: You can customize all project configurations in `Ai-Service/app/Config/dataConfig.py`.
- **Prompts**: You can customize all system prompts in `app/Config/promptConfig.py`.
- **Queries**: You can customize all queries `app/Config/queryConfig.py`.

### Run the Service
```bash
uv run main.py
```
The service will start on `http://localhost:8000`.

### Run Tests
```bash
cd tests
uv run tests.py
```

---

## 3. Business Backend Setup (Node.js)

Navigate to the `backend` directory:
```bash
cd backend
```

### Environment Variables
Create a `.env` file in `backend/` with the details inside .env.example
### Install Dependencies
```bash
npm install
```

### Run the Server
```bash
node src/index.js
```
The server will start on `http://localhost:3000`.

---

## 4. Frontend Setup (React)

Navigate to the `frontend` directory:
```bash
cd frontend
```

### Environment Variables
### Environment Variables
Create a `.env` file in `frontend/` with the following content:
```env
VITE_API_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:8000
```

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```
The app will be available at `http://localhost:5173`.

---

## Summary of Ports

-   **Frontend**: `5173`
-   **Business Backend**: `3000`
-   **AI Service**: `8000`

Ensure all services are running for the full application to function correctly.

NOTE: MAKE SURE JWT SECRET IS SET SAME IN BOTH AI-SERVICE AND BACKEND