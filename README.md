# The Universal Front Door Support Agent

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmsftsean%2Fhiedcab_frontdoor_agent%2Fmain%2Finfra%2Fazuredeploy.json)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Azure](https://img.shields.io/badge/Azure-Ready-0078D4?style=flat&logo=microsoft-azure)](https://azure.microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Eliminate the "47 Front Doors" Problem** - A three-agent AI system that provides a single, intelligent entry point for university student support.

---

## Overview

The **Universal Front Door Support Agent** is a three-agent AI system that provides a single, intelligent entry point for all university student support requests. Instead of navigating multiple disconnected support channels, students interact with one interface that:

- **Detects intent** from natural language queries
- **Routes requests** to the correct department
- **Creates tickets** automatically in ServiceNow
- **Retrieves knowledge** articles for self-service
- **Escalates to humans** for policy-related requests

**Target Impact**: Increase first-contact resolution from **40%** to **65%**

### Solution Architecture

![Solution Architecture](./docs/architecture/architecture-overview.jpg)

---

## Hackathon Labs Overview

**Build this entire system in 8 hours!** This repository includes a complete hackathon curriculum with 8 progressive labs:

| Lab | Title | Duration | What You'll Build |
|:---:|-------|:--------:|-------------------|
| 00 | [Environment Setup](./labs/00-setup/) | 30 min | Verify prerequisites, configure Azure credentials, test local development environment |
| 01 | [Understanding AI Agents](./labs/01-understanding-agents/) | 90 min | Learn multi-agent vs monolithic architectures, build an intent classifier with >90% accuracy |
| 02 | [Azure MCP Setup](./labs/02-azure-mcp-setup/) | 30 min | Configure Model Context Protocol for Azure OpenAI and AI Search integration |
| 03 | [Spec-Driven Development](./labs/03-spec-driven-development/) | 45 min | Write feature specs and AI constitution before generating code with Claude/Copilot |
| 04 | [Build RAG Pipeline](./labs/04-build-rag-pipeline/) | 2 hrs | Implement hybrid search (vector + keyword) with Azure AI Search and 54 KB articles |
| 05 | [Agent Orchestration](./labs/05-agent-orchestration/) | 2 hrs | Wire up QueryAgent → RouterAgent → ActionAgent pipeline with session management |
| 06 | [Deploy with azd](./labs/06-deploy-with-azd/) | 90 min | Containerize with Docker, deploy to Azure Container Apps with `azd up` |
| 07 | [MCP Server](./labs/07-mcp-server/) | 60 min | *(Stretch)* Expose your agent as an MCP server for Claude Desktop integration |

### Learning Path

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Lab 00    │     │   Lab 01    │     │   Lab 02    │     │   Lab 03    │
│   Setup     │────▶│   Agents    │────▶│    MCP      │────▶│   Specs     │
│   30 min    │     │   90 min    │     │   30 min    │     │   45 min    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
       ┌───────────────────────────────────────────────────────────┘
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Lab 04    │     │   Lab 05    │     │   Lab 06    │     │   Lab 07    │
│    RAG      │────▶│  Pipeline   │────▶│   Deploy    │────▶│    MCP      │
│   2 hrs     │     │   2 hrs     │     │   90 min    │     │   60 min    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Key Skills by Lab

| Skill | Lab 00 | Lab 01 | Lab 02 | Lab 03 | Lab 04 | Lab 05 | Lab 06 | Lab 07 |
|-------|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
| Python/FastAPI | | | | | ● | ● | ● | ● |
| Azure OpenAI | | ● | ● | | ● | ● | | |
| Azure AI Search | | | ● | | ● | ● | | |
| Prompt Engineering | | ● | | ● | ● | ● | | |
| Docker/Containers | | | | | | | ● | |
| Azure Deployment | | | | | | | ● | |
| MCP Protocol | | | ● | | | | | ● |

### Azure Service Requirements

Labs 00-03 and 06 can run entirely in **mock mode** without Azure credentials. Labs 04, 05, and 07 require live Azure OpenAI for their core learning objectives.

| Requirement | Lab 00 | Lab 01 | Lab 02 | Lab 03 | Lab 04 | Lab 05 | Lab 06 | Lab 07 |
|-------------|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
| Mock Mode OK | ✓ | ✓ | ✓ | ✓ | | | ✓ | |
| Azure OpenAI (GPT-4o) | | | | | **Required** | **Required** | | **Required** |
| Azure AI Search | | | | | **Required** | **Required** | | |

> **Cost-Saving Tip**: Run Labs 00-03 with `USE_MOCK_MODE=true` to validate your setup before provisioning Azure services. Switch to live Azure OpenAI starting in Lab 04 when you build the RAG pipeline.

**Coach Materials**: [coach-guide/](./coach-guide/) | **Participant Guide**: [docs/hackathon/](./docs/hackathon/)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)

