# Local LLM

A personal, self-hosted AI platform built around local and open-source LLMs.

The goal is to build a ChatGPT-style application that can run locally, support multiple LLM providers, maintain conversation history, process documents, use RAG, and integrate with MCP tools.

---

## Project Status

### Phase 1 — Chat Foundation

- [x] FastAPI backend
- [x] LLM provider configuration
- [x] Basic chat API
- [ ] Store conversations in database
- [ ] Load previous chats after page refresh
- [ ] Create conversations
- [ ] Delete conversations

### Phase 2 — File Upload

- [ ] Add `/files/upload` API
- [ ] Support PDF, TXT, DOCX, etc.
- [ ] Save uploaded files locally
- [ ] Track files against conversations
- [ ] File list
- [ ] File delete

### Phase 3 — RAG

- [ ] Extract text from documents
- [ ] Split documents into chunks
- [ ] Generate embeddings
- [ ] Store embeddings in ChromaDB
- [ ] Retrieve relevant chunks
- [ ] Send retrieved context to LLM
- [ ] Return document/source references

### Phase 4 — Frontend

- [x] Basic chat UI
- [ ] Conversation sidebar
- [ ] Create conversation
- [ ] Delete conversation
- [ ] Load conversation history
- [ ] File upload UI
- [ ] Streaming responses
- [ ] Source/document references

---

## Architecture

```text
                         ┌──────────────────┐
                         │    Frontend      │
                         │  React + Vite    │
                         └────────┬─────────┘
                                  │
                                  │ REST API
                                  ▼
                         ┌──────────────────┐
                         │     FastAPI      │
                         │     Backend      │
                         └────────┬─────────┘
                                  │
                   ┌──────────────┼──────────────┐
                   │              │              │
                   ▼              ▼              ▼
             Conversation      LLM Service       RAG
                Service            │          (Phase 3)
                   │               │
                   ▼         Provider Factory
              SQLite DB             │
                              ┌─────┼─────┐
                              ▼     ▼     ▼
                           OpenAI Gemini Groq