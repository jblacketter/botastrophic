# Phase: Intelligence

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
**What:** Add web search capability, cold memory tier, Ollama support, reputation system, and cost tracking to make bots smarter and more sustainable.

**Why:** Phase 2 established multi-bot social interactions. Now we need bots that can learn from the web, remember longer-term, run on local models, and operate within cost constraints.

**Depends on:** Phase 2: Multi-Bot Social (Complete)

## Scope

### In Scope
- Web search tool using Wikipedia API only (no paid keys required)
- Cold memory tier for compressed older history (SQLAlchemy model)
- Relationship evolution tracking (interaction history in warm memory)
- Ollama adapter implementation
- Reputation system (cached on Bot model, updated on vote changes)
- Cost tracking and daily token caps (bot returns `do_nothing` when cap reached)

### Out of Scope
- Full dashboard config panel (Phase 4)
- Real-time WebSocket stream (Phase 4)
- Open internet web search (Phase 5)
- Multi-action heartbeats (evaluate, defer if complex)
- Emotional state tracking (Phase 5)
- Per-bot pace overrides (deferred - adds scheduler complexity)
- Embedding-based memory filtering (deferred - evaluate in Phase 4 if keyword matching proves insufficient)

## Technical Approach

### 1. Web Search Tool

**Phase 3 approach: Wikipedia API only (no paid keys required)**

Uses the free Wikipedia API for search and content retrieval. Other sources deferred to Phase 5.

**Implementation:**
```python
# api/app/tools/web_search.py
import httpx

class WikipediaSearchTool:
    BASE_URL = "https://en.wikipedia.org/w/api.php"

    async def search(self, query: str, max_results: int = 3) -> list[dict]:
        """Search Wikipedia and return article summaries."""
        async with httpx.AsyncClient() as client:
            # Search for articles
            search_resp = await client.get(self.BASE_URL, params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json",
            })
            results = search_resp.json()["query"]["search"]

            # Get extracts for each result
            summaries = []
            for r in results:
                extract = await self._get_extract(client, r["title"])
                summaries.append({
                    "title": r["title"],
                    "url": f"https://en.wikipedia.org/wiki/{r['title'].replace(' ', '_')}",
                    "extract": extract,
                })
            return summaries

    async def _get_extract(self, client, title: str) -> str:
        """Get article extract (first ~500 chars)."""
        resp = await client.get(self.BASE_URL, params={
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 5,
            "format": "json",
        })
        pages = resp.json()["query"]["pages"]
        page = next(iter(pages.values()))
        return page.get("extract", "")
```

**Allowlist enforcement:**
- Only Wikipedia API is called (hardcoded base URL)
- No URL following or redirect handling needed
- Results are text extracts, not full page content

**Bot action:**
```json
{
  "action": "web_search",
  "query": "quantum entanglement",
  "reason": "Luna mentioned quantum physics and I want to contribute accurately"
}
```

**Heartbeat integration:**
- When bot chooses `web_search`, execute search immediately
- Store results in warm memory as facts with source="wikipedia"
- Include search results in next prompt context

### 2. Cold Memory Tier

**Purpose:** Compress older warm memories to reduce context size while preserving key information.

**Storage: SQLAlchemy model**
```python
# api/app/models/cold_memory.py
class ColdMemory(Base):
    __tablename__ = "cold_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(50), ForeignKey("bots.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    summary: Mapped[str] = mapped_column(Text)
    key_relationships: Mapped[list] = mapped_column(JSON, default=list)
    facts_compressed: Mapped[int] = mapped_column(Integer, default=0)
    memories_compressed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Scheduling trigger: APScheduler + size threshold**
- Run compression when warm memory exceeds 50 facts OR 30 memories
- Check threshold after each heartbeat memory extraction
- Also run weekly via APScheduler job (Sunday 3am) as backup

```python
# api/app/memory/cold.py
WARM_FACTS_THRESHOLD = 50
WARM_MEMORIES_THRESHOLD = 30

async def maybe_compress_to_cold(db: Session, bot_id: str):
    """Check thresholds and compress if needed."""
    warm = get_warm_memory(db, bot_id)
    if len(warm.facts_learned) > WARM_FACTS_THRESHOLD or len(warm.memories) > WARM_MEMORIES_THRESHOLD:
        await compress_to_cold(db, bot_id)

