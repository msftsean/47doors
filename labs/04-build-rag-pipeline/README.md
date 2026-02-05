# 🔍 Lab 04 - Build RAG Pipeline

| 📋 Attribute | Value |
|-------------|-------|
| ⏱️ **Duration** | 120 minutes (2 hours) |
| 📊 **Difficulty** | ⭐⭐⭐ Advanced |
| 🎯 **Prerequisites** | Labs 01 and 02 completed |

---

> 📢 **HACKATHON NOTE:** The Azure AI Search index `university-kb` has been **pre-populated** with 32 KB articles and embeddings. **Skip Steps 2 and 3** and proceed directly to **Step 4: Implement the Search Tool**.
>
> 🧪 **Verify your setup first:**
> ```bash
> cd labs/04-build-rag-pipeline
> python verify_index.py
> ```

---

## 📈 Progress Tracker

```
Lab Progress: [░░░░░░░░░░] 0% - Not Started

Checkpoints:
□ Step 1: Understand Your Knowledge Base
□ Step 2: Create Azure AI Search Index (PRE-COMPLETED ✅)
□ Step 3: Generate Embeddings (PRE-COMPLETED ✅)
□ Step 4: Implement the Search Tool ← START HERE
□ Step 5: Build the RetrieveAgent
□ Step 6: Test Your RAG Pipeline
```

---

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

1. 🔧 **Set up Azure AI Search with hybrid search** - Configure an Azure AI Search index that supports both vector and keyword search for optimal retrieval
2. 🧠 **Create embeddings for KB articles** - Generate vector embeddings from knowledge base documents and index them for semantic search
3. 📚 **Build a RetrieveAgent with citations** - Implement an agent that retrieves relevant documents and includes proper citations in responses

---

## 🤔 What is RAG?

**Retrieval-Augmented Generation (RAG)** is a technique that enhances AI responses by retrieving relevant information from a knowledge base before generating answers. Instead of relying solely on the model's training data, RAG:

1. 🔍 **Retrieves** relevant documents from your knowledge base
2. ➕ **Augments** the prompt with this retrieved context
3. 💬 **Generates** a response grounded in your specific data

### 🌟 Why RAG Matters

| 🚫 Without RAG | ✅ With RAG |
|-------------|----------|
| Responses based only on training data | Responses grounded in your data |
| May hallucinate facts | Can cite specific sources |
| Outdated information | Access to current documents |
| Generic answers | Domain-specific answers |
| No source attribution | Clear citations and references |

### 🏗️ RAG Architecture

```
+------------------+       +------------------+       +------------------+
|   User Query     |       |   Embedding      |       |   Azure AI       |
|   "How do I      | ----> |   Model          | ----> |   Search         |
|    reset pwd?"   |       |   (Vectorize)    |       |   (Retrieve)     |
+------------------+       +------------------+       +------------------+
                                                              |
                                                              v
+------------------+       +------------------+       +------------------+
|   Response       |       |   LLM            |       |   Retrieved      |
|   with Citations | <---- |   (Generate)     | <---- |   Documents      |
+------------------+       +------------------+       +------------------+
```

---

## 🔀 What is Hybrid Search?

**Hybrid search** combines two search strategies to maximize retrieval quality:

### 🧠 Vector Search (Semantic)
- 🔢 Converts text to numerical vectors (embeddings)
- 🔍 Finds semantically similar content
- 📝 Handles synonyms and related concepts
- ✅ Great for: "What's the policy on working from home?" finding "Remote work guidelines"

### 📝 Keyword Search (Lexical)
- 🔤 Traditional text matching (BM25)
- 🎯 Exact term matching with relevance scoring
- 📌 Handles specific terminology and names
- ✅ Great for: Finding "Error code E-1234" or "Form W-2"

### 🤝 Why Hybrid?

| 🔍 Search Type | 💪 Strength | ⚠️ Weakness |
|-------------|----------|----------|
| Vector Only | Semantic understanding | May miss exact terms |
| Keyword Only | Exact matching | Misses related concepts |
| **🌟 Hybrid** | Best of both worlds | Slightly more complex |

Azure AI Search combines both approaches using **Reciprocal Rank Fusion (RRF)** to merge results from vector and keyword searches.

---

## 🏗️ Architecture Overview

In this lab, you will build the following components:

