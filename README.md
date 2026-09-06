# Local LLM

A personal, self-hosted AI platform built around local and open-source LLMs.

## Goals

- Run LLMs locally
- Chat with local models
- Analyze documents and source code
- Build RAG-based knowledge retrieval
- Integrate MCP tools
- Integrate GitLab and TMS
- Keep private data local
- Provide an extensible API and web interface

## Architecture

See `architecture.png` for the current high-level architecture.

## Project Structure

app/              Application code
config/           Configuration
documents/        Local documents
models/            Model configuration
rag/              Retrieval-Augmented Generation
mcp/              MCP servers and integrations
scripts/          Utility scripts
tests/            Automated tests
data/              Runtime data
docker/            Container configuration
logs/              Application logs


## Commands
activate environment    python -m venv .venv

.venv\Scripts\Activate.ps1