# Lab 06 - Deploy with azd

**Duration:** 90 minutes
**Prerequisites:** Lab 05 completed

---

## Learning Objectives

By the end of this lab, you will be able to:

1. **Containerize your agent with Docker** - Package your application into Docker containers for consistent deployment
2. **Deploy with azd up** - Use Azure Developer CLI to provision infrastructure and deploy your application in a single command
3. **Configure monitoring and health checks** - Set up application health monitoring and view logs in Azure

---

## What is Azure Developer CLI (azd)?

**Azure Developer CLI (azd)** is a developer-centric command-line tool that accelerates the time it takes to get your application running in Azure. It provides:

### Key Benefits

| Feature | Description |
|---------|-------------|
| **Single Command Deployment** | `azd up` provisions infrastructure AND deploys your code |
| **Template-Based** | Uses `azure.yaml` to define your application structure |
| **Infrastructure as Code** | Integrates with Bicep/Terraform for repeatable infrastructure |
| **Environment Management** | Manage multiple environments (dev, staging, prod) |
| **CI/CD Pipeline Generation** | Auto-generate GitHub Actions or Azure DevOps pipelines |

### How azd Works

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

### The azure.yaml File

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
- What services make up your application
- What language/runtime each service uses
- How to host each service (Container Apps, Static Web Apps, etc.)
- Where to find infrastructure definitions

---

## Architecture Overview

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

### Azure Resources Created

| Resource | Purpose |
|----------|---------|
| **Container Apps Environment** | Hosts your containerized backend |
| **Azure Container Registry** | Stores your Docker images |
| **Static Web App** | Hosts your frontend |
| **Azure OpenAI** | LLM inference for your agent |
| **Azure AI Search** | Vector search for RAG |
| **Cosmos DB** | Session and conversation storage |
| **Log Analytics** | Monitoring and logging |

---

## Step-by-Step Instructions

### Step 1: Verify Docker Setup

Before deploying to Azure, ensure your application runs correctly in Docker locally.

#### 1a: Check Docker Installation

```bash
# Verify Docker is installed and running
docker --version
docker info

# Verify Docker Compose is available
docker compose version
```

If Docker is not installed, see [Docker Desktop installation guide](https://docs.docker.com/desktop/).

#### 1b: Review the Dockerfile

Your backend Dockerfile should look similar to:

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key elements:
- **Multi-stage builds** for smaller images (if needed)
- **Non-root user** for security
- **Health check** for container orchestration
- **Proper caching** of dependencies

#### 1c: Review docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - MOCK_MODE=true
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT:-}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY:-}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
```

**Task:** Review your docker-compose.yml and ensure all services are defined correctly.

### Step 2: Test Locally with Docker Compose

Build and run your containers locally before deploying to Azure.

#### 2a: Build the Containers

```bash
# Build all services
docker compose build

# Or build a specific service
docker compose build backend
```

Expected output:
```
[+] Building 45.2s (12/12) FINISHED
 => [backend] Building...
 => [frontend] Building...
```

#### 2b: Start the Services

```bash
# Start all services in detached mode
docker compose up -d

# Watch the logs
docker compose logs -f
```

#### 2c: Verify Services are Running

```bash
# Check container status
docker compose ps

# Expected output:
# NAME                    STATUS              PORTS
# 47doors-backend-1      Up (healthy)        0.0.0.0:8000->8000/tcp
# 47doors-frontend-1     Up                  0.0.0.0:3000->80/tcp
```

#### 2d: Test the Health Endpoint

```bash
# Test backend health
curl http://localhost:8000/api/health

# Expected response includes: {"status": "healthy", "timestamp": "...", "services": {...}}
```

#### 2e: Test the Application

Open your browser and navigate to:
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

**Task:** Complete Exercise 06a to verify your local Docker setup.

### Step 3: Install and Configure azd

#### 3a: Install Azure Developer CLI

```bash
# Windows (PowerShell)
winget install microsoft.azd

# macOS
brew tap azure/azd && brew install azd

# Linux
curl -fsSL https://aka.ms/install-azd.sh | bash
```

Verify installation:
```bash
azd version
# Expected: azd version 1.x.x
```

#### 3b: Authenticate with Azure

```bash
# Login to Azure
azd auth login

# This will open a browser for authentication
# After login, you'll see: Logged in to Azure.
```

#### 3c: Review azure.yaml

The `azure.yaml` file in your project root defines the application:

```yaml
name: university-front-door-agent
metadata:
  template: university-front-door-agent@0.0.1

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
  module: main

hooks:
  postdeploy:
    shell: sh
    run: |
      echo "Deployment complete!"
      echo "Backend URL: ${AZURE_CONTAINERAPP_URL}"
      echo "API Health: ${AZURE_CONTAINERAPP_URL}/api/health"
```

### Step 4: Initialize azd Environment

#### 4a: Initialize the Environment

```bash
# Initialize azd in your project
azd init

