# 47doors Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-02

## Active Technologies

- Python 3.11+ (backend), TypeScript 5 (frontend), Node.js 18+ + FastAPI 0.109+, Pydantic v2.5+, React 18, Azure OpenAI, Azure AI Search (001-boot-camp-labs)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (backend), TypeScript 5 (frontend), Node.js 18+: Follow standard conventions

## Recent Changes

- 001-boot-camp-labs: Added Python 3.11+ (backend), TypeScript 5 (frontend), Node.js 18+ + FastAPI 0.109+, Pydantic v2.5+, React 18, Azure OpenAI, Azure AI Search

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

<!-- MANUAL ADDITIONS START -->
## Voice Feature Build (002-voice-interaction)

### Mission
Implement the voice interaction feature per specs/002-voice-interaction/. Adds real-time voice conversation using Azure OpenAI GPT-4o Realtime API via WebRTC. The existing 3-agent pipeline is exposed as Realtime API function tools.

### Source of Truth
- Spec: specs/002-voice-interaction/spec.md
- Plan: specs/002-voice-interaction/plan.md
- Tasks: specs/002-voice-interaction/tasks.md
- Constitution: .specify/memory/constitution.md

### Execution Rules
1. Follow tasks.md in phase order (Phase 1-8)
2. Write tests BEFORE implementation (Constitution Principle V)
3. After each phase run: cd backend && python -m pytest -x
4. Commit after each phase: feat(voice): Phase N - description
5. Push after each phase commit
6. If tests fail, fix before moving to next phase
7. MVP cutline is Phase 3 — prioritize Phases 1-3
8. Do NOT modify existing text chat functionality
9. For mock mode: ensure voice works without Azure credentials
<!-- MANUAL ADDITIONS END -->

## Documentation Standards

All markdown documents created or modified in this project MUST follow these conventions:

### Emojis
- Use relevant emojis in section headers (e.g., 🎯 Goals, 🏗️ Architecture, ✅ Done, ⚠️ Warnings, 🧪 Testing, 🚀 Deployment, 📋 Tasks, 🔧 Configuration, 🛡️ Security, 📊 Status)
- Use ✅ ❌ ⏳ 🔄 for task/checklist status indicators

### Status Bars
- Every doc must include a status bar at the top after the title:
```
| Status | Owner | Phase | Last Updated |
|--------|-------|-------|--------------|
| ⏳ In Progress | Brobot | Phase 2 | 2026-03-01 |
```

### Version Control Matrix
- Every doc must end with a version control matrix:
```
## 📋 Version Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-01 | Brobot | Initial creation |
```

- Use semver: MAJOR.MINOR.PATCH
- Update the matrix on every meaningful edit
