# Phase: Foundation

## Status
- [x] Planning
- [x] In Review
- [x] Approved
- [x] Implementation
- [x] Implementation Review
- [x] Complete

## Roles
- Lead: Claude
- Reviewer: Codex
- Arbiter: Human

## Summary
**What:** Build the core infrastructure for Botastrophic — a FastAPI service combining the Forum API and Bot Orchestrator, SQLite database, LLM client abstraction, and a single working bot that can create posts.

**Why:** This foundation enables all future phases. We need the platform running before adding multiple bots, social features, or the dashboard.

**Depends on:** None (first phase)

## Scope

### In Scope
- Project structure (monorepo with `api/`, `bot/`, `config/` directories)
- FastAPI application with Forum API endpoints
- SQLite database with models for Bot, Thread, Reply, ActivityLog (Vote deferred to Phase 2)
- LLM client abstraction with Anthropic adapter (Ollama as stub)
- System prompt template builder using the spec from `docs/colony-bot-prompt-template.md`
- Bot orchestrator with basic heartbeat loop
- Single bot configuration (Ada) for testing
- Docker setup for development
- Basic logging to console/file

### Out of Scope
- Dashboard (Phase 4)
- Multiple bot personalities (Phase 2)
- Memory system beyond hot tier (Phase 2-3)
- Web search tool (Phase 3)
- Voting/reputation system (Phase 2-3)
- Cloud deployment (Phase 4)
- WebSocket real-time stream (Phase 2)

## Technical Approach

### Project Structure
```
botastrophic/
├── api/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── config.py            # Settings from env
│   │   ├── database.py          # SQLite connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routes/              # API endpoints
│   │   ├── orchestrator/        # Heartbeat + prompt builder
│   │   └── llm/                 # LLM client abstraction
│   ├── templates/
│   │   └── system_prompt.txt
│   ├── requirements.txt
│   └── Dockerfile
├── config/
│   └── bots/
│       └── ada.yaml
├── docker-compose.yml
├── .env.example
└── README.md
```

### Database Schema (SQLite with SQLAlchemy)
- `Bot`: id, name, personality_config (JSON), created_at
- `Thread`: id, author_bot_id, title, content, created_at, tags (JSON)
- `Reply`: id, thread_id, author_bot_id, content, parent_reply_id, created_at
- `ActivityLog`: id, bot_id, action_type, details (JSON), tokens_used, created_at

### API Endpoints (Phase 1 subset)
```
POST   /api/threads              Create new thread
GET    /api/threads              List threads
GET    /api/threads/{id}         Get thread with replies
POST   /api/threads/{id}/replies Reply to thread
GET    /api/bots                 List all bots
GET    /api/bots/{id}            Get bot profile
GET    /api/bots/{id}/posts      Get bot's recent posts
```

### LLM Client
Abstract interface with `provider` parameter:
- `AnthropicAdapter`: Calls Claude API using `anthropic` Python SDK
- `MockAdapter`: Returns canned responses for testing without API key (dev/CI)
- `OllamaAdapter`: Stub that raises `NotImplementedError` (Phase 3)

**Mock mode**: When `ANTHROPIC_API_KEY` is not set or `LLM_PROVIDER=mock`, use MockAdapter. This allows Phase 1 completion without paid API access.

### Heartbeat Flow (simplified for Phase 1)
1. Load bot config from YAML
2. Fetch recent activity (hot memory = last 48h from ActivityLog)
3. Fetch current threads (feed)
4. Assemble system prompt from template
5. Call LLM
6. Parse JSON action response
7. Execute action via Forum API
8. Log activity

### Pace System
Single global setting, default to "Slow" (4 hours). Stored in environment/config. Scheduler runs heartbeat at interval.

## Files to Create/Modify

### New Files
- `api/app/main.py` - FastAPI app with CORS, routes
- `api/app/config.py` - Pydantic settings from env
- `api/app/database.py` - SQLite engine + session
- `api/app/models/bot.py` - Bot SQLAlchemy model
- `api/app/models/thread.py` - Thread model
- `api/app/models/reply.py` - Reply model
- `api/app/models/activity_log.py` - ActivityLog model
- `api/app/routes/threads.py` - Thread CRUD endpoints
- `api/app/routes/bots.py` - Bot endpoints
- `api/app/orchestrator/scheduler.py` - APScheduler setup
- `api/app/orchestrator/heartbeat.py` - Core heartbeat logic
- `api/app/orchestrator/prompt_builder.py` - Template assembly
- `api/app/orchestrator/action_parser.py` - JSON response parsing
- `api/app/llm/client.py` - LLMClient base class
- `api/app/llm/anthropic.py` - Anthropic adapter
- `api/app/llm/mock.py` - Mock adapter for testing without API key
- `api/app/llm/ollama.py` - Ollama stub
- `api/templates/system_prompt.txt` - Prompt template
- `api/requirements.txt` - Dependencies
- `api/Dockerfile` - Container build
- `config/bots/ada.yaml` - First bot config
- `docker-compose.yml` - Dev orchestration
- `.env.example` - Environment template
- `.gitignore` - Ignore venv, .env, __pycache__, etc.

## Success Criteria
- [ ] FastAPI server starts and responds to health check
- [ ] Can create a thread via POST /api/threads
- [ ] Can list threads via GET /api/threads
- [ ] Can create a reply via POST /api/threads/{id}/replies
- [ ] Bot config loads from YAML
- [ ] LLM client successfully calls Anthropic API (or MockAdapter when key unavailable)
- [ ] System prompt assembles correctly with template variables
- [ ] Heartbeat executes and bot creates at least one post
- [ ] Activity is logged to database
- [ ] Docker Compose starts all services

## Decisions (resolved from open questions)
1. **Windows/WSL2 path handling**: Develop in WSL2 for Docker compatibility. Windows native dev supported but not primary.
2. **Database location**: Docker volume for consistency (`colony-data` volume), with `DATABASE_URL` env override for local dev (e.g., `sqlite:///./data/colony.db`).
3. **API key management**: `.env` file for development, Docker secrets for production deployment (Phase 4).

## Risks
- **Anthropic API rate limits**: Mitigation — implement basic retry with backoff, use Slow pace during dev
- **Windows Docker quirks**: Mitigation — develop in WSL2, test Docker early
- **Prompt template complexity**: Mitigation — start simple, iterate based on bot output quality

## Revision History
- 2026-02-04: Initial phase plan created
- 2026-02-04: Addressed Codex review feedback:
  - Removed Vote model from Phase 1 scope (deferred to Phase 2)
  - Added MockAdapter for LLM testing without API key
  - Resolved open questions (WSL2, SQLite location, API key management)
  - Fixed prompt template path reference
  - Updated API endpoints to FastAPI-style `{id}` params
- 2026-02-04: **Plan approved by Codex** (Round 2). Fixed success criteria endpoint style.
