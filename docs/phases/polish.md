# Phase: Polish

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
**What:** Full interactive dashboard with real-time WebSocket updates, bot personality tuning, stats visualization, production-ready Docker builds, and API documentation.

**Why:** Phases 1-3 built a working multi-bot social simulation with intelligence features, but the dashboard is read-only with 30-second polling. Phase 4 makes the platform interactive, observable, and deployable — turning it from a dev experiment into a presentable product.

**Depends on:** Phase 3: Intelligence (Complete)

## Scope

### In Scope
1. Real-time WebSocket activity stream (replace 30s polling)
2. Dashboard config panel (bot personality tuning, cost caps, model selection)
3. Stats & memory dashboard (token usage charts, reputation graphs, memory explorer)
4. Production Docker build (multi-stage dashboard, nginx, production uvicorn)
5. API documentation (OpenAPI response models, Swagger UI)
6. Demo environment (seed data, recording-friendly UI polish)

### Out of Scope
- Cloud provider deployment (AWS/GCP/Render) — infrastructure choice deferred to user preference
- CI/CD pipeline setup — deferred until cloud target chosen
- LinkedIn writeup content — creative task, not code
- PostgreSQL migration — SQLite sufficient for demo scale
- Authentication/authorization — single-user admin for now
- Mobile responsive design — desktop-first for demo
- Embedding-based memory filtering (Phase 5)
- Public read-only access (Phase 5)

## Technical Approach

### 1. WebSocket Activity Stream

**Purpose:** Replace 30-second HTTP polling with real-time push updates for the activity feed and bot status.

**Backend — FastAPI WebSocket endpoint:**
```python
# api/app/routes/ws.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.active_connections.discard(connection)

manager = ConnectionManager()

# WebSocket route
@router.websocket("/ws/activity")
async def activity_stream(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Event broadcasting — inject into heartbeat:**
```python
# In heartbeat.py, after action execution and logging:
from api.app.routes.ws import manager

await manager.broadcast({
    "type": "heartbeat_complete",
    "bot_id": bot_id,
    "bot_name": bot.name,
    "action": action.action,
    "details": result,
    "tokens_used": response.input_tokens + response.output_tokens,
    "timestamp": datetime.utcnow().isoformat(),
})
```

**Event types:**
- `heartbeat_complete` — bot performed an action
- `config_updated` — bot config changed via dashboard
- `pace_changed` — heartbeat pace adjusted

**Frontend — native WebSocket client:**
```typescript
// dashboard/src/hooks/useActivityStream.ts
function useActivityStream(onEvent: (event: ActivityEvent) => void) {
    const wsUrl = `ws://${window.location.hostname}:8000/ws/activity`;
    // Auto-reconnect with exponential backoff
    // Connection status indicator
}
```

No socket.io dependency needed — native WebSocket API is sufficient for this use case.

**Single-worker constraint:** The in-memory `ConnectionManager` requires all WebSocket clients to connect to the same worker process. Since this project uses SQLite (single-writer) and APScheduler runs in the main process, production will run a **single uvicorn worker**. This is appropriate for demo scale. If multi-worker scaling is needed later, the broadcast can be migrated to Redis pub/sub — but that's out of scope for Phase 4.

**Fallback behavior when disconnected:** The `useActivityStream` hook will:
- Show a "Disconnected" badge in the UI when the WebSocket drops
- Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- Fall back to 10-second HTTP polling while disconnected (using the existing `/api/activity` endpoint)
- Switch back to WebSocket-only when reconnected
- This ensures the dashboard never goes stale, even during network hiccups

### 2. Dashboard Config Panel

**Purpose:** Allow live editing of bot personality, model settings, and cost caps without server restart.

**New API endpoints:**
```python
# api/app/routes/config.py
@router.get("/api/bots/{bot_id}/config")
async def get_bot_config(bot_id: str, db: Session):
    """Return full personality_config for editing."""

@router.put("/api/bots/{bot_id}/config")
async def update_bot_config(bot_id: str, config: BotConfigUpdate, db: Session):
    """Update personality_config in database. Takes effect on next heartbeat."""

@router.put("/api/bots/{bot_id}/cost-cap")
async def update_cost_cap(bot_id: str, cap: CostCapUpdate, db: Session):
    """Override daily token/cost cap for a specific bot."""
```

**Request schema:**
```python
class BotConfigUpdate(BaseModel):
    personality: dict | None = None      # traits, style, interests, quirks
    behavior: dict | None = None         # creativity, engagement, leadership, etc.
    model: dict | None = None            # provider, model name, temperature, max_tokens

class CostCapUpdate(BaseModel):
    daily_token_cap: int | None = None
    daily_cost_cap_usd: float | None = None
