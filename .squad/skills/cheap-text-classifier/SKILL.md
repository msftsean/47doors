# Skill: Cheap Text Classifier (keyword-first, LLM fallback)

**Author:** Tank
**Origin:** `backend/app/services/oracle_gallery.py` (Oracle gallery sentiment router)

## When to use

You need to route a short string into one of N small, fixed categories, and:

- You have rough domain intuition for what words signal each category
- Sub-100ms latency matters (stage demo, voice loop, hot path)
- You want deterministic, unit-testable behavior on common inputs
- An LLM call is *acceptable* for the long tail but should be the exception, not the rule

Examples:
- Sentiment / mood routing for Oracle gallery image selection
- Intent pre-filtering before a more expensive agent call
- Cheap topic tagging for analytics

## When *not* to use

- Open-ended classification with hundreds of categories — use embeddings + nearest-neighbor
- Anything safety-critical where false negatives are unacceptable — use a real classifier
- Inputs longer than a few sentences where keyword density is unreliable

## Pattern

1. Define a `_KEYWORD_MAP: dict[str, list[str]]` — category → list of lowercase trigger words/substrings (use stems where possible: `"trembl"` matches `trembling`/`trembled`)
2. Define an explicit tie-break `_PRIORITY` tuple of categories (most-specific → most-generic). Encode product knowledge here — e.g., `institutional` beats `wonder` if both score equally
3. `_classify_keywords(text)`: lowercase, count substring hits per category, return highest-score category (using priority on ties), or `None` if zero hits
4. `_classify_llm(text)`: only fires when keywords return `None`. Send a tiny prompt: "Classify into one of: [slugs]. Reply with ONLY the slug." Use `max_tokens=10`, `temperature=0.0`. Validate the response is one of the known slugs.
5. Final fallback: a hard-coded "safe default" category for when even the LLM call fails / returns garbage

## Skeleton

```python
_PRIORITY = ("specific_a", "specific_b", "generic")
_KEYWORDS: dict[str, list[str]] = {"specific_a": [...], "specific_b": [...], "generic": [...]}

def _score(text: str) -> dict[str, int]:
    low = text.lower()
    return {c: sum(1 for k in kws if k in low) for c, kws in _KEYWORDS.items()}

def _classify_keywords(text: str) -> str | None:
    s = _score(text)
    if not any(s.values()):
        return None
    best = max(s.values())
    tied = [c for c, v in s.items() if v == best]
    if len(tied) == 1:
        return tied[0]
    for c in _PRIORITY:
        if c in tied:
            return c
    return tied[0]

def classify(text: str, default: str = "generic") -> str:
    if not text or not text.strip():
        return default
    if (kw := _classify_keywords(text)) is not None:
        return kw
    try:
        return _llm_one_shot(text)  # validated against known slugs
    except Exception:
        return default
```

## Testing

Three tests cover 90% of regressions:

1. **Happy keyword path** — a representative phrase routes to the expected category
2. **Empty / whitespace input** — returns the safe default without calling the LLM
3. **Tie-break** — a phrase matching keywords from two categories routes to the higher-priority one

LLM fallback is hard to assert deterministically; mock the client and assert it's only called when keyword scoring returns zero.

## Tradeoffs

- **Pro:** O(n_keywords) latency, deterministic, readable, testable, free
- **Con:** brittle on inputs that paraphrase around your keywords (that's what the LLM fallback is for)
- **Con:** keyword maps drift — review them whenever the upstream input distribution changes (e.g., new prompt templates)
