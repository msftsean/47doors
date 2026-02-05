# 🚀 Lab 06 - Deploy with azd

| 📋 Attribute | Value |
|-------------|-------|
| ⏱️ **Duration** | 90 minutes |
| 📊 **Difficulty** | ⭐⭐⭐ Advanced |
| 🎯 **Prerequisites** | Lab 05 completed |

---

## 📈 Progress Tracker

```
Lab Progress: [░░░░░░░░░░] 0% - Not Started

Checkpoints:
□ Step 1: Verify Docker Setup
□ Step 2: Test Locally with Docker Compose
□ Step 3: Install and Configure azd
□ Step 4: Initialize azd Environment
□ Step 5: Deploy with azd up
□ Step 6: Verify Deployment
□ Step 7: View Logs and Monitoring
□ Step 8: Clean Up (Optional)
```

---

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

1. 🐳 **Containerize your agent with Docker** - Package your application into Docker containers for consistent deployment
2. ☁️ **Deploy with azd up** - Use Azure Developer CLI to provision infrastructure and deploy your application in a single command
3. 📊 **Configure monitoring and health checks** - Set up application health monitoring and view logs in Azure

---

## 🤔 What is Azure Developer CLI (azd)?

**Azure Developer CLI (azd)** is a developer-centric command-line tool that accelerates the time it takes to get your application running in Azure. It provides:

### 🌟 Key Benefits

| ✨ Feature | 📝 Description |
|---------|-------------|
| **Single Command Deployment** | `azd up` provisions infrastructure AND deploys your code |
| **Template-Based** | Uses `azure.yaml` to define your application structure |
| **Infrastructure as Code** | Integrates with Bicep/Terraform for repeatable infrastructure |
| **Environment Management** | Manage multiple environments (dev, staging, prod) |
| **CI/CD Pipeline Generation** | Auto-generate GitHub Actions or Azure DevOps pipelines |

### 🏗️ How azd Works

```
+------------------+     +------------------+     +------------------+
|   azure.yaml     |     |   azd provision  |     |   Azure          |
|   (App Config)   | --> |   (Create Infra) | --> |   Resources      |
+------------------+     +------------------+     +------------------+
                                                          |
+------------------+     +------------------+              |
|   azd deploy     |     |   Container App  |              |
|   (Push Code)    | --> |   Running        | <------------+
+------------------+     +------------------+
```

### 📄 The azure.yaml File

The `azure.yaml` file describes your application to azd:

```yaml
name: university-front-door-agent

services:
  backend:
    project: ./backend
    language: python
    host: containerapp
    docker:
      path: Dockerfile

  frontend:
    project: ./frontend
    language: js
    host: staticwebapp

infra:
  provider: bicep
  path: ./infra
```

This tells azd:
- 📦 What services make up your application
- 🐍 What language/runtime each service uses
- 🏠 How to host each service (Container Apps, Static Web Apps, etc.)
- 🏗️ Where to find infrastructure definitions

---

## 🏗️ Architecture Overview

In this lab, you will deploy your agent system to Azure:

```
+------------------+     +------------------+     +------------------+
|   Local Docker   |     |   azd up         |     |   Azure          |
|   Compose Test   | --> |   (Provision +   | --> |   Container Apps |
|                  |     |    Deploy)       |     |   + AI Services  |
+------------------+     +------------------+     +------------------+
         |                                                 |
         v                                                 v
+------------------+                             +------------------+
|   Backend :8000  |                             |   /api/health    |
|   Frontend :3000 |                             |   Monitoring     |
+------------------+                             +------------------+
```

### ☁️ Azure Resources Created

| 🔧 Resource | 📝 Purpose |
|----------|---------|
| 📦 **Container Apps Environment** | Hosts your containerized backend |
| 🗄️ **Azure Container Registry** | Stores your Docker images |
| 🌐 **Static Web App** | Hosts your frontend |
| 🤖 **Azure OpenAI** | LLM inference for your agent |
| 🔍 **Azure AI Search** | Vector search for RAG |
| 💾 **Cosmos DB** | Session and conversation storage |
| 📊 **Log Analytics** | Monitoring and logging |

---

## 📝 Step-by-Step Instructions

### 🔹 Step 1: Verify Docker Setup

Before deploying to Azure, ensure your application runs correctly in Docker locally.

#### 1a: 🔍 Check Docker Installation

```bash
# ✅ Verify Docker is installed and running
docker --version
docker info

# ✅ Verify Docker Compose is available
docker compose version
```

