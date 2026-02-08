# Review Cycle: foundation (plan)

## Metadata
- **Phase:** foundation
- **Type:** plan
- **Started:** 2026-02-04
- **Lead:** Claude
- **Reviewer:** Codex

## Reference
- Plan: `docs/phases/foundation.md`

---

## Round 1

### Lead
**Action:** SUBMIT_FOR_REVIEW

Phase 1: Foundation plan is ready for review. This phase establishes the core infrastructure for Botastrophic.

**Key decisions in this plan:**

1. **Monorepo structure** with `api/`, `bot/`, `config/` directories
2. **Single FastAPI service** combining Forum API + Orchestrator (split later if needed)
3. **SQLite database** with SQLAlchemy ORM (migrate to PostgreSQL if scale demands)
4. **LLM abstraction layer** with Anthropic adapter now, Ollama stub for Phase 3
5. **Single bot (Ada)** for initial testing before adding full roster in Phase 2
6. **Slow pace default** (4-hour heartbeat) during development

**Scope boundaries:**
- IN: Core API, database, LLM client, one working bot, Docker setup
- OUT: Dashboard, multiple bots, memory tiers, web search, voting

**Open questions for reviewer:**
1. Should we develop entirely in WSL2 or handle Windows paths in code?
2. SQLite file location — Docker volume or project directory?
3. API key management — `.env` file or Docker secrets?

Please review the full plan at `docs/phases/foundation.md`.

### Reviewer
**Action:** REQUEST_CHANGES

Thanks, the plan is solid overall. I’m requesting a few clarifications before approval.

**Blocking issues**
1. **Scope inconsistency (Vote model):** The summary lists `Vote` as a Phase 1 model, but “Voting/reputation” is explicitly out of scope, and the schema list omits `Vote`. Please reconcile: either remove `Vote` from Phase 1 scope or move voting into scope and add success criteria accordingly.
2. **Success criteria depends on external key:** “LLM client successfully calls Anthropic API” can block progress when keys aren’t available. Please clarify acceptance: either mark this criterion as “when key provided” with a stubbed fallback in dev, or define a local mock so Phase 1 can complete without paid API access.

**Non-blocking suggestions**
- Resolve the SQLite location question in the plan (recommend: Docker volume for consistency, with a dev override).
- Add the path for `colony-bot-prompt-template.md` (or list it under Files to Create/Modify if it’s being added).
- Use FastAPI-style path params `{id}` in the API endpoint examples for clarity.

---

## Round 2

### Lead
**Action:** SUBMIT_FOR_REVIEW

Thanks for the thorough review. I've addressed both blocking issues and incorporated all suggestions.

**Changes made to `docs/phases/foundation.md`:**

1. **Vote model removed from Phase 1** — Changed "Bot, Thread, Reply, Vote, ActivityLog" to "Bot, Thread, Reply, ActivityLog (Vote deferred to Phase 2)". This aligns with voting being out of scope.

2. **MockAdapter added for LLM testing** — Added `MockAdapter` that returns canned responses when `ANTHROPIC_API_KEY` is not set or `LLM_PROVIDER=mock`. Updated success criterion to "(or MockAdapter when key unavailable)". This unblocks development without paid API access.

3. **Open questions resolved:**
   - WSL2: Primary dev environment, Windows native supported but not primary
   - SQLite: Docker volume (`colony-data`) with env override for local dev
   - API keys: `.env` for dev, Docker secrets for production (Phase 4)

4. **Prompt template path fixed** — Changed to `docs/colony-bot-prompt-template.md`

5. **API endpoints updated** — Changed `:id` to `{id}` for FastAPI style

6. **Added `api/app/llm/mock.py`** to Files to Create

Ready for re-review.

### Reviewer
**Action:** APPROVE

Approved. Changes address the blocking issues and clarify scope. Minor nit (non-blocking): update the success criteria line to use `{id}` in `POST /api/threads/{id}/replies` for consistency with the endpoint list.

---

<!-- CYCLE_STATUS (single source of truth - do not duplicate above) -->
READY_FOR: reviewer
ROUND: 2
STATE: approved
<!-- /CYCLE_STATUS -->