# If azure.yaml already exists, azd will use it
# Otherwise, it will guide you through setup
```

#### 4b: Create an Environment

```bash
# Create a new environment (e.g., dev, staging, prod)
azd env new dev

# Set environment-specific values
azd env set AZURE_LOCATION eastus
azd env set AZURE_SUBSCRIPTION_ID <your-subscription-id>
```

#### 4c: Review Environment Variables

```bash
# List all environment variables
azd env get-values

# Key variables to set:
# AZURE_LOCATION - Azure region for deployment
# AZURE_SUBSCRIPTION_ID - Your Azure subscription
# AZURE_OPENAI_DEPLOYMENT - GPT model deployment name
```

### Step 5: Deploy with azd up

#### 5a: Run azd up

The magic command that provisions AND deploys:

```bash
# Provision infrastructure and deploy application
azd up
```

This single command:
1. Creates all Azure resources defined in your Bicep templates
2. Builds your Docker containers
3. Pushes images to Azure Container Registry
4. Deploys containers to Azure Container Apps
5. Configures networking and environment variables

#### 5b: Monitor the Deployment

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

SUCCESS: Your application was provisioned and deployed to Azure.
```

#### 5c: Get Deployment URLs

```bash
# Show deployed service endpoints
azd show

# Output:
# Service           Endpoint
# backend           https://ca-backend-xxxx.azurecontainerapps.io
# frontend          https://xxx.azurestaticapps.net
```

**Task:** Complete Exercise 06b to deploy your application to Azure.

### Step 6: Verify Deployment

#### 6a: Test the Health Endpoint

```bash
# Get the backend URL
BACKEND_URL=$(azd env get-value AZURE_CONTAINERAPP_URL)

# Test health endpoint
curl $BACKEND_URL/api/health

# Expected response includes: {"status": "healthy", "timestamp": "...", "services": {...}}
```

#### 6b: Test the Chat Endpoint

```bash
# Test the chat endpoint
curl -X POST $BACKEND_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": null}'

# Expected: Agent response with session_id
```

#### 6c: Access the Frontend

```bash
# Get frontend URL
FRONTEND_URL=$(azd env get-value AZURE_STATICWEBAPP_URL)
echo "Open in browser: $FRONTEND_URL"
```

### Step 7: View Logs and Monitoring

#### 7a: View Container Logs

```bash
# Stream logs from backend container
az containerapp logs show \
  --name ca-backend \
  --resource-group rg-university-front-door-agent-dev \
  --follow
```

#### 7b: Access Log Analytics

1. Navigate to Azure Portal
2. Find your Log Analytics workspace
3. Run queries to analyze your application:

```kusto
// View recent container logs
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "ca-backend"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
| take 100

// View HTTP requests
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "ca-backend"
| where Log_s contains "HTTP"
| project TimeGenerated, Log_s
```

#### 7c: Set Up Alerts (Optional)

```bash
# Create an alert for health check failures
az monitor metrics alert create \
  --name "Backend Health Alert" \
  --resource-group rg-university-front-door-agent-dev \
  --scopes <container-app-resource-id> \
  --condition "avg HealthProbeSuccessRate < 90" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### Step 8: Clean Up (When Done)

When you're finished with the lab, clean up Azure resources to avoid charges:

```bash
# Delete all resources created by azd
azd down