```
labs/04-build-rag-pipeline/
  📁 data/                    # Knowledge base articles (JSON)
  📁 start/
    📄 index_schema.json      # Azure AI Search index definition
    📄 indexer.py             # Script to index KB articles
    📄 retrieve_agent.py      # RetrieveAgent implementation (skeleton)
    📄 search_tool.py         # Search tool implementation (skeleton)
    📄 config.py              # Configuration settings
  📁 solution/
    📄 index_schema.json      # Complete index definition
    📄 indexer.py             # Complete indexer script
    📄 retrieve_agent.py      # Complete RetrieveAgent
    📄 search_tool.py         # Complete search tool
    📄 config.py              # Complete configuration
```

---

## 📝 Step-by-Step Instructions

### 🔹 Step 1: Understand Your Knowledge Base

The `data/` directory contains knowledge base articles in JSON format. Each article has:

```json
{
  "id": "kb-001",
  "title": "Password Reset Procedure",
  "content": "To reset your password, follow these steps...",
  "category": "Security",
  "lastUpdated": "2024-01-15",
  "tags": ["password", "security", "account"]
}
```

Before indexing, review the KB articles to understand:
- 📊 How many articles exist
- 🏷️ What categories and topics they cover
- 📏 The structure and length of content

```bash
# 📊 Count KB articles
ls data/*.json | wc -l

# 👀 Preview an article
cat data/kb-001.json | jq .
```

### 🔹 Step 2: Create the Azure AI Search Index

> ⏭️ **SKIP THIS STEP** - The index has been pre-created for the hackathon. Read this section for understanding only.

The search index defines how documents are stored and queried. Open `start/index_schema.json` and configure:

#### 📋 Fields Configuration

| 🏷️ Field | 📊 Type | 📝 Purpose |
|-------|------|---------|
| `id` | String (Key) | Unique document identifier |
| `title` | String (Searchable) | Article title for keyword search |
| `content` | String (Searchable) | Full article text |
| `contentVector` | Collection(Single) | Vector embedding for semantic search |
| `category` | String (Filterable) | For filtering by category |
| `tags` | Collection(String) | For filtering by tags |
| `lastUpdated` | DateTimeOffset | For sorting by recency |

#### 🧠 Vector Configuration

Configure the vector field for hybrid search:

```json
{
  "name": "contentVector",
  "type": "Collection(Edm.Single)",
  "dimensions": 1536,
  "vectorSearchProfile": "my-vector-profile"
}
```

#### 🎯 Semantic Configuration

Enable semantic ranking for improved relevance:

```json
{
  "semanticConfiguration": {
    "name": "my-semantic-config",
    "prioritizedFields": {
      "contentFields": [
        { "fieldName": "content" }
      ],
      "titleField": { "fieldName": "title" }
    }
  }
}
```

**Task:** ~~Complete the index schema in `start/index_schema.json`.~~ *(Pre-completed for hackathon)* ✅

### 🔹 Step 3: Generate Embeddings and Index Documents

> ⏭️ **SKIP THIS STEP** - All 32 KB articles have been pre-indexed with embeddings. Read this section for understanding only.

Open `start/indexer.py` and implement the indexing pipeline:

#### 3a: 📂 Load KB Articles

```python
def load_kb_articles(data_dir: str) -> list[dict]:
    """Load all KB articles from the data directory."""
    articles = []
    for file_path in Path(data_dir).glob("*.json"):
        with open(file_path) as f:
            articles.append(json.load(f))
    return articles
```

#### 3b: 🧠 Generate Embeddings

Use Azure OpenAI to create vector embeddings:

```python
async def generate_embedding(text: str, client: AzureOpenAI) -> list[float]:
    """Generate embedding vector for text using Azure OpenAI."""
    response = await client.embeddings.create(
        model="text-embedding-ada-002",  # or your deployed model
        input=text
    )
    return response.data[0].embedding
```

#### 3c: ⬆️ Upload to Index

Create and upload documents to Azure AI Search:

```python
async def index_documents(articles: list[dict], search_client: SearchClient):
    """Index KB articles with embeddings into Azure AI Search."""
    documents = []
    for article in articles:
        # Generate embedding for content
        embedding = await generate_embedding(article["content"], openai_client)

        documents.append({
            "id": article["id"],
            "title": article["title"],
            "content": article["content"],
            "contentVector": embedding,
            "category": article["category"],
            "tags": article.get("tags", []),
            "lastUpdated": article["lastUpdated"]
        })

    # Upload in batches
    result = await search_client.upload_documents(documents)
    print(f"Indexed {len(result)} documents")
```

**Task:** ~~Complete the indexer in `start/indexer.py` and run it to populate your index.~~ *(Pre-completed for hackathon)* ✅

```bash
# ⏭️ (SKIP) Run the indexer - already done
# python start/indexer.py --data-dir ./data

# ✅ Verify documents were indexed
python verify_index.py
```

### 🔹 Step 4: Implement the Search Tool

