# Changelog

All notable changes to the 47 Doors University Support Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Hackathon Labs Curriculum** (`001-hackathon-labs`): Complete 8-hour hackathon curriculum with 8 progressive lab exercises
  - Lab 00: Environment Setup (30 min) - Prerequisites verification and Azure configuration
  - Lab 01: Understanding AI Agents (90 min) - Three-agent pattern and intent classification
  - Lab 02: Azure MCP Setup (30 min) - Model Context Protocol configuration
  - Lab 03: Spec-Driven Development (45 min) - Writing specs and constitutions for AI agents
  - Lab 04: Build RAG Pipeline (2 hours) - Azure AI Search with hybrid search and citations
  - Lab 05: Agent Orchestration (2 hours) - QueryAgent → RouterAgent → ActionAgent pipeline
  - Lab 06: Deploy with azd (90 min) - Docker containerization and Azure deployment
  - Lab 07: MCP Server (60 min) - Stretch goal for exposing 47 Doors as MCP server

- **Coach Guide Materials** (`coach-guide/`)
  - `FACILITATION.md` - 8-hour timeline with pacing markers and intervention points
  - `TROUBLESHOOTING.md` - Per-lab common issues and quick fixes
  - `ASSESSMENT_RUBRIC.md` - 100-point scoring rubric across 6 criteria
  - `TALKING_POINTS.md` - Phase transition messaging and key concepts

- **Participant Documentation** (`docs/hackathon/`)
  - `PARTICIPANT_GUIDE.md` - Quick reference for hackathon participants
  - `QUICK_REFERENCE.md` - Cheat sheet with commands and file locations

- **Shared Resources** (`shared/`)
  - `constitution.md` - Higher education AI agent principles (FERPA, accessibility, escalation)
  - `department_routing.json` - Department configuration with hours and routing keywords
  - `university_schema.json` - JSON Schema definitions for curriculum entities
  - `sample_queries.json` - 56 test queries for intent classification testing

- **Knowledge Base Content** (`labs/04-build-rag-pipeline/data/`)
  - 54 knowledge base articles across 5 departments:
    - Financial Aid (12 articles)
    - Registration (12 articles)
    - Housing (10 articles)
    - IT Support (10 articles)
    - Policies (10 articles)

- **Start/Solution Code Pattern**
  - Lab 02: MCP configuration templates
  - Lab 04: search_tool.py, retrieve_agent.py (RAG pipeline)
  - Lab 05: query_agent.py, router_agent.py, action_agent.py, pipeline.py (orchestration)
  - Lab 06: Dockerfile, docker-compose.yml, azure.yaml templates
  - Lab 07: mcp_server.py (MCP tools implementation)

### Changed

- Updated main README.md with hackathon curriculum section and lab links
- Added `.dockerignore` for optimized container builds

## [1.0.0] - 2026-01-15

### Added

- Initial release of 47 Doors University Support Agent
- Three-agent architecture (QueryAgent, RouterAgent, ActionAgent)
- FastAPI backend with Azure OpenAI integration
- React frontend with TypeScript
- Azure deployment with Bicep templates
- Docker Compose for local development
- Mock data for development without Azure services