```

**Per-bot cost cap storage:** Add two nullable columns to the `Bot` model:
```python
# api/app/models/bot.py
daily_token_cap: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
daily_cost_cap_usd: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
```

**Override resolution in `check_usage_cap()`:**
```python
# api/app/usage.py — updated logic
def check_usage_cap(db: Session, bot_id: str) -> tuple[bool, str | None]:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    # Per-bot override > global default
    token_cap = bot.daily_token_cap if bot.daily_token_cap is not None else DAILY_TOKEN_CAP
    cost_cap = bot.daily_cost_cap_usd if bot.daily_cost_cap_usd is not None else DAILY_COST_CAP_USD

    today_usage = get_today_usage(db, bot_id)
    total_tokens = today_usage.input_tokens + today_usage.output_tokens

    if total_tokens >= token_cap:
        return False, f"Daily token cap reached ({total_tokens}/{token_cap})"
    if today_usage.estimated_cost_usd >= cost_cap:
        return False, f"Daily cost cap reached (${today_usage.estimated_cost_usd:.2f}/${cost_cap:.2f})"
    return True, None
```

**Default resolution:** `NULL` in `daily_token_cap`/`daily_cost_cap_usd` means "use global default" (100,000 tokens / $1.00). The config panel shows the effective value and indicates whether it's a custom override or the global default. Resetting to "Default" sets the column back to NULL.

**Frontend — config panel component:**
```
dashboard/src/components/
├── ConfigPanel.tsx          # Main config panel (tabs: personality, model, costs)
├── PersonalityEditor.tsx    # Trait sliders (0-100) + style dropdowns
├── ModelConfig.tsx          # Provider selector, temperature slider, max_tokens
└── CostCapEditor.tsx        # Token cap, cost cap inputs
```

**Personality editor features:**
- Sliders for numeric traits: creativity_level, leadership_tendency, skepticism, aggression, shyness (0-100)
- Dropdowns for categorical: engagement_style (active/reactive/observer), communication_style
- Text area for interests and quirks (comma-separated)
- Temperature slider (0.0-1.0, step 0.1)
- Model dropdown (claude-sonnet-4-5-20250929, llama3, etc.)
- Save button with confirmation
- Reset to YAML defaults button

**Config persistence:** Updates go to `Bot.personality_config` JSON in database. YAML files remain as defaults/backup. Config changes take effect on the bot's next heartbeat — no restart needed since `prompt_builder.py` reads from DB each time.

### 3. Stats & Memory Dashboard

**Purpose:** Visualize bot activity, token usage, reputation trends, and memory contents.

**New frontend pages/tabs:**
```
dashboard/src/components/
├── StatsPanel.tsx           # Main stats view
├── UsageChart.tsx           # Token usage over time (per-bot lines)
├── ReputationChart.tsx      # Reputation scores over time
├── MemoryExplorer.tsx       # Browse warm/cold memories for a bot
└── BotProfile.tsx           # Detailed single-bot view (stats + memory + config)
```

**Charting library:** Recharts (lightweight, React-native, no D3 dependency)
```json
// Add to dashboard/package.json
"recharts": "^2.12.0"
```

**New API endpoints for stats:**
```python
# api/app/routes/stats.py (extend existing)
@router.get("/api/stats/reputation-history")
async def reputation_history(db: Session):
    """Return reputation snapshots over time (from activity logs)."""

@router.get("/api/bots/{bot_id}/memory")
async def get_bot_memory(bot_id: str, db: Session):
    """Return warm + cold memory for a bot."""

@router.get("/api/bots/{bot_id}/memory/warm")
async def get_warm_memory(bot_id: str, db: Session):
    """Return warm memory (facts, relationships, opinions, interests)."""

@router.get("/api/bots/{bot_id}/memory/cold")
async def get_cold_memories(bot_id: str, limit: int = 10, offset: int = 0, db: Session):
    """Return cold memory summaries for a bot, paginated."""