# Confirm deletion when prompted
# This removes ALL resources in the resource group
```

---

## Deliverables

By the end of this lab, you should have:

| Deliverable | Success Criteria |
|-------------|------------------|
| Local Docker Test | Application runs successfully with `docker compose up` |
| azd Configuration | `azure.yaml` properly configured for your services |
| Azure Deployment | Application deployed with `azd up` |
| Health Check | `/api/health` endpoint returns healthy status |
| Monitoring Access | Able to view container logs in Azure |

---

## Troubleshooting Tips

### Quick Fixes (Under 2 Minutes)

| Error | Quick Fix |
|-------|-----------|
| `docker: command not found` | Start Docker Desktop application |
| `azd: command not found` | Restart terminal after installation |
| `UNAUTHORIZED` during push | Run `azd auth login` again |
| Container exits immediately | Check logs: `docker compose logs backend` |
| Port already in use | Stop other containers: `docker compose down` |

### Common Issues

**Issue:** Docker build fails with "no such file or directory"
- **Solution:** Ensure you're running commands from the project root
- **Solution:** Verify all file paths in Dockerfile are correct
- **Solution:** Check that requirements.txt exists in the backend directory

**Issue:** `azd up` fails with authentication error
- **Solution:** Run `azd auth login` again
- **Solution:** Verify your Azure subscription is active
- **Solution:** Check that you have Contributor access to the subscription

**Issue:** Container fails to start in Azure
- **Solution:** Check container logs: `az containerapp logs show`
- **Solution:** Verify environment variables are set correctly
- **Solution:** Ensure the health check endpoint returns 200

**Issue:** Health check fails with timeout
- **Solution:** Increase `start_period` in health check configuration
- **Solution:** Verify the application starts within the timeout period
- **Solution:** Check that port 8000 is exposed correctly

**Issue:** Frontend can't connect to backend
- **Solution:** Check CORS configuration in backend
- **Solution:** Verify the API URL environment variable
- **Solution:** Ensure backend container is healthy before frontend starts

### Azure-Specific Deployment Errors

**Issue:** "Quota exceeded" or "InsufficientQuota"
```
Error: The subscription has reached the limit of 'Standard_v2' vCPUs for region 'eastus'
```
- **Solution:** Try a different region: `azd env set AZURE_LOCATION westus3`
- **Solution:** Request quota increase in Azure Portal → Quotas
- **Solution:** Use a smaller container size in your Bicep template

**Issue:** "Azure OpenAI deployment not found"
```
Error: The deployment 'gpt-4o' does not exist in resource 'aoai-xxx'
```
- **Solution:** Verify model name matches: `azd env get-value AZURE_OPENAI_DEPLOYMENT_NAME`
- **Solution:** Check model availability in your region (GPT-4o not available everywhere)
- **Solution:** Deploy model manually in Azure Portal → Azure OpenAI Studio

**Issue:** "Container Registry access denied"
```
Error: Get https://xxx.azurecr.io/v2/: unauthorized
```
- **Solution:** Enable admin access on ACR: `az acr update --name <acr-name> --admin-enabled true`
- **Solution:** Verify managed identity is configured correctly
- **Solution:** Re-run `azd provision` to fix permissions

**Issue:** "Resource group already exists"
```
Error: Resource group 'rg-university-front-door-agent-dev' already exists
```
- **Solution:** Use the existing group: This is usually fine, continue
- **Solution:** Clean up first: `azd down` then `azd up`
- **Solution:** Use a new environment: `azd env new dev2`

**Issue:** "Bicep compilation failed"
```
Error: Unable to find module 'main.bicep'
```
- **Solution:** Verify infra path in azure.yaml points to correct directory
- **Solution:** Check that main.bicep exists and has no syntax errors
- **Solution:** Run `az bicep build --file infra/main.bicep` to see detailed errors

**Issue:** Container stuck in "Provisioning" state
- **Solution:** Wait 5-10 minutes - first deployment can be slow
- **Solution:** Check Activity Log in Azure Portal for actual errors
- **Solution:** Verify image was pushed: `az acr repository list --name <acr-name>`

### Networking and Connectivity Errors

**Issue:** "Connection refused" when testing Azure endpoint
```bash
curl: (7) Failed to connect to xxx.azurecontainerapps.io
```
- **Solution:** Container may still be starting - wait 2-3 minutes
- **Solution:** Check ingress is enabled: Container Apps → Ingress settings
- **Solution:** Verify external access is enabled (not internal-only)

**Issue:** CORS errors in browser console
```
Access to XMLHttpRequest has been blocked by CORS policy
```
- **Solution:** Add frontend URL to backend CORS allowed origins
- **Solution:** Verify `CORS_ORIGINS` environment variable is set in Container App
- **Solution:** Check backend logs for CORS configuration loading

### Debugging Checklist

1. [ ] Docker Desktop is running
2. [ ] `docker compose build` completes without errors
3. [ ] `docker compose up` shows healthy containers
4. [ ] Health endpoint returns 200 locally
5. [ ] `azd auth login` successful
6. [ ] `azd up` completes without errors
7. [ ] Azure health endpoint returns 200
8. [ ] Container logs show no errors

### Useful Commands

```bash
# Check azd environment
azd env list
azd env get-values

# View deployment status
azd show

# Redeploy after code changes
azd deploy

# Reprovision infrastructure
azd provision

# View resource group in Azure Portal
az group show --name rg-university-front-door-agent-dev --query "id" -o tsv
```

### Getting Help

- Review the [azd documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- Check [Container Apps documentation](https://learn.microsoft.com/azure/container-apps/)
- Consult [Docker documentation](https://docs.docker.com/)
- Reach out to your instructor or lab assistant

---

## Additional Resources

- [Azure Developer CLI Overview](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Monitor Container Insights](https://learn.microsoft.com/azure/azure-monitor/containers/container-insights-overview)

---

## Summary

In this lab, you learned how to:

1. **Test locally with Docker Compose** - Verify your application works in containers
2. **Configure azure.yaml** - Define your application structure for azd
3. **Deploy with azd up** - Provision infrastructure and deploy in one command
4. **Verify deployment** - Test health checks and endpoints in Azure
5. **Monitor your application** - View logs and set up alerts

Your AI support agent is now running in production on Azure Container Apps, ready to handle user requests at scale.

---

## Congratulations!

You have successfully deployed your AI agent to Azure. Your agent pipeline from Labs 04 and 05 is now:
- Containerized and portable
- Running in Azure Container Apps
- Monitored with health checks
- Accessible via public endpoints

This completes the deployment phase of the hackathon. You now have a fully functional AI support agent running in the cloud.
