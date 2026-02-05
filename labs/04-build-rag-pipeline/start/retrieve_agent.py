"""
Lab 04 - Build RAG Pipeline
RetrieveAgent: RAG agent that uses SearchTool to answer questions with citations

This module provides a RetrieveAgent class that implements a Retrieval-Augmented
Generation (RAG) pattern: search for relevant documents, build context, and
generate a response with citations.

RAG Pattern Benefits:
- Grounds LLM responses in actual documents (reduces hallucination)
- Provides traceable citations for verification
- Allows the LLM to answer questions about private/recent data

Azure SDK Documentation:
- AsyncAzureOpenAI: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints
- Embeddings API: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/embeddings
- Chat Completions: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/chatgpt
"""

from typing import Any

from openai import AsyncAzureOpenAI

from search_tool import SearchTool


class RetrieveAgent:
    """
    A RAG agent that retrieves relevant documents and generates
    responses with citations.

    The agent follows the RAG pattern:
    1. Search for relevant documents using hybrid search
    2. Build a context from the retrieved documents
    3. Generate a response using an LLM with the context
    4. Include citations to source documents
    """

    def __init__(
        self,
        search_tool: SearchTool,
        llm_client: AsyncAzureOpenAI,
        model_deployment: str = "gpt-4o",
    ) -> None:
        """
        Initialize the RetrieveAgent.

        Args:
            search_tool: A SearchTool instance for performing searches.
            llm_client: An AsyncAzureOpenAI client for generating responses.
            model_deployment: The name of the model deployment to use.
        """
        # TODO 1: Store the search_tool, llm_client, and model_deployment as instance attributes
        # Purpose: These will be used in the retrieve() method to perform search and generation
        #
        # Implementation:
        #   self.search_tool = search_tool
        #   self.llm_client = llm_client
        #   self.model_deployment = model_deployment
        pass

    async def _get_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        # TODO 2: Use the LLM client to generate an embedding for the text
        # Embeddings are dense vector representations that capture semantic meaning.
        # Similar concepts will have similar vectors (measured by cosine similarity).
        #
        # Implementation:
        #   response = await self.llm_client.embeddings.create(
        #       model="text-embedding-ada-002",  # or your embedding deployment name
        #       input=text
        #   )
        #
        # Note: For async clients, use 'await'. For sync clients, omit 'await'.
        # The model name should match your Azure OpenAI embedding deployment name.
        #
        # Azure SDK Reference:
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/embeddings

        # TODO 3: Extract and return the embedding vector from the response
        # The API returns a list of embeddings; we only sent one text, so take the first.
        # The embedding is a list of floats (typically 1536 dimensions for ada-002).
        #
        # Implementation:
        #   return response.data[0].embedding
        return []

    def _build_context(self, search_results: list[dict[str, Any]]) -> str:
        """
        Build a context string from search results for the LLM prompt.

        Args:
            search_results: List of search result dictionaries.

        Returns:
            A formatted string containing the retrieved context with source references.
        """
        # TODO 4: Build a context string from the search results
        # Each result should be numbered so the LLM can reference them in citations.
        # Include metadata (like source document) to help the model understand context.
        #
        # Format each result as:
        # [Source {index}] {title}
        # {content}
        #
        # Example output:
        # [Source 1] Introduction to RAG
        # RAG combines retrieval with generation...
        #
        # [Source 2] Vector Search Basics
        # Vector search uses embeddings to find similar...
        #
        # Implementation:
        #   if not search_results:
        #       return "No relevant context found."
        #
        #   context_parts = []
        #   for i, result in enumerate(search_results, start=1):
        #       title = result.get("title", "Unknown")
        #       content = result.get("content", "")
        #       context_parts.append(f"[Source {i}] {title}\n{content}")
        #
        #   return "\n\n".join(context_parts)

        # TODO 5: Return the formatted context string
        return ""

    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build the prompt for the LLM including the context and query.

        Args:
            query: The user's question.
            context: The retrieved context from search results.

        Returns:
            A formatted prompt string for the LLM.
        """
        # TODO 6: Create a prompt that instructs the LLM to:
        # 1. Answer the question based ONLY on the provided context
        # 2. Include citations using [Source N] format
        # 3. Say "I don't know" if the context doesn't contain the answer
        #
        # The structure is important:
        # - Context comes first so the model "sees" it before the question
        # - Clear separation between context and question
        # - Explicit instruction to use citations
        #
        # Implementation (using f-string with triple quotes):
        #   return f"""Use the following context to answer the question. Include citations
        #   using [Source N] format. If the context doesn't contain enough
        #   information to answer, say "I don't know based on the provided context."
        #
        #   Context:
        #   {context}
        #
        #   Question: {query}
        #
        #   Answer:"""
        #
        # Prompt Engineering Tips:
        # - Be explicit about using ONLY the provided context (prevents hallucination)
        # - Require citations for traceability
        # - Provide a fallback for when context is insufficient

        return ""

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Retrieve relevant documents and generate a response with citations.

        This is the main RAG pipeline method that orchestrates:
        1. Embedding the query
        2. Searching for relevant documents
        3. Building context from results
        4. Generating a response with the LLM

        Args:
            query: The user's question.
            top_k: Number of documents to retrieve (default: 5).

        Returns:
            A dictionary containing:
            - answer: The generated response with citations
            - sources: List of source documents used
            - query: The original query
        """
        # =======================================================================
        # RAG PIPELINE - Complete these steps in order
        # =======================================================================

        # TODO 7: Step 1 - Get the embedding for the query
        # Convert the user's question into a vector for semantic search.
        #
        # Implementation:
        #   query_vector = await self._get_embedding(query)

        # TODO 8: Step 2 - Search for relevant documents using hybrid search
        # Use both the text query (for keyword search) and the vector (for semantic search).
        #
        # Implementation:
        #   search_results = await self.search_tool.search(
        #       query=query,
        #       query_vector=query_vector,
        #       top_k=top_k
        #   )

        # TODO 9: Step 3 - Build context from search results
        # Format the search results into a string the LLM can use.
        #
        # Implementation:
        #   context = self._build_context(search_results)

        # TODO 10: Step 4 - Build the prompt with context and query
        # Combine the context and user question into a prompt.
        #
        # Implementation:
        #   prompt = self._build_prompt(query, context)

        # TODO 11: Step 5 - Generate response using the LLM
        # Send the prompt to Azure OpenAI and get a completion.
        # The system message defines the agent's behavior; the user message contains the prompt.
        # Temperature controls creativity (lower = more focused, higher = more creative).
        # For factual Q&A, 0.3-0.7 is typically a good range.
        #
        # Implementation:
        #   response = await self.llm_client.chat.completions.create(
        #       model=self.model_deployment,
        #       messages=[
        #           {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
        #           {"role": "user", "content": prompt}
        #       ],
        #       temperature=0.7
        #   )
        #
        # Azure SDK Reference:
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/chatgpt

        # TODO 12: Step 6 - Extract the answer from the LLM response
        # The response contains a list of choices; we typically use the first one.
        #
        # Implementation:
        #   answer = response.choices[0].message.content

        # TODO 13: Step 7 - Return the result dictionary with answer, sources, and query
        # Include all relevant information for the caller to use.
        #
        # Implementation:
        #   return {
        #       "answer": answer,
        #       "sources": search_results,
        #       "query": query,
        #   }
        return {
            "answer": "",
            "sources": [],
            "query": query,
        }