### Option 1: Local Development (Recommended)

```bash
# Clone repository
git clone https://github.com/msftsean/hiedcab_frontdoor_agent.git
cd hiedcab_frontdoor_agent

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/health |

### Option 2: Docker Compose

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |

---

## Architecture

### Three-Agent Conversation Flow

![Agent Workflow](./docs/architecture/agent-workflow.jpg)

The three-agent system processes each user query through a coordinated pipeline:

1. **QueryAgent** - Classifies intent (financial aid, registration, housing, technical support, general)
2. **RouterAgent** - Searches Azure AI Search for relevant KB articles
3. **ActionAgent** - Generates contextual responses and determines if a support ticket is needed

### Azure Infrastructure

![Deployment Infrastructure](./docs/architecture/deployment-infrastructure.jpg)

| Service | Purpose |
|---------|---------|
| Azure OpenAI | Intent classification, response generation |
| Container Apps | Backend API hosting |
| Static Web Apps | Frontend hosting |
| Cosmos DB | Session and audit storage |
| AI Search | Knowledge base search |
| Key Vault | Secrets management |

---

## Azure Deployment

### Supported Regions

Deploy to regions with GPT-4o availability:

| Region | GPT-4o | GPT-4o-mini |
|--------|:------:|:-----------:|
| East US | Yes | Yes |
| East US 2 | Yes | Yes |
| West US 3 | Yes | Yes |
| UK South | Yes | Yes |
| Sweden Central | Yes | Yes |

### Deploy with Azure Developer CLI

```bash
# Login to Azure
azd auth login

# Initialize and deploy
azd init
azd up
```

### Cost Estimates

![Cost Tiers](./docs/architecture/cost-tiers.jpg)

| Scale | Users | Monthly Cost |
|-------|------:|-------------:|
| Development | 1-10 | $50-100 |
| Small Pilot | 100-500 | $160-305 |
| Medium | 500-2,000 | $400-700 |
| Production | 2,000-10,000 | $1,000-2,500 |

See [Cost Estimation Guide](./docs/deployment/COST_ESTIMATION.md) for details.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Submit support query |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/session/{id}` | Get session |
| `DELETE` | `/api/session/{id}` | End session |

### POST /api/chat

**Request:**
```json
{
  "message": "I forgot my password",
  "session_id": null
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "ticket_id": "TKT-IT-20260121-0001",
  "department": "IT",
  "status": "created",
  "message": "I've created a ticket for IT Support...",
  "knowledge_articles": [
    {
      "title": "How to Reset Your Password",
      "url": "https://kb.university.edu/password-reset",
      "relevance_score": 0.94
    }
  ],
  "escalated": false,
  "estimated_response_time": "2 hours"
}
```

---

## Testing

### Backend

```bash
cd backend
source .venv/bin/activate
pytest                           # Run all tests
pytest --cov=app --cov-report=html  # With coverage
```

### Frontend

```bash
cd frontend
npm test          # Unit tests
npm run test:e2e  # E2E tests
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Feature Spec](./docs/specs/spec.md) | Detailed requirements |
| [Data Model](./docs/specs/data-model.md) | Schema definitions |
| [Implementation Plan](./docs/specs/plan.md) | Development roadmap |
| [Customization Guide](./docs/customization/CUSTOMIZATION.md) | Hands-on customization lab |
| [Sample Customizations](./docs/customization/SAMPLE_CUSTOMIZATIONS.md) | Ready-to-use examples |
| [Cost Estimation](./docs/deployment/COST_ESTIMATION.md) | Detailed pricing |

---

## Project Structure

```
47doors/
├── backend/           # FastAPI Python backend
│   ├── app/
│   │   ├── agents/   # QueryAgent, RouterAgent, ActionAgent
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # Pydantic schemas
│   │   └── services/ # Azure integrations
│   └── tests/
├── frontend/          # React TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   └── services/
│   └── tests/
├── labs/              # Hackathon curriculum (8 labs)
│   ├── 00-setup/
│   ├── 01-understanding-agents/
│   ├── 02-azure-mcp-setup/
│   ├── 03-spec-driven-development/
│   ├── 04-build-rag-pipeline/
│   ├── 05-agent-orchestration/
│   ├── 06-deploy-with-azd/
│   └── 07-mcp-server/
├── coach-guide/       # Facilitation materials
├── shared/            # Common resources (constitution, schemas)
├── docs/              # Documentation
│   ├── architecture/ # Diagrams
│   ├── customization/
│   ├── deployment/
│   ├── hackathon/    # Participant guides
│   └── specs/        # Feature specifications
├── infra/             # Azure Bicep templates
├── docker-compose.yml
└── azure.yaml
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with Azure AI for Higher Education
</p>