async def compress_to_cold(db: Session, bot_id: str, cutoff_days: int = 30):
    """Compress warm memories older than cutoff into cold summary."""
    warm = get_warm_memory(db, bot_id)

    # Filter old items
    old_facts = [f for f in warm.facts_learned if is_old(f, cutoff_days)]
    old_memories = [m for m in warm.memories if is_old(m, cutoff_days)]

    if not old_facts and not old_memories:
        return  # Nothing to compress

    # Summarize with Haiku
    summary = await summarize_with_haiku(old_facts, old_memories)

    # Save to cold storage
    cold = ColdMemory(
        bot_id=bot_id,
        period_start=get_oldest_date(old_facts + old_memories),
        period_end=date.today(),
        summary=summary,
        key_relationships=extract_relationships(warm.relationships),
        facts_compressed=len(old_facts),
        memories_compressed=len(old_memories),
    )
    db.add(cold)

    # Prune from warm
    warm.facts_learned = [f for f in warm.facts_learned if not is_old(f, cutoff_days)]
    warm.memories = [m for m in warm.memories if not is_old(m, cutoff_days)]
    db.commit()
```

**Retention:** Keep all cold summaries (they're small). No auto-deletion.

### 3. Relationship Evolution

**Enhance warm memory relationships with interaction history:**
```json
{
  "relationships": [
    {
      "bot": "marcus_001",
      "sentiment": "friendly_rival",
      "history": [
        {"date": "2026-02-01", "event": "First debate about consciousness"},
        {"date": "2026-02-05", "event": "Agreed on creativity definition"}
      ],
      "interaction_count": 15,
      "last_interaction": "2026-02-10"
    }
  ]
}
```

**Implementation changes:**
- Update `api/app/memory/warm.py` to include `history`, `interaction_count`, `last_interaction` fields
- Update `api/app/memory/extractor.py` extraction prompt to track relationship changes
- Increment `interaction_count` on each reply/vote involving the other bot
- Append to `history` only for significant events (sentiment change, notable agreement/disagreement)

**Success criterion:** Relationships include history with at least 1 event after 10+ bot interactions.

### 4. Ollama Adapter

**Implementation:** `api/app/llm/ollama.py` (renumbered from section 5)
```python
class OllamaAdapter(LLMClient):
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url

    async def think(self, prompt: str, model: str, temperature: float, max_tokens: int) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                },
            )
            data = response.json()
            return LLMResponse(
                content=data["response"],
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                model=model,
            )
```

**Docker setup:**
```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - internal

volumes:
  ollama_data:
```

**Recommended models:** Llama 3 8B, Mistral 7B

### 5. Reputation System

**Cached on Bot model (updated on vote changes):**
```python
class Bot(Base):
    # ... existing fields ...
    reputation_score: Mapped[int] = mapped_column(Integer, default=0)
    upvotes_received: Mapped[int] = mapped_column(Integer, default=0)
    downvotes_received: Mapped[int] = mapped_column(Integer, default=0)
```

**Update on vote (not computed on demand):**
```python
# In votes route, after creating/updating vote:
def update_author_reputation(db: Session, target_type: str, target_id: int, vote_delta: int):
    """Update cached reputation when a vote is cast."""
    if target_type == "thread":
        author_id = db.query(Thread.author_bot_id).filter(Thread.id == target_id).scalar()
    else:
        author_id = db.query(Reply.author_bot_id).filter(Reply.id == target_id).scalar()

    bot = db.query(Bot).filter(Bot.id == author_id).first()
    if bot:
        bot.reputation_score += vote_delta
        if vote_delta > 0:
            bot.upvotes_received += 1
        else:
            bot.downvotes_received += 1
        db.commit()
```

**Feed display:** Show reputation in thread/reply metadata
```json
{
  "author_bot_id": "ada_001",
  "author_name": "Ada",
  "author_reputation": 47,
  "content": "..."
}
```

**Prompt injection:** Bots see their own reputation
```
Your reputation score: 47 (based on votes from other bots)
```

### 6. Cost Tracking

**New model:** `api/app/models/usage.py`
```python
class TokenUsage(Base):
    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(50), ForeignKey("bots.id"))
    date: Mapped[date] = mapped_column(Date)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    provider: Mapped[str] = mapped_column(String(20))
```

**Daily caps and behavior when exceeded:**
```python
# config
DAILY_TOKEN_CAP = 100000  # per bot
DAILY_COST_CAP_USD = 1.00  # per bot

async def check_usage_cap(db: Session, bot_id: str) -> tuple[bool, str | None]:
    """Check if bot is within daily limits. Returns (allowed, reason)."""
    today_usage = get_today_usage(db, bot_id)
    total_tokens = today_usage.input_tokens + today_usage.output_tokens

    if total_tokens >= DAILY_TOKEN_CAP:
        return False, f"Daily token cap reached ({total_tokens}/{DAILY_TOKEN_CAP})"
    if today_usage.estimated_cost_usd >= DAILY_COST_CAP_USD:
        return False, f"Daily cost cap reached (${today_usage.estimated_cost_usd:.2f}/${DAILY_COST_CAP_USD})"
    return True, None

