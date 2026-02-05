"""
Lab 04 - Build RAG Pipeline
SearchTool: Hybrid search over Azure AI Search

This module provides a SearchTool class that performs hybrid search
(combining keyword and vector search) against an Azure AI Search index.

Key Concepts:
- Vector search: Uses embeddings to find semantically similar content
- Keyword search: Traditional BM25-based text matching
- Hybrid search: Combines both approaches using Reciprocal Rank Fusion (RRF)

Azure SDK Documentation:
- SearchClient: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.searchclient
- VectorizedQuery: https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.models.vectorizedquery
"""

from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery


class SearchTool:
    """
    A tool for performing hybrid search over Azure AI Search.

    Hybrid search combines traditional keyword-based search with
    vector similarity search for improved relevance.
    """

    def __init__(
        self,
        endpoint: str,
        index_name: str,
        credential: AzureKeyCredential,
    ) -> None:
        """
        Initialize the SearchTool.

        Args:
            endpoint: The Azure AI Search service endpoint URL.
            index_name: The name of the search index to query.
            credential: Azure credential for authentication.
        """
        # TODO 1: Store the endpoint, index_name, and credential as instance attributes
        # Purpose: These will be needed to create the search client and for debugging
        # Implementation:
        #   self.endpoint = endpoint
        #   self.index_name = index_name
        #   self.credential = credential

        # TODO 2: Create a SearchClient instance using the provided parameters
        # The SearchClient handles connection pooling and retries automatically.
        #
        # Implementation:
        #   self.client = SearchClient(
        #       endpoint=endpoint,
        #       index_name=index_name,
        #       credential=credential
        #   )
        #
        # Azure SDK Reference:
        # https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.searchclient
        pass

    async def search(
        self,
        query: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search combining keyword and vector search.

        Args:
            query: The text query for keyword search.
            query_vector: The embedding vector for vector search.
            top_k: Number of results to return (default: 5).

        Returns:
            A list of search results, each containing document content
            and metadata (id, title, chunk, score).
        """
        # TODO 3: Create a VectorizedQuery for vector search
        # The VectorizedQuery wraps your embedding vector and specifies which index
        # field to search against. The 'fields' parameter must match the vector
        # field name defined in your Azure AI Search index schema.
        #
        # Implementation:
        #   vector_query = VectorizedQuery(
        #       vector=query_vector,           # The embedding from your query
        #       k_nearest_neighbors=top_k,     # How many nearest neighbors to find
        #       fields="content_vector"        # Must match vector field in index schema
        #   )
        #
        # Azure SDK Reference:
        # https://learn.microsoft.com/en-us/python/api/azure-search-documents/azure.search.documents.models.vectorizedquery

        # TODO 4: Perform hybrid search using the SearchClient
        # Hybrid search combines BOTH keyword (BM25) and vector (semantic) search.
        # When you provide both search_text AND vector_queries, Azure AI Search
        # uses Reciprocal Rank Fusion (RRF) to combine the results.
        #
        # Implementation:
        #   results = self.client.search(
        #       search_text=query,             # Enables keyword/BM25 search
        #       vector_queries=[vector_query], # Enables vector/semantic search
        #       top=top_k,                     # Maximum results to return
        #       select=["id", "title", "chunk", "content"]  # Fields to retrieve
        #   )
        #
        # The 'select' parameter specifies which fields to include in results.
        # Only request fields you need to minimize response size.
        #
        # Azure SDK Reference:
        # https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview

        # TODO 5: Process search results into a list of dictionaries
        # Iterate over the search results and extract the fields you need.
        # The results object is an iterator of dict-like SearchResult objects.
        #
        # Implementation:
        #   search_results = []
        #   for result in results:
        #       search_results.append({
        #           "id": result.get("id"),
        #           "title": result.get("title"),
        #           "chunk": result.get("chunk"),
        #           "content": result.get("content"),
        #           "score": result.get("@search.score", 0.0)  # Note the @ prefix!
        #       })
        #
        # Important: The relevance score is stored in "@search.score" (with @ prefix)
        # because it's a computed field, not a stored document field.

        # TODO 6: Return the list of processed results
        # Return the search_results list you built in the previous step
        return []