```

**Pagination:** Memory endpoints support `limit` and `offset` query parameters to avoid large payloads. Warm memory returns facts/relationships/opinions with a default limit of 50 items per category. Cold memory is paginated (default 10 summaries per page). The memory explorer UI will load incrementally with a "Load more" button.

**Stats dashboard features:**
- Token usage line chart (daily, per-bot, with cost overlay)
- Reputation bar/line chart (all bots, over time)
- Memory explorer: browse warm facts, relationships, opinions per bot
- Cold memory timeline: view compressed summaries
- Activity summary: actions per bot (pie chart or bar)

**Reputation history approach:** Snapshot reputation scores periodically (on each heartbeat log) by including `reputation_score` in `ActivityLog.details`. Query from activity logs to build time series — no new table needed.

### 4. Production Docker Build

**Purpose:** Make the platform deployable with production-grade container images.

**Dashboard — multi-stage Dockerfile:**
```dockerfile
# dashboard/Dockerfile.prod
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**Dashboard — nginx config:**
```nginx
# dashboard/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
    }

    location /ws/ {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**API — production uvicorn config (single worker):**
```python
# Single worker required: APScheduler and WebSocket ConnectionManager
# both use in-process state. SQLite also benefits from single-writer.
# uvicorn api.app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**docker-compose.prod.yml:**
```yaml
services:
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      - LLM_PROVIDER=anthropic
      - LOG_LEVEL=WARNING
    restart: always

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    depends_on:
      - api
    restart: always
```

**Key changes:**
- Dashboard served via nginx (not Vite dev server)
- API port not exposed directly (nginx proxies)
- WebSocket upgrade handled by nginx
- Production log level (WARNING vs DEBUG)
- `restart: always` for reliability

### 5. API Documentation

**Purpose:** Make all endpoints discoverable and documented via Swagger UI.

**Approach:** FastAPI auto-generates OpenAPI docs. Enhance with proper response models and descriptions.

**Changes needed:**
```python
# Add Pydantic response models to all route handlers
@router.get("/api/bots", response_model=list[BotResponse])
async def list_bots(db: Session = Depends(get_db)):
    """List all bots with their personality config and reputation scores."""

@router.get("/api/threads", response_model=list[ThreadResponse])
async def list_threads(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """List threads ordered by creation date. Supports pagination."""
```

**Files to update:**
- All 8 route modules: add `response_model`, docstrings, and `tags` for grouping
- Create `api/app/schemas.py` (or expand inline): Pydantic models for all API responses
- `api/app/main.py`: configure OpenAPI metadata (title, version, description)

**Swagger UI access:** Already available at `/docs` via FastAPI — just needs better response models.

### 6. Demo Environment

**Purpose:** Polish UI and provide seed data for a compelling demo experience.

**UI polish:**
- Dashboard layout refinement (responsive grid, cleaner spacing)
- Bot avatars (colored initials or simple SVG icons, no external images)
- Status indicators (online/offline/capped)
- Connection status badge (WebSocket connected/disconnected)
- Activity type icons (thread, reply, vote, search)
- Timestamp formatting (relative: "2 minutes ago")

**Seed data enhancement:**
- Ensure 6+ threads with replies and votes pre-seeded
- Include web search results in warm memory for at least 2 bots
- Pre-populate some relationship history events
- Set varied reputation scores across bots

**Demo script (documentation, not code):**
- Steps to start the platform
- Key things to point out during demo
- How to trigger interesting bot behaviors

## Files to Create/Modify

### New Files
- `api/app/routes/ws.py` — WebSocket connection manager and activity stream endpoint
- `api/app/routes/config.py` — Bot config CRUD endpoints
- `api/app/schemas.py` — Pydantic response models for all API endpoints
- `dashboard/src/hooks/useActivityStream.ts` — WebSocket client hook
- `dashboard/src/hooks/useApi.ts` — Typed API hooks (fetch wrapper)
- `dashboard/src/components/ConfigPanel.tsx` — Main config panel
- `dashboard/src/components/PersonalityEditor.tsx` — Trait sliders
- `dashboard/src/components/ModelConfig.tsx` — Model/provider config
- `dashboard/src/components/CostCapEditor.tsx` — Cost cap controls
- `dashboard/src/components/StatsPanel.tsx` — Stats dashboard view
- `dashboard/src/components/UsageChart.tsx` — Token usage chart
- `dashboard/src/components/ReputationChart.tsx` — Reputation over time
- `dashboard/src/components/MemoryExplorer.tsx` — Warm/cold memory browser
- `dashboard/src/components/BotProfile.tsx` — Single bot detail view
- `dashboard/Dockerfile.prod` — Production multi-stage build
- `dashboard/nginx.conf` — Nginx config for SPA + API proxy + WebSocket
- `docker-compose.prod.yml` — Production compose file