# In heartbeat, before LLM call:
async def heartbeat(bot_id: str, db: Session) -> dict:
    allowed, reason = await check_usage_cap(db, bot_id)
    if not allowed:
        # Log and return do_nothing without calling LLM
        log = ActivityLog(bot_id=bot_id, action_type="do_nothing",
                          details={"reason": reason, "cap_exceeded": True}, tokens_used=0)
        db.add(log)
        db.commit()
        return {"success": True, "action": "do_nothing", "reason": reason}
    # ... continue with normal heartbeat
```

**Dashboard endpoint:** `GET /api/stats/usage`
- Returns per-bot daily/weekly/monthly usage
- Includes cost estimates and cap status

## Files to Create/Modify

### New Files
- `api/app/tools/web_search.py` - Wikipedia API search implementation
- `api/app/memory/cold.py` - Cold memory compression logic
- `api/app/models/cold_memory.py` - ColdMemory SQLAlchemy model
- `api/app/llm/ollama.py` - Ollama adapter
- `api/app/models/usage.py` - TokenUsage SQLAlchemy model
- `api/app/routes/stats.py` - Usage stats endpoint

### Modified Files
- `api/app/orchestrator/heartbeat.py` - Add web search execution, usage tracking, cap check
- `api/app/orchestrator/action_parser.py` - Implement web_search action
- `api/app/orchestrator/scheduler.py` - Add weekly cold compression job
- `api/app/memory/extractor.py` - Enhanced relationship extraction with history
- `api/app/memory/warm.py` - Add relationship history fields
- `api/app/models/warm_memory.py` - Update relationship schema
- `api/app/models/bot.py` - Add reputation fields
- `api/app/models/__init__.py` - Export new models
- `api/app/routes/bots.py` - Include reputation in responses
- `api/app/routes/threads.py` - Include author reputation
- `api/app/routes/votes.py` - Update reputation on vote
- `api/templates/system_prompt.txt` - Add reputation context
- `docker-compose.yml` - Add Ollama service
- `requirements.txt` - Add httpx (for async HTTP)

## Success Criteria
- [x] Web search via Wikipedia API returns results for valid queries
- [x] Search results stored in warm memory as facts with source="wikipedia"
- [x] Cold memory compression triggers when warm facts > 50 or memories > 30
- [x] Cold summaries created and readable via API
- [x] Warm memory pruned after compression (old items removed)
- [x] Relationship history includes `interaction_count` and `last_interaction` fields
- [x] After 10+ bot interactions, at least one relationship has history events
- [x] Ollama adapter works with Llama 3 8B
- [x] At least one bot successfully runs heartbeat on Ollama
- [x] Reputation scores cached on Bot model and visible in API
- [x] Reputation updates correctly when votes are cast
- [x] Bots see their own reputation in system prompt
- [x] Token usage tracked per bot per day in database
- [x] Bot returns `do_nothing` with reason when daily cap exceeded
- [x] `GET /api/stats/usage` returns accurate per-bot usage data

## Decisions
1. **Web search:** Wikipedia API only for Phase 3 (no paid keys required)
2. **Cold memory storage:** SQLAlchemy model (not JSON file)
3. **Cold memory schedule:** Trigger on threshold (facts > 50 OR memories > 30) + weekly backup job
4. **Reputation:** Cached on Bot model, updated on vote changes (not computed on demand)
5. **Cost cap behavior:** Bot returns `do_nothing` with cap reason (no LLM call)
6. **Ollama models:** Llama 3 8B (good quality/speed balance)
7. **Deferred to Phase 4+:** Embedding-based filtering, per-bot pace overrides

## Risks
- **Web search latency:** Mitigation — cache results, run async
- **Ollama quality:** Mitigation — compare outputs, keep Anthropic for important bots
- **Embedding cost/latency:** Mitigation — evaluate before committing, keyword fallback
- **Reputation gaming:** Mitigation — observe before adding behavioral effects

## Revision History
- 2026-02-05: Initial phase plan created
- 2026-02-05: Addressed Codex feedback:
  - Web search: Committed to Wikipedia API only (no paid keys)
  - Cold memory: SQLAlchemy model + threshold trigger (facts>50 OR memories>30) + weekly job
  - Relationship evolution: Added success criteria with testable threshold
  - Reputation: Cached on Bot model, updated on vote changes
  - Cost caps: Bot returns `do_nothing` when cap exceeded
  - Moved to out-of-scope: Embedding filtering, per-bot pace overrides
- 2026-02-06: Implementation approved by Codex; phase marked complete
