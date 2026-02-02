# Lab 00 - Environment Setup

**Duration:** 30 minutes

## Learning Objectives

By the end of this lab, you will be able to:

- Verify all prerequisites are installed and properly configured
- Configure Azure credentials for the hackathon environment
- Test GitHub Copilot Agent Mode functionality
- Confirm your development environment is ready for the remaining labs

## Prerequisites

Before starting this lab, ensure you have the following installed:

| Tool | Version | Verification Command |
|------|---------|---------------------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| VS Code | Latest | `code --version` |
| GitHub Copilot | Extension installed | Check VS Code Extensions |
| Azure CLI | Latest | `az --version` |
| Docker | Latest | `docker --version` |

## Step-by-Step Instructions

### Step 1: Clone the Repository

If you haven't already cloned the repository, do so now:

```bash
git clone https://github.com/your-org/47doors.git
cd 47doors
```

### Step 2: Configure Environment Variables

Copy the environment template and configure your credentials:

```bash
cp .env.template .env
```

Open `.env` in your editor and configure the following variables:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key
AZURE_SEARCH_INDEX_NAME=your-index-name

# Additional settings as needed
```

> **Note:** Your instructor will provide the Azure credentials for the hackathon environment.

### Step 3: Install Python Dependencies

Create a virtual environment and install the Python dependencies:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Install Node.js Dependencies

Navigate to the frontend directory and install Node.js dependencies:

```bash
cd frontend/
npm install
cd ..
```

### Step 5: Verify Environment Setup

Run the environment verification script to check your setup:

```bash
python verify_environment.py
```

The script will check:
- Python version compatibility
- Required Python packages
- Node.js version compatibility
- Azure CLI authentication
- Environment variable configuration
- Docker availability

All checks should pass with green checkmarks. If any checks fail, refer to the Troubleshooting section below.

### Step 6: Start the Backend and Test Health Endpoint

Start the FastAPI backend server:

```bash
cd backend/
uvicorn app.main:app --reload
```

In a new terminal, test the health endpoint:

```bash
curl http://localhost:8000/api/health
```

Or open in your browser: [http://localhost:8000/api/health](http://localhost:8000/api/health)

You should see a response similar to:

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Deliverables Checklist

Before moving to the next lab, confirm the following:

- [ ] All prerequisites are installed with correct versions
- [ ] `.env` file is configured with Azure credentials
- [ ] Python virtual environment is created and activated
- [ ] Python dependencies installed successfully (`pip install -r requirements.txt`)
- [ ] Node.js dependencies installed successfully (`npm install`)
- [ ] `verify_environment.py` passes all checks
- [ ] Backend server starts without errors
- [ ] `/api/health` endpoint returns a successful response
- [ ] VS Code with GitHub Copilot extension is ready

## Troubleshooting

### Python Version Issues

**Problem:** `python --version` shows version < 3.11

**Solution:** Install Python 3.11+ from [python.org](https://www.python.org/downloads/) or use a version manager like `pyenv`.

```bash
# Using pyenv
pyenv install 3.11.0
pyenv local 3.11.0
```

### Node.js Version Issues

**Problem:** `node --version` shows version < 18

**Solution:** Install Node.js 18+ from [nodejs.org](https://nodejs.org/) or use a version manager like `nvm`.

```bash
# Using nvm
nvm install 18
nvm use 18
```

### Azure CLI Authentication

**Problem:** `az account show` returns an authentication error

**Solution:** Log in to Azure CLI:

```bash
az login
```

Follow the browser prompts to authenticate.

### Missing Environment Variables

**Problem:** `verify_environment.py` reports missing environment variables

**Solution:** Ensure your `.env` file contains all required variables. Double-check that you copied from `.env.template` and filled in all values.

### Docker Not Running

**Problem:** `docker --version` works but containers won't start

**Solution:** Ensure Docker Desktop is running:
- On Windows/macOS: Start Docker Desktop application
- On Linux: Run `sudo systemctl start docker`

### Port Already in Use

**Problem:** Backend fails to start with "Address already in use" error

**Solution:** Kill the process using port 8000:

```bash
# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### pip Install Fails

**Problem:** `pip install -r requirements.txt` fails with dependency errors

**Solution:** Try upgrading pip first:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### GitHub Copilot Not Working

**Problem:** Copilot suggestions don't appear in VS Code

**Solution:**
1. Ensure you're signed in to GitHub in VS Code
2. Check that your GitHub account has an active Copilot subscription
3. Restart VS Code
4. Check the Copilot icon in the status bar for any errors

## Next Steps

Once all checklist items are complete, proceed to:

**[Lab 01 - Understanding Agents](../01-understanding-agents/README.md)**

---

**Need help?** Raise your hand or ask in the hackathon chat channel.
