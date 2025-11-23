# Veritas - Intelligent Research Agent

Veritas is an advanced AI-powered research assistant designed to autonomously generate, refine, and manage comprehensive account plans and research reports. It leverages a multi-agent architecture to perform deep web research, synthesize information, and interact with users in real-time.

## Architecture Overview

The project follows a modern **microservices architecture** consisting of three main components:

1.  **Frontend (React)**: A responsive, interactive UI for chatting with the agent and viewing research results.
2.  **Business Backend (Node.js)**: Handles user authentication, session management, and analytics.
3.  **AI Service (Python)**: The core intelligence engine powered by LangGraph, responsible for research orchestration, RAG, and LLM interactions.

```mermaid
graph TD
    User[User] -->|HTTPS/WSS| Frontend[Frontend (React)]
    Frontend -->|REST API| NodeBE[Business Backend (Node.js)]
    Frontend -->|WebSocket| PythonBE[AI Service (Python)]
    
    NodeBE -->|Auth/Data| DB[(Supabase Postgres)]
    PythonBE -->|Read/Write| DB
    
    PythonBE -->|Vector Search| Pinecone[(Pinecone Vector DB)]
    PythonBE -->|LLM Calls| Gemini[Google Gemini API]
    PythonBE -->|Search| Tavily[Tavily API]
    PythonBE -->|Search| Perplexity[Perplexity API]
```

---

## 🛠️ Tech Stack

### **Frontend**
*   **Framework**: React 19 (via Vite)
*   **Styling**: Tailwind CSS (Utility-first styling for rapid UI development)
*   **Icons**: Lucide React (Consistent, clean iconography)
*   **Animations**: Anime.js + **Framer Motion** (Smooth page transitions and "Thinking" states)
*   **Markdown**: `react-markdown` + `remark-gfm` (Rich text rendering for AI responses)
*   **State Management**: React Context API (Auth & Theme)

### **Business Backend**
*   **Runtime**: Node.js
*   **Framework**: Express.js (Lightweight, unopinionated web framework)
*   **Database**: PostgreSQL (via Supabase)
*   **Authentication**: JWT (JSON Web Tokens) + bcrypt (Password hashing)
*   **Validation**: Middleware-based request validation

### **AI Service**
*   **Runtime**: Python 3.11+
*   **Framework**: FastAPI (High-performance async web framework)
*   **Orchestration**: **LangGraph** (Stateful, cyclic multi-agent workflows)
*   **Configuration**: Centralized `promptConfig.py` for easy prompt management.
*   **LLM Integration**: LangChain (Unified interface for LLMs and Embeddings)
*   **Models**: Google Gemini 2.0 Flash 
*   **Vector DB**: Pinecone (Managed vector search for RAG)
*   **Search Tools**: Tavily (Optimized for LLM context), Perplexity (Deep research)
*   **Package Manager**: `uv` (Fast Python package installer)

---

## 💡 Design Decisions & Rationale

### 1. **Microservices Architecture (Node.js + Python)**
*   **Decision**: Split the backend into two services.
*   **Why**: 
    *   **Node.js** is excellent for I/O-bound tasks like handling high-concurrency REST APIs, authentication, and CRUD operations. It has a vast ecosystem for web standard libraries.
    *   **Python** is the undisputed king of AI/ML. Libraries like LangChain, LangGraph, and data processing tools are native to Python.
*   **Why not Monolith?**: Trying to force AI logic into Node.js (less mature AI ecosystem) or Auth/CRUD into Python (slower for simple requests) would compromise the strengths of both.

### 2. **LangGraph for Orchestration**
*   **Decision**: Use LangGraph instead of a simple linear chain.
*   **Why**: Research is not linear. It requires loops: *Plan -> Research -> Evaluate -> (Need more info?) -> Research -> Write*. LangGraph allows us to define cyclic graphs with state persistence, enabling "Human-in-the-loop" interactions where the agent can pause and ask the user for clarification.
*   **Why not LangChain Agents?**: Standard ReAct agents can be unpredictable. LangGraph provides more control over the state machine and transitions.

### 3. **WebSockets for AI Communication**
*   **Decision**: Use WebSockets instead of REST for the chat interface.
*   **Why**: AI responses can be slow. Users need immediate feedback. WebSockets allow us to stream "thoughts" (intermediate steps), status updates ("Searching Tavily..."), and partial tokens in real-time, creating a responsive "alive" feeling.
*   **Why not Server-Sent Events (SSE)?**: SSE is one-way. We needed bi-directional communication for features like interrupting the agent or sending real-time edits.

### 4. **Supabase (PostgreSQL + JSONB)**
*   **Decision**: Use Supabase as the primary datastore.
*   **Why**: It provides a production-ready Postgres database with built-in Auth support (though we implemented custom JWT for flexibility).
*   **Schema Design**: We use structured columns for critical data (`id`, `user_id`) but `JSONB` for flexible content like `account_plans` and `research_data`. This allows the AI to evolve its output schema without requiring constant database migrations.

### 5. **Pinecone for RAG**
*   **Decision**: Use Pinecone as an external Vector Database.
*   **Why**: While Postgres has `pgvector`, Pinecone is a specialized managed service that offers low-latency vector search at scale without managing index maintenance or vacuuming. It simplifies the infrastructure.

### 6. **Human-in-the-Loop (HITL)**
*   **Decision**: The AI explicitly pauses to ask for user input if research is ambiguous.
*   **Why**: Hallucination is a major risk in autonomous agents. By detecting ambiguity and asking the user ("Did you mean X or Y?"), we significantly increase the reliability of the final report.

---

## 🚀 Setup

For detailed setup instructions, please refer to **[SETUP.md](./SETUP.md)**.