If Docker is not installed, see [Docker Desktop installation guide](https://docs.docker.com/desktop/).

#### 1b: 📄 Review the Dockerfile

Your backend Dockerfile should look similar to:

```dockerfile
# 🐳 Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 📦 Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 📋 Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 💻 Copy application code
COPY . .

# 🔒 Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 8000

# 💚 Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key elements:
- 🏗️ **Multi-stage builds** for smaller images (if needed)
- 🔒 **Non-root user** for security
- 💚 **Health check** for container orchestration
- 📦 **Proper caching** of dependencies

**Task:** Review your docker-compose.yml and ensure all services are defined correctly. 📝

### 🔹 Step 2: Test Locally with Docker Compose

Build and run your containers locally before deploying to Azure.

#### 2a: 🔨 Build the Containers

```bash
# 🔨 Build all services
docker compose build

# 🔨 Or build a specific service
docker compose build backend
```

#### 2b: 🚀 Start the Services

```bash
# 🚀 Start all services in detached mode
docker compose up -d

# 📋 Watch the logs
docker compose logs -f
```

#### 2c: ✅ Verify Services are Running

```bash
# 📊 Check container status
docker compose ps

# Expected output:
# NAME                    STATUS              PORTS
# 47doors-backend-1      Up (healthy)        0.0.0.0:8000->8000/tcp
# 47doors-frontend-1     Up                  0.0.0.0:3000->80/tcp
```

#### 2d: 🧪 Test the Health Endpoint

```bash
# 💚 Test backend health
curl http://localhost:8000/api/health
```

#### 2e: 🌐 Test the Application

Open your browser and navigate to:
- 🎨 Frontend: http://localhost:3000
- 📚 Backend API docs: http://localhost:8000/docs

### 🔹 Step 3: Install and Configure azd

#### 3a: 📦 Install Azure Developer CLI

```bash
# 🪟 Windows (PowerShell)
winget install microsoft.azd

# 🍎 macOS
brew tap azure/azd && brew install azd

# 🐧 Linux
curl -fsSL https://aka.ms/install-azd.sh | bash
```

Verify installation:
```bash
azd version
# Expected: azd version 1.x.x
```

#### 3b: 🔐 Authenticate with Azure

```bash
# 🔐 Login to Azure
azd auth login

# 🌐 This will open a browser for authentication
# ✅ After login, you'll see: Logged in to Azure.
```

### 🔹 Step 4: Initialize azd Environment

```bash
# 🏗️ Initialize azd in your project
azd init

# 🌍 Create a new environment (e.g., dev, staging, prod)
azd env new dev

# ⚙️ Set environment-specific values
azd env set AZURE_LOCATION eastus
azd env set AZURE_SUBSCRIPTION_ID <your-subscription-id>
```

### 🔹 Step 5: Deploy with azd up

#### 5a: 🚀 Run azd up

The magic command that provisions AND deploys:

```bash
# 🚀 Provision infrastructure and deploy application
azd up
```

This single command:
1. ☁️ Creates all Azure resources defined in your Bicep templates
2. 🐳 Builds your Docker containers
3. ⬆️ Pushes images to Azure Container Registry
4. 🚀 Deploys containers to Azure Container Apps
5. ⚙️ Configures networking and environment variables

#### 5b: 📊 Monitor the Deployment

```
Provisioning Azure resources (azd provision)
  (✓) Done: Resource group: rg-university-front-door-agent-dev
  (✓) Done: Azure OpenAI: aoai-frontdoor-dev
  (✓) Done: Container Apps Environment: cae-frontdoor-dev
  (✓) Done: Container Registry: acrfrontdoordev
  ...

Deploying services (azd deploy)
  (✓) Done: Building container image
  (✓) Done: Pushing to registry
  (✓) Done: Deploying backend
  (✓) Done: Deploying frontend

SUCCESS: Your application was provisioned and deployed to Azure. 🎉
```

#### 5c: 🔗 Get Deployment URLs

```bash
# 📋 Show deployed service endpoints
azd show

# Output:
# Service           Endpoint
# backend           https://ca-backend-xxxx.azurecontainerapps.io
# frontend          https://xxx.azurestaticapps.net
```

### 🔹 Step 6: Verify Deployment

#### 6a: 💚 Test the Health Endpoint

```bash
# 🔗 Get the backend URL
BACKEND_URL=$(azd env get-value AZURE_CONTAINERAPP_URL)

# 💚 Test health endpoint
curl $BACKEND_URL/api/health
```

#### 6b: 💬 Test the Chat Endpoint

```bash
# 💬 Test the chat endpoint
curl -X POST $BACKEND_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": null}'
```

### 🔹 Step 7: View Logs and Monitoring

#### 7a: 📋 View Container Logs

```bash
# 📋 Stream logs from backend container
az containerapp logs show \
  --name ca-backend \
  --resource-group rg-university-front-door-agent-dev \
  --follow
```

#### 7b: 📊 Access Log Analytics

1. 🌐 Navigate to Azure Portal
2. 🔍 Find your Log Analytics workspace
3. 📝 Run queries to analyze your application

### 🔹 Step 8: Clean Up (When Done)

When you're finished with the lab, clean up Azure resources to avoid charges:

```bash
# 🗑️ Delete all resources created by azd
azd down

# ⚠️ Confirm deletion when prompted
# This removes ALL resources in the resource group
```

---

## ✅ Deliverables

By the end of this lab, you should have:

| 📋 Deliverable | ✅ Success Criteria |
|-------------|------------------|
| 🐳 Local Docker Test | Application runs successfully with `docker compose up` |
| 📄 azd Configuration | `azure.yaml` properly configured for your services |
| ☁️ Azure Deployment | Application deployed with `azd up` |
| 💚 Health Check | `/api/health` endpoint returns healthy status |
| 📊 Monitoring Access | Able to view container logs in Azure |

---

## 🔧 Troubleshooting Tips

### ⚡ Quick Fixes (Under 2 Minutes)

| ❌ Error | ✅ Quick Fix |
|-------|-----------|
| `docker: command not found` | Start Docker Desktop application |
| `azd: command not found` | Restart terminal after installation |
| `UNAUTHORIZED` during push | Run `azd auth login` again |
| Container exits immediately | Check logs: `docker compose logs backend` |
| Port already in use | Stop other containers: `docker compose down` |

### ⚠️ Common Issues

**Issue:** Docker build fails with "no such file or directory"
- ✅ **Solution:** Ensure you're running commands from the project root
- ✅ **Solution:** Verify all file paths in Dockerfile are correct
- ✅ **Solution:** Check that requirements.txt exists in the backend directory

**Issue:** `azd up` fails with authentication error
- ✅ **Solution:** Run `azd auth login` again
- ✅ **Solution:** Verify your Azure subscription is active
- ✅ **Solution:** Check that you have Contributor access to the subscription

**Issue:** Container fails to start in Azure
- ✅ **Solution:** Check container logs: `az containerapp logs show`
- ✅ **Solution:** Verify environment variables are set correctly
- ✅ **Solution:** Ensure the health check endpoint returns 200

### 📋 Debugging Checklist

1. [ ] 🐳 Docker Desktop is running
2. [ ] 🔨 `docker compose build` completes without errors
3. [ ] 🚀 `docker compose up` shows healthy containers
4. [ ] 💚 Health endpoint returns 200 locally
5. [ ] 🔐 `azd auth login` successful
6. [ ] ☁️ `azd up` completes without errors
7. [ ] 💚 Azure health endpoint returns 200
8. [ ] 📋 Container logs show no errors

---

## 📚 Additional Resources

- 📖 [Azure Developer CLI Overview](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview)
- 📦 [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- 🐳 [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- 🏗️ [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- 📊 [Azure Monitor Container Insights](https://learn.microsoft.com/azure/azure-monitor/containers/container-insights-overview)

---

## 🎉 Summary

In this lab, you learned how to:

1. 🐳 **Test locally with Docker Compose** - Verify your application works in containers
2. 📄 **Configure azure.yaml** - Define your application structure for azd
3. 🚀 **Deploy with azd up** - Provision infrastructure and deploy in one command
4. ✅ **Verify deployment** - Test health checks and endpoints in Azure
5. 📊 **Monitor your application** - View logs and set up alerts

Your AI support agent is now running in production on Azure Container Apps, ready to handle user requests at scale. 🎉

---

## 🏆 Congratulations!

You have successfully deployed your AI agent to Azure. Your agent pipeline from Labs 04 and 05 is now:
- 🐳 Containerized and portable
- ☁️ Running in Azure Container Apps
- 💚 Monitored with health checks
- 🌐 Accessible via public endpoints

This completes the deployment phase of the hackathon. You now have a fully functional AI support agent running in the cloud.

---

## 📊 Version Matrix

| Component | Required Version | Tested Version |
|-----------|-----------------|----------------|
| 🐳 Docker | 20.10+ | 24.0.7 |
| 📦 Docker Compose | 2.0+ | 2.23.0 |
| ☁️ azd | 1.5+ | 1.7.0 |
| 🔧 Azure CLI | 2.50+ | 2.56.0 |
| 🏗️ Bicep | 0.22+ | 0.24.24 |

---

<div align="center">

[← Lab 05](../05-agent-orchestration/README.md) | **Lab 06** | [Lab 07 →](../07-mcp-server/README.md)

📅 Last Updated: 2026-02-04 | 📝 Version: 1.0.0

</div>
