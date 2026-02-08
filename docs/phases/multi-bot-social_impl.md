# Implementation Log: Multi-Bot Social

**Started:** 2026-02-04
**Completed:** 2026-02-04
**Lead:** Claude
**Plan:** docs/phases/multi-bot-social.md

## Progress

### Session 1 - 2026-02-04

#### Bot Configurations
- [x] `config/bots/marcus.yaml`
- [x] `config/bots/luna.yaml`
- [x] `config/bots/rex.yaml`
- [x] `config/bots/echo.yaml`
- [x] `config/bots/sage.yaml`

#### New Models
- [x] `api/app/models/vote.py` - Vote model with unique constraint
- [x] `api/app/models/follow.py` - Follow model with unique constraint
- [x] `api/app/models/warm_memory.py` - WarmMemory model (bot_id PK)
- [x] Update `api/app/models/__init__.py`

#### New Routes
- [x] `api/app/routes/votes.py` - Vote endpoints
- [x] `api/app/routes/pace.py` - Pace control endpoints
- [x] `api/app/routes/follows.py` - Follow endpoints

#### Route Updates
- [x] `api/app/routes/threads.py` - Add vote counts
- [x] `api/app/routes/bots.py` - Add follower counts

#### Memory System
- [x] `api/app/memory/__init__.py`
- [x] `api/app/memory/warm.py` - Warm memory CRUD
- [x] `api/app/memory/extractor.py` - Post-heartbeat extraction
- [x] `api/app/memory/filter.py` - Keyword-based filtering

#### Orchestrator Updates
- [x] `api/app/orchestrator/heartbeat.py` - Add memory extraction, voting
- [x] `api/app/orchestrator/prompt_builder.py` - Inject warm memory
- [x] `api/app/orchestrator/action_parser.py` - Add vote action

#### Seeds
- [x] `seeds/initial_threads.json`
- [x] `api/app/seed_loader.py`

#### Dashboard
- [x] `dashboard/package.json`
- [x] `dashboard/vite.config.ts`
- [x] `dashboard/tailwind.config.js`
- [x] `dashboard/src/App.tsx`
- [x] `dashboard/src/components/BotList.tsx`
- [x] `dashboard/src/components/ThreadList.tsx`
- [x] `dashboard/src/components/ThreadDetail.tsx`
- [x] `dashboard/src/components/PaceControl.tsx`
- [x] `dashboard/Dockerfile`

#### Docker
- [x] Update `docker-compose.yml` - Add dashboard service

## Files Created
- `config/bots/marcus.yaml`
- `config/bots/luna.yaml`
- `config/bots/rex.yaml`
- `config/bots/echo.yaml`
- `config/bots/sage.yaml`
- `api/app/models/vote.py`
- `api/app/models/follow.py`
- `api/app/models/warm_memory.py`
- `api/app/routes/votes.py`
- `api/app/routes/pace.py`
- `api/app/routes/follows.py`
- `api/app/memory/__init__.py`
- `api/app/memory/warm.py`
- `api/app/memory/extractor.py`
- `api/app/memory/filter.py`
- `seeds/initial_threads.json`
- `api/app/seed_loader.py`
- `dashboard/` (full React app)

## Files Modified
- `api/app/models/__init__.py` - Added new model exports
- `api/app/routes/threads.py` - Added vote_score to responses
- `api/app/routes/bots.py` - Added follower/following counts
- `api/app/orchestrator/heartbeat.py` - Added vote action and memory extraction
- `api/app/orchestrator/prompt_builder.py` - Added warm memory injection
- `api/app/orchestrator/action_parser.py` - Added vote action type
- `api/app/main.py` - Added new routers and seed loading
- `api/templates/system_prompt.txt` - Added vote action option
- `docker-compose.yml` - Added dashboard service

## Decisions Made
- Dashboard component naming: Used `BotList`, `ThreadList`, `ThreadDetail`, `PaceControl` instead of spec names for clarity
- Memory extraction: Uses fallback extraction when LLM fails
- Vote scores: Calculated on-demand via SQL sum, not stored denormalized
- Follow model: Uses `follower_id`/`following_id` column names

## Issues Encountered
- Follow model column name mismatch: Initially used `follower_bot_id`/`followed_bot_id` in routes but model had `follower_id`/`following_id`. Fixed by updating routes to match model.
- Dashboard pace control API mismatch: Client used POST/`pace` but server used PUT/`preset`. Fixed by aligning client to server contract.
- Mock adapter didn't support replies/votes or memory extraction. Fixed by adding weighted responses and extraction detection.
- Activity feed was missing. Added `api/app/routes/activity.py` and `ActivityFeed.tsx` component.

## Verification

All endpoints tested and working:
- `GET /api/bots` - Returns 6 bots with follower/following counts
- `GET /api/threads` - Returns threads with vote_score
- `GET /api/threads/{id}` - Returns thread with replies and vote scores
- `POST /api/threads/{id}/vote` - Creates/updates votes
- `GET /api/pace` - Returns current pace setting
- `PUT /api/pace` - Updates pace (fixed from POST)
- `GET /api/activity` - Returns activity log (new)
- `POST /api/heartbeat/{bot_id}` - Triggers heartbeat with memory extraction

### Cross-Bot Engagement Verified
- Thread #1 authored by `ada_001`
- Reply #1 authored by `marcus_001` on Thread #1
- This satisfies the success criterion: `author_bot_id != thread.author_bot_id`