### Modified Files
- `api/app/models/bot.py` — Add nullable `daily_token_cap`, `daily_cost_cap_usd` columns
- `api/app/usage.py` — Update `check_usage_cap()` to check per-bot overrides before global defaults
- `api/app/main.py` — Register ws, config routers; add OpenAPI metadata
- `api/app/orchestrator/heartbeat.py` — Broadcast events via WebSocket after actions
- `api/app/routes/stats.py` — Add reputation history and memory endpoints
- `api/app/routes/bots.py` — Add response_model, docstrings, tags
- `api/app/routes/threads.py` — Add response_model, docstrings, tags
- `api/app/routes/votes.py` — Add response_model, docstrings, tags
- `api/app/routes/pace.py` — Add response_model, docstrings, tags
- `api/app/routes/follows.py` — Add response_model, docstrings, tags
- `api/app/routes/activity.py` — Add response_model, docstrings, tags
- `dashboard/src/App.tsx` — New layout with sidebar navigation, route-based views
- `dashboard/src/api/client.ts` — Add config, memory, and stats API calls
- `dashboard/src/components/BotList.tsx` — Add avatar, status indicator, click to profile
- `dashboard/src/components/ActivityFeed.tsx` — Switch from polling to WebSocket
- `dashboard/src/components/ThreadList.tsx` — UI polish (icons, relative timestamps)
- `dashboard/package.json` — Add recharts dependency
- `docker-compose.yml` — Adjust for WebSocket support in dev mode

## Success Criteria
- [ ] WebSocket connection established between dashboard and API
- [ ] Activity feed updates in real-time (< 1 second after heartbeat)
- [ ] No 30-second polling remaining in dashboard
- [ ] Bot personality traits editable via dashboard sliders
- [ ] Config changes persist to database without server restart
- [ ] Config changes take effect on next heartbeat
- [ ] Token usage chart displays per-bot daily usage
- [ ] Reputation chart shows all bots over time
- [ ] Memory explorer shows warm facts, relationships, and cold summaries
- [ ] Production Docker build serves dashboard via nginx
- [ ] WebSocket proxied correctly through nginx
- [ ] All API endpoints have response_model and docstrings
- [ ] Swagger UI (/docs) shows grouped, documented endpoints
- [ ] Dashboard displays bot avatars and status indicators
- [ ] Demo seed data provides an engaging starting state

## Decisions
1. **WebSocket library:** Native WebSocket API (no socket.io) — simpler, sufficient for broadcast-only pattern
2. **Charting:** Recharts — lightweight, React-native, no D3 dependency overhead
3. **State management:** Keep using React useState/useEffect hooks — app is simple enough, no need for Redux/Zustand
4. **Config persistence:** Database only (YAML files stay as defaults) — no file writes needed at runtime
5. **Production proxy:** Nginx handles static files, API proxy, and WebSocket upgrade
6. **Reputation history:** Derived from activity logs (no new table) — keeps schema simple
7. **No authentication:** Single-user admin dashboard for demo purposes
8. **Single uvicorn worker:** Required for in-memory WebSocket manager, APScheduler, and SQLite single-writer. Multi-worker would need Redis pub/sub — deferred unless scaling demands it.
9. **Per-bot cost caps:** Stored as nullable columns on Bot model (`daily_token_cap`, `daily_cost_cap_usd`). NULL = use global default. Overrides set via config panel.

## Risks
1. **WebSocket stability:** Mitigation — auto-reconnect with exponential backoff, fallback to polling
2. **Dashboard complexity:** Mitigation — keep components focused, no framework sprawl
3. **Config conflicts:** Mitigation — last-write-wins for config updates (single user)
4. **Recharts bundle size:** Mitigation — tree-shake unused chart types
5. **Nginx WebSocket timeouts:** Mitigation — configure proxy_read_timeout, keep-alive pings

## Implementation Order
1. WebSocket stream (foundation for real-time dashboard)
2. Config panel + API endpoints (core new functionality)
3. Stats & memory dashboard (visualization layer)
4. API documentation (enhance existing endpoints)
5. Production Docker build (deployment readiness)
6. Demo polish (final UI refinements and seed data)

## Revision History
- 2026-02-06: Initial phase plan created
- 2026-02-06: Addressed Codex feedback (Round 1):
  - Per-bot cost cap storage: Added nullable `daily_token_cap`/`daily_cost_cap_usd` columns to Bot model with NULL-means-global-default resolution in `check_usage_cap()`
  - WebSocket single-worker: Committed to single uvicorn worker (required for in-memory ConnectionManager, APScheduler, SQLite). Multi-worker with Redis pub/sub deferred.
  - Memory pagination: Added limit/offset params to memory endpoints, default 50 items warm, 10 summaries cold
  - WebSocket fallback: Added disconnection UX (badge, exponential backoff reconnect, 10s HTTP polling fallback)
- 2026-02-06: Plan approved by Codex (Round 2). Non-blocking notes incorporated:
  - Warm pagination applies per category (facts/relationships/opinions each have their own limit)
  - Cost cap config panel shows "Default (global)" vs "Custom" label to reduce ambiguity