> ✅ **START HERE** - Begin the lab from this step!

Open `start/search_tool.py` and implement hybrid search:

#### 4a: 🧠 Vector Search Query

```python
from azure.search.documents.models import VectorizedQuery

def create_vector_query(query_embedding: list[float]) -> VectorizedQuery:
    """Create a vector query for semantic search."""
    return VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=5,
        fields="contentVector"
    )
```

#### 4b: 🔀 Hybrid Search Implementation

```python
async def hybrid_search(
    query: str,
    search_client: SearchClient,
    openai_client: AzureOpenAI,
    top_k: int = 5,
    filter_category: str = None
) -> list[dict]:
    """
    Perform hybrid search combining vector and keyword search.

    Args:
        query: User's search query
        search_client: Azure AI Search client
        openai_client: Azure OpenAI client for embeddings
        top_k: Number of results to return
        filter_category: Optional category filter

    Returns:
        List of search results with scores
    """
    # 🧠 Generate query embedding
    query_embedding = await generate_embedding(query, openai_client)

    # 🔍 Create vector query
    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_k,
        fields="contentVector"
    )

    # 🏷️ Build filter if category specified
    filter_expr = f"category eq '{filter_category}'" if filter_category else None

    # 🔀 Execute hybrid search
    results = search_client.search(
        search_text=query,  # Keyword search
        vector_queries=[vector_query],  # Vector search
        filter=filter_expr,
        select=["id", "title", "content", "category", "lastUpdated"],
        top=top_k
    )

    return [
        {
            "id": doc["id"],
            "title": doc["title"],
            "content": doc["content"],
            "category": doc["category"],
            "score": doc["@search.score"]
        }
        for doc in results
    ]
```

**Task:** Complete the search tool in `start/search_tool.py`. 📝

### 🔹 Step 5: Build the RetrieveAgent

Open `start/retrieve_agent.py` and implement the RAG agent:

#### 5a: 🏗️ Agent Structure

```python
class RetrieveAgent:
    """Agent that retrieves relevant KB articles and generates cited responses."""

    def __init__(
        self,
        search_client: SearchClient,
        openai_client: AzureOpenAI,
        model_deployment: str
    ):
        self.search_client = search_client
        self.openai_client = openai_client
        self.model_deployment = model_deployment

    async def answer(self, query: str) -> RetrieveResponse:
        """
        Answer a user query using RAG.

        1. 🔍 Search for relevant documents
        2. 📝 Build context with citations
        3. 💬 Generate response with source attribution
        """
        # Step 1: Retrieve relevant documents
        documents = await hybrid_search(
            query=query,
            search_client=self.search_client,
            openai_client=self.openai_client,
            top_k=5
        )

        # Step 2: Build context with numbered citations
        context = self._build_context(documents)

        # Step 3: Generate response
        response = await self._generate_response(query, context, documents)

        return response
```

#### 5b: 📚 Building Context with Citations

```python
def _build_context(self, documents: list[dict]) -> str:
    """Build context string with numbered citations."""
    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(
            f"[{i}] {doc['title']}\n{doc['content']}\n"
        )
    return "\n---\n".join(context_parts)
```

#### 5c: 💬 Generating Cited Responses

```python
async def _generate_response(
    self,
    query: str,
    context: str,
    documents: list[dict]
) -> RetrieveResponse:
    """Generate a response with proper citations."""

    system_prompt = """You are a helpful assistant that answers questions based on the provided knowledge base articles.

IMPORTANT RULES:
1. ✅ Only answer based on the provided context
2. 📝 Always cite your sources using [1], [2], etc.
3. 🚫 If the context doesn't contain relevant information, say so
4. ✂️ Be concise but complete
5. 📚 Include all relevant citations at the end of your response

Format your response as:
<answer with inline citations>

Sources:
[1] <title>
[2] <title>
..."""

    user_prompt = f"""Context:
{context}

Question: {query}

Please provide a helpful answer with citations."""

    response = await self.openai_client.chat.completions.create(
        model=self.model_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )

    return RetrieveResponse(
        answer=response.choices[0].message.content,
        sources=[
            {"id": doc["id"], "title": doc["title"]}
            for doc in documents
        ]
    )
```

**Task:** Complete the RetrieveAgent in `start/retrieve_agent.py`. 📝

### 🔹 Step 6: Test Your RAG Pipeline

Create a test script to verify your implementation:

