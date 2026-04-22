# Tasks: NYU Oracle

**Feature:** 003-nyu-oracle
**Branch:** `feature/nyu-oracle`
**Order:** dependency-ordered; reflects the actual sequence of tonight's implementation.
**Patch source:** `C:\Users\segayle\Downloads\nyu-oracle-patch\`

Legend: `[ ]` pending · `[x]` done · **P0** = blocks demo · **P1** = nice to have

---

## Phase 0 — Preconditions

- [ ] **T-00.1** [P0] Confirm branch: `git rev-parse --abbrev-ref HEAD` returns `feature/nyu-oracle`.
- [ ] **T-00.2** [P0] Confirm patch files exist in `C:\Users\segayle\Downloads\nyu-oracle-patch\` (all 5 code files + `INTEGRATION.md`).
- [ ] **T-00.3** [P0] Confirm `backend\app\services\transcript_bus.py` and `backend\app\api\transcripts.py` exist (Oracle depends on them).

---

## Phase 1 — Write tests first (Constitution Principle V)

> Tests are authored against the **public interface** described in `spec.md §4` and `plan.md §6`. They are expected to **fail** until Phase 2 lands the patch files. This satisfies TDD: we are validating the shipping implementation, not the reference.

- [ ] **T-01.1** [P0] Create `backend\tests\test_oracle_service.py` with three tests:
  - `test_distill_visual_prompt_appends_style_suffix`
  - `test_distill_visual_prompt_fallback_on_exception`
  - `test_generate_returns_error_when_endpoint_missing`
- [ ] **T-01.2** [P0] Create `backend\tests\test_oracle_api.py` with six tests:
  - `test_image_happy_path`
  - `test_image_blocked_path`
  - `test_image_error_path`
  - `test_image_rejects_empty_text`
  - `test_provoke_publishes_to_bus`
  - `test_provoke_forbidden_in_production`
- [ ] **T-01.3** [P0] Run `cd backend; python -m pytest tests\test_oracle_service.py tests\test_oracle_api.py -x -q` and **confirm they fail with ImportError** (no `app.api.oracle` yet). This proves the tests are wired correctly.

---

## Phase 2 — Copy new files from patch

- [ ] **T-02.1** [P0] Copy `C:\Users\segayle\Downloads\nyu-oracle-patch\oracle_service.py` → `C:\Users\segayle\repos\47doors\backend\app\services\oracle_service.py`.
- [ ] **T-02.2** [P0] Copy `C:\Users\segayle\Downloads\nyu-oracle-patch\oracle.py` → `C:\Users\segayle\repos\47doors\backend\app\api\oracle.py`.
- [ ] **T-02.3** [P0] Copy `C:\Users\segayle\Downloads\nyu-oracle-patch\oracle.ts` → `C:\Users\segayle\repos\47doors\frontend\src\types\oracle.ts`.
- [ ] **T-02.4** [P0] Copy `C:\Users\segayle\Downloads\nyu-oracle-patch\useOracle.ts` → `C:\Users\segayle\repos\47doors\frontend\src\hooks\useOracle.ts`.
- [ ] **T-02.5** [P0] Copy `C:\Users\segayle\Downloads\nyu-oracle-patch\OraclePage.tsx` → `C:\Users\segayle\repos\47doors\frontend\src\components\OraclePage.tsx`.

Powershell one-liner (optional):
```powershell
$src = "C:\Users\segayle\Downloads\nyu-oracle-patch"
$repo = "C:\Users\segayle\repos\47doors"
Copy-Item "$src\oracle_service.py" "$repo\backend\app\services\oracle_service.py"
Copy-Item "$src\oracle.py"         "$repo\backend\app\api\oracle.py"
Copy-Item "$src\oracle.ts"         "$repo\frontend\src\types\oracle.ts"
Copy-Item "$src\useOracle.ts"      "$repo\frontend\src\hooks\useOracle.ts"
Copy-Item "$src\OraclePage.tsx"    "$repo\frontend\src\components\OraclePage.tsx"
```

---

## Phase 3 — Apply diffs to existing files

- [ ] **T-03.1** [P0] Edit `backend\app\main.py`:
  - Add `from app.api.oracle import router as oracle_router` to imports.
  - In `create_app()`, after existing `include_router` calls, add:
    `app.include_router(oracle_router, prefix=f"{settings.api_prefix}/oracle", tags=["Oracle"])`.
- [ ] **T-03.2** [P0] Edit `backend\app\core\config.py`: add to `Settings`:
  ```python
  oracle_image_deployment: str = Field(
      default="gpt-image-1",
      description="Azure OpenAI Images deployment (gpt-image-1 or dall-e-3)",
  )
  ```
- [ ] **T-03.3** [P0] Append `ORACLE_IMAGE_DEPLOYMENT=gpt-image-1` to `backend\.env`.
- [ ] **T-03.4** [P0] Edit `frontend\src\App.tsx` (around line 24, next to `isDirectLiveRoute`):
  - Add `const isDirectOracleRoute = window.location.pathname.toLowerCase() === '/oracle';`
  - Add `import { OraclePage } from './components/OraclePage';`
  - Before the normal layout `return`, add `if (isDirectOracleRoute) return <OraclePage />;`

---

## Phase 4 — Shift+B manual override

- [ ] **T-04.1** [P1] In `frontend\src\components\OraclePage.tsx`, add a `useEffect` that listens for `window` `keydown` with `event.shiftKey && (event.key === 'B' || event.key === 'b')` and locally sets a simulated block state. Reason string: `"Simulated block (operator override)"`. See spec FR-7. Pressing again (or a new `agent_speech`) clears it.

---

## Phase 5 — Run tests

- [ ] **T-05.1** [P0] `cd backend; python -m pytest tests\test_oracle_service.py tests\test_oracle_api.py -x -q` — all 9 tests pass.
- [ ] **T-05.2** [P0] `cd backend; python -m pytest tests\ -x -q` — full suite still green (no regressions).
- [ ] **T-05.3** [P0] `cd frontend; npx tsc --noEmit` — no type errors.
- [ ] **T-05.4** [P0] `cd frontend; npx vite build` — build succeeds.

---

## Phase 6 — Local smoke test

- [ ] **T-06.1** [P0] Terminal 1: `cd backend; uvicorn app.main:app --reload --port 8000`.
- [ ] **T-06.2** [P0] Terminal 2: `cd frontend; npm run dev`.
- [ ] **T-06.3** [P0] Open `http://localhost:5173/oracle` — verify idle state renders.
- [ ] **T-06.4** [P0] Terminal 3: fire the three `curl` calls from `INTEGRATION.md` (`call_started`, `user_speech`, `agent_speech`). Confirm:
  - user utterance appears as italic serif,
  - agent reply appears as oracle typography,
  - image cross-fades in behind within ~12 s.
