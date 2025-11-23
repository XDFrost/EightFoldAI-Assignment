# Veritas - Intelligent Research Agent

Veritas is an advanced AI-powered research assistant designed to autonomously generate, refine, and manage comprehensive account plans and research reports. It leverages a multi-agent architecture to perform deep web research, synthesize information, and interact with users in real-time via text and voice.

## Key Features

*   **Deep Web Research**: Autonomously searches Tavily and Perplexity to gather real-time financial data, news, and market insights.
*   **Intelligent Synthesis**: Transforms raw data into structured, narrative-driven reports (Executive Summary, Key Findings, Detailed Analysis).
*   **Dynamic Account Plans**: Generates strategic account plans based on research, which can be edited section-by-section.
*   **Voice Interaction**: Full duplex voice conversation with interruption (barge-in) support using Deepgram.
*   **Context Awareness**: Remembers previous context (e.g., "Add numbers" refers to the previous company).
*   **Human-in-the-Loop**: Proactively asks for clarification when it detects conflicting or ambiguous information.

---

## System Architecture

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

### AI Orchestration (LangGraph)

The AI Service uses **LangGraph** to manage the research workflow as a state machine:

1.  **Intent Analysis**: Classifies the user's request (Research, Plan, Edit, Chat).
2.  **Query Generation**: Uses LLM to generate optimized search queries based on context.
3.  **Research Node**: Executes searches via Tavily/Perplexity.
4.  **Evaluation Node**: Checks for ambiguity/conflicts. If found, asks the user.
5.  **Synthesis Node**: Generates the final report or plan.

---

## Design Decisions & Rationale

### 1. **Microservices Architecture (Node.js + Python)**
*   **Decision**: Split the backend into two distinct services.
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

### 7. **Voice Interaction (Deepgram)**
*   **Decision**: Use Deepgram for both STT and TTS over WebSockets.
*   **Why**: Latency is critical for voice. Deepgram offers one of the fastest transcription and speech generation APIs. By streaming audio directly over the existing WebSocket connection, we minimize overhead and enable features like "barge-in" (interruption) for a natural conversation flow.

---

## Intents & Capabilities

The agent is designed to handle specific user intents:

| Intent | Description | Triggers |
| :--- | :--- | :--- |
| **`research_company`** | Conducts deep research on a company. | "Research Twitter", "Find info on Tesla", "Add numbers to the report" |
| **`generate_plan`** | Creates a strategic account plan. | "Create an account plan for Apple", "Write a strategy document" |
| **`edit_section`** | Updates a specific section of an *existing* plan. | "Change the executive summary", "Update the financials section" |
| **`chat`** | General conversation and small talk. | "Hello", "How are you?", "What can you do?" |
| **`answer_clarification`** | Handles user responses to AI questions. | "2023", "The first option", "Yes, dig deeper" |

---

## Database Schema (Supabase)

We use **PostgreSQL** via Supabase with a mix of structured columns and `JSONB` for flexibility.

### `users`
*   `id`: UUID (Primary Key)
*   `email`: String
*   `password_hash`: String
*   `created_at`: Timestamp

### `conversations`
*   `id`: UUID (Primary Key)
*   `user_id`: UUID (Foreign Key)
*   `title`: String (Auto-generated)
*   `created_at`: Timestamp

### `messages`
*   `id`: UUID (Primary Key)
*   `conversation_id`: UUID (Foreign Key)
*   `role`: String ("user" or "assistant")
*   `content`: Text
*   `created_at`: Timestamp

### `research_data`
*   `id`: UUID (Primary Key)
*   `user_id`: UUID (Foreign Key)
*   `company`: String
*   `content`: JSONB (Stores the full research report structure)
*   `created_at`: Timestamp

### `account_plans`
*   `id`: UUID (Primary Key)
*   `user_id`: UUID (Foreign Key)
*   `company`: String
*   `content`: JSONB (Stores the plan sections: Executive Summary, Financials, etc.)
*   `version`: Integer

---

## Tech Stack

### **Frontend**
*   **Framework**: React 19 (via Vite)
*   **Styling**: Tailwind CSS
*   **Icons**: Lucide React
*   **Animations**: Framer Motion
*   **Markdown**: `react-markdown` + `remark-gfm`

### **Business Backend**
*   **Runtime**: Node.js
*   **Framework**: Express.js
*   **Database**: PostgreSQL (Supabase)
*   **Auth**: JWT + bcrypt

### **AI Service**
*   **Runtime**: Python 3.11+
*   **Framework**: FastAPI
*   **Orchestration**: **LangGraph**
*   **LLM**: Google Gemini 2.0 Flash
*   **Vector DB**: Pinecone
*   **Search**: Tavily, Perplexity
*   **Voice**: Deepgram

---

## Project Structure

```
EightFoldAI/
├── Ai-Service/             # Python AI Backend
│   ├── app/
│   │   ├── api/            # WebSocket & REST endpoints
│   │   ├── Config/         # Prompts & Data Config
│   │   ├── core/           # Orchestrator & LLM Client
│   │   ├── services/       # Research, Voice, Plan Services
│   │   └── main.py         # Entry point
│   └── requirements.txt
├── backend/                # Node.js Business Backend
│   ├── src/
│   │   ├── controllers/    # Auth & User Logic
│   │   ├── routes/         # API Routes
│   │   └── index.js        # Entry point
│   └── package.json
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/     # ChatInterface, VoiceInterface
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## Setup

For detailed setup instructions, please refer to **[SETUP.md](./SETUP.md)**.