```python
# test_rag.py
import asyncio
from retrieve_agent import RetrieveAgent

async def test_rag_pipeline():
    agent = RetrieveAgent(...)  # Initialize with your clients

    # 🧪 Test queries
    test_queries = [
        "How do I reset my password?",
        "What is the vacation policy?",
        "How do I submit an expense report?",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 50)

        response = await agent.answer(query)

        print(f"💬 Answer: {response.answer}")
        print(f"\n📚 Sources:")
        for source in response.sources:
            print(f"  - [{source['id']}] {source['title']}")

if __name__ == "__main__":
    asyncio.run(test_rag_pipeline())
```

Run your tests:

```bash
python test_rag.py
```

---

## ✅ Deliverables

By the end of this lab, you should have:

| 📋 Deliverable | ✅ Success Criteria |
|-------------|------------------|
| 🔍 Azure AI Search Index | ✅ Pre-configured (32 articles indexed) |
| 🧠 Indexed KB Articles | ✅ Pre-indexed with embeddings |
| 🔀 Hybrid Search Tool | Returns relevant results combining vector and keyword search |
| 📚 RetrieveAgent | Generates responses with proper citations |
| 🧪 Test Results | All test queries return relevant, cited responses |

---

## 🔧 Troubleshooting Tips

### ⚠️ Common Issues

**Issue:** Index creation fails with field configuration error
- ✅ **Solution:** Verify vector dimensions match your embedding model (1536 for text-embedding-ada-002)
- ✅ **Solution:** Ensure all required fields have correct types
- ✅ **Solution:** Check that vector search profile is properly configured

**Issue:** Embeddings generation is slow
- ✅ **Solution:** Process articles in batches rather than one at a time
- ✅ **Solution:** Use async/await for concurrent API calls
- ✅ **Solution:** Check Azure OpenAI rate limits and add retry logic

**Issue:** Search returns no results
- ✅ **Solution:** Verify documents were successfully indexed (`az search document search`)
- ✅ **Solution:** Check that query embedding is being generated correctly
- ✅ **Solution:** Ensure field names in query match index schema

**Issue:** Citations are missing or incorrect
- ✅ **Solution:** Verify document IDs are preserved through the pipeline
- ✅ **Solution:** Check that the system prompt clearly instructs citation format
- ✅ **Solution:** Ensure retrieved documents are passed to the generation step

**Issue:** Low relevance scores for obvious matches
- ✅ **Solution:** Enable semantic ranking in your index
- ✅ **Solution:** Review your embedding model choice
- ✅ **Solution:** Check if BM25 keyword scores are being properly combined

### 📋 Debugging Checklist

1. [ ] ☁️ Azure AI Search service is running and accessible
2. [ ] 🧠 Azure OpenAI embeddings endpoint is configured
3. [ ] 📄 Index schema is valid and created successfully
4. [ ] 📊 Documents are indexed (check document count)
5. [ ] 🔢 Embeddings have correct dimensions
6. [ ] 🔍 Hybrid search returns results for test queries
7. [ ] 📚 Citations appear in generated responses

### 🆘 Getting Help

- 📖 Review the solution files for reference implementations
- 📚 Check Azure AI Search documentation for field type requirements
- 🧠 Consult Azure OpenAI documentation for embedding models
- 👋 Reach out to your instructor or lab assistant

---

## 📚 Additional Resources

- 🔀 [Azure AI Search Hybrid Search](https://learn.microsoft.com/azure/search/hybrid-search-overview)
- 🧠 [Azure OpenAI Embeddings](https://learn.microsoft.com/azure/ai-services/openai/concepts/understand-embeddings)
- 📖 [RAG Pattern Best Practices](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-openai-e2e-chat)
- 🎯 [Semantic Ranking Configuration](https://learn.microsoft.com/azure/search/semantic-search-overview)

---

## ➡️ Next Steps

Once your RAG pipeline returns relevant, cited responses for all test queries, proceed to:

**[Lab 05 - Agent Orchestration](../05-agent-orchestration/README.md)** 🔄

In the next lab, you will learn how to orchestrate multiple agents including your RetrieveAgent in a cohesive system.

---

## 📊 Version Matrix

| Component | Required Version | Tested Version |
|-----------|-----------------|----------------|
| 🐍 Python | 3.11+ | 3.11.9 |
| 🧠 Azure OpenAI | GPT-4o | 2024-02-15-preview |
| 🔢 text-embedding-ada-002 | v2 | 1536 dimensions |
| 🔍 Azure AI Search | 2024-05-01-preview | Standard tier |
| 🔧 azure-search-documents | 11.4+ | 11.4.0 |

---

<div align="center">

[← Lab 03](../03-spec-driven-development/README.md) | **Lab 04** | [Lab 05 →](../05-agent-orchestration/README.md)

📅 Last Updated: 2026-02-04 | 📝 Version: 1.0.0

</div>
