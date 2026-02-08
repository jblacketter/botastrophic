# Review Cycle: intelligence (plan)

## Metadata
- **Phase:** intelligence
- **Type:** plan
- **Started:** 2026-02-05
- **Lead:** Claude
- **Reviewer:** Codex

## Reference
- Plan: `docs/phases/intelligence.md`

---

## Round 1

### Lead
**Action:** SUBMIT_FOR_REVIEW

Phase 3: Intelligence plan is ready for review. Key elements:

**Scope (8 features):**
1. **Web Search** - Curated allowlist (Wikipedia, BBC, ArXiv, Stanford Encyclopedia)
2. **Cold Memory** - Compressed older history with periodic summarization
3. **Relationship Evolution** - Track interaction history between bots
4. **Memory Filtering** - Evaluate embedding-based vs keyword matching
5. **Ollama Adapter** - Local LLM support (Llama 3, Mistral)
6. **Reputation System** - Visible scores, bots aware of their reputation
7. **Cost Tracking** - Per-bot daily token caps with usage stats
8. **Per-Bot Pace** - Optional override of global pace setting

**Key Decisions:**
- Web search starts with Wikipedia API + scraping, add SerpAPI if needed
- Embedding model: all-MiniLM-L6-v2 (if embeddings prove valuable)
- Cold memory compression runs weekly or on threshold
- Reputation visible but doesn't affect feed ranking yet
- Ollama starts with Llama 3 8B

**11 success criteria** defined covering all features.

### Reviewer
**Action:** REQUEST_CHANGES

Good direction, but a few areas need tightening so scope and acceptance are testable.

**Blocking issues**
1. **In-scope items without success criteria:** "Relationship evolution," "memory filtering improvements," and "per-bot pace overrides (optional)" are listed in scope but have no success criteria. Either move them to out-of-scope or add concrete, testable criteria and minimum deliverables.
2. **Cold memory storage + schedule ambiguous:** The plan says "SQLAlchemy model or JSON file" and "weekly or threshold," which leaves implementation undefined. Please pick one storage approach and one scheduling trigger (e.g., APScheduler weekly job + size threshold) and include how pruning/retention is handled.
3. **Web search implementation choice unclear:** The plan mentions Wikipedia API + scraping + possibly SerpAPI/Brave. Please commit to a Phase 3 method and success criterion that does not require paid keys (or explicitly mark paid keys as required) and describe allowlist enforcement (final resolved URL + redirects).

**Non-blocking suggestions**
- For reputation, define whether scores are computed on demand or cached/updated on vote changes to avoid expensive joins per request.
- For cost caps, specify behavior when cap reached (e.g., bot returns `do_nothing` and logs a reason).

---

## Round 2

### Lead
**Action:** SUBMIT_REVISION

All blocking issues addressed. Plan updated at `docs/phases/intelligence.md`.

**Changes made:**

1. **Scope clarified (6 features, 2 moved to out-of-scope):**
   - Moved "embedding-based memory filtering" to out-of-scope (Phase 4+)
   - Moved "per-bot pace overrides" to out-of-scope (adds scheduler complexity)
   - Added testable success criterion for relationship evolution: "After 10+ bot interactions, at least one relationship has history events"

2. **Cold memory storage + schedule locked in:**
   - Storage: SQLAlchemy `ColdMemory` model (not JSON file)
   - Trigger: Threshold check (facts > 50 OR memories > 30) after each heartbeat
   - Backup: Weekly APScheduler job (Sunday 3am)
   - Retention: Keep all cold summaries (they're small)
   - Pruning: Old items removed from warm memory after compression

3. **Web search implementation locked in:**
   - Wikipedia API only for Phase 3 (no paid keys required)
   - Hardcoded base URL - no URL following or redirect handling needed
   - Returns text extracts, not full page content
   - Success criterion: "Web search via Wikipedia API returns results for valid queries"

**Non-blocking suggestions addressed:**
- Reputation: Cached on Bot model, updated on vote changes (not computed on demand)
- Cost caps: Bot returns `do_nothing` with reason when cap exceeded, no LLM call made

**Success criteria now 15 items** covering all in-scope features with testable conditions.

### Reviewer
**Action:** APPROVE

Approved. The plan now locks in storage/scheduling and the Wikipedia-only search approach, and the scope/success criteria are concrete and testable.

---

<!-- CYCLE_STATUS (single source of truth - do not duplicate above) -->
READY_FOR: reviewer
ROUND: 2
STATE: approved
<!-- /CYCLE_STATUS -->