- [ ] **T-06.5** [P1] Press **Shift+B** on `/oracle` — confirm crimson BLOCKED state appears with reason `"Simulated block (operator override)"`.
- [ ] **T-06.6** [P1] `provoke` with an agent_speech containing a policy-violating string; confirm real BLOCKED state appears (if image deployment's safety is aggressive enough) or accept Shift+B as the guaranteed path.

---

## Phase 7 — Commit & hand off

- [ ] **T-07.1** [P0] `git add specs\003-nyu-oracle` then `git commit -m "docs(oracle): add spec-kit artifacts for nyu-oracle feature"`.
- [ ] **T-07.2** [P0] Commit code separately (tests first, then patch files) on the same branch. Suggested commits:
  - `test(oracle): add failing unit tests for oracle service + api`
  - `feat(oracle): add visual-prompt distillation and image gen service`
  - `feat(oracle): add /api/oracle/image and /api/oracle/provoke endpoints`
  - `feat(oracle): add /oracle projector route (types, hook, page)`
  - `feat(oracle): add Shift+B manual BLOCKED override`
  - `chore(config): add ORACLE_IMAGE_DEPLOYMENT setting`
- [ ] **T-07.3** [P0] **Do NOT push.** User reviews locally first.

---

## Phase 8 — Deploy (post-review, outside this spec)

Deployment steps (Container Apps env var + redeploy) are documented in the user's existing deployment runbook (`C:\Users\segayle\Downloads\...`). Not duplicated here per scope boundary.

Pre-talk verification (stage operator):
- [ ] **T-08.1** [P0] On prod, open `/oracle` on projector laptop, press F11 for fullscreen.
- [ ] **T-08.2** [P0] Fire one `POST /api/oracle/provoke` agent_speech call to confirm end-to-end before dialing.
- [ ] **T-08.3** [P0] Dial `+1 (913) 217-1946`; speak one benign turn; confirm image generates.
- [ ] **T-08.4** [P0] Confirm Shift+B still works on the projector browser as final safety net.

---

## Dependency graph

```
T-00.* ──► T-01.* ──► T-02.* ──► T-03.* ──► T-05.1 ──► T-05.2 ──► T-05.3 ──► T-05.4 ──► T-06.* ──► T-07.*
                                    │
                                    └──► T-04.1 ──┘
```

T-04.1 (Shift+B) is logically P1 but must be completed before T-06.5; it gates only the smoke-test step, not the primary flow.
