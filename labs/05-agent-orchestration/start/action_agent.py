"""
Action Agent Module

This agent is responsible for executing actions based on routing decisions,
including searching knowledge bases, creating tickets, and formatting responses.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from router_agent import RoutingDecision


class ActionType(Enum):
    """Types of actions the agent can execute."""
    SEARCH_KB = "search_kb"
    CREATE_TICKET = "create_ticket"
    SEND_NOTIFICATION = "send_notification"
    ESCALATE = "escalate"
    RESPOND = "respond"


@dataclass
class Citation:
    """Represents a citation from a knowledge base article."""
    source_id: str
    title: str
    content_snippet: str
    relevance_score: float
    url: str | None


@dataclass
class ActionResponse:
    """Structured response from action execution."""
    routing_decision: RoutingDecision
    response_text: str
    citations: list[Citation]
    actions_taken: list[ActionType]
    ticket_id: str | None
    follow_up_required: bool
    metadata: dict[str, Any]


class ActionAgent:
    """
    Agent responsible for executing actions and generating responses.

    This agent takes routing decisions and executes the appropriate actions,
    such as searching knowledge bases, creating support tickets, and
    generating user-facing responses with proper citations.

    Attributes:
        client: The Azure OpenAI client for LLM calls.
        search_client: The Azure AI Search client for KB queries.
        model: The model deployment name to use.
        index_name: The search index name for knowledge base.
    """

    def __init__(
        self,
        client: Any,
        search_client: Any,
        model: str = "gpt-4o",
        index_name: str = "knowledge-base"
    ) -> None:
        """
        Initialize the ActionAgent.

        Args:
            client: Azure OpenAI client instance.
            search_client: Azure AI Search client instance.
            model: The model deployment name to use.
            index_name: The search index name for knowledge base queries.
        """
        self.client = client
        self.search_client = search_client
        self.model = model
        self.index_name = index_name

    async def execute(self, routing_decision: RoutingDecision) -> ActionResponse:
        """
        Execute actions based on the routing decision.

        This method processes the routing decision and:
        1. Searches the knowledge base for relevant information
        2. Creates support tickets if required
        3. Generates a response with proper citations
        4. Handles escalation if flagged

        Args:
            routing_decision: The routing decision from RouterAgent.

        Returns:
            ActionResponse with response text, citations, and actions taken.

        Raises:
            ValueError: If routing_decision is invalid.
        """
        if routing_decision is None:
            raise ValueError("Routing decision cannot be None")

        actions_taken: list[ActionType] = []
        citations: list[Citation] = []
        ticket_id: str | None = None

        # TODO 1: Search knowledge base for relevant articles
        #
        # Use the _search_knowledge_base() helper method:
        #
        # search_query = routing_decision.query_result.original_query
        # citations = await self._search_knowledge_base(
        #     query=search_query,
        #     top_k=5  # Return top 5 most relevant results
        # )
        # actions_taken.append(ActionType.SEARCH_KB)
        #
        # This uses Azure AI Search with hybrid search (vector + keyword)
        # to find relevant documents from your knowledge base.

        # TODO 2: Create support ticket if routing suggests it
        #
        # Check the suggested_actions from the routing decision:
        #
        # if "create_ticket" in routing_decision.suggested_actions:
        #     ticket_id = await self._create_support_ticket(routing_decision)
        #     actions_taken.append(ActionType.CREATE_TICKET)
        #
        # You might also create tickets for complaints or when the user
        # explicitly requests one.

        # TODO 3: Handle escalation if required
        #
        # Check the requires_escalation flag from the routing decision:
        #
        # if routing_decision.requires_escalation:
        #     # In production: send notification to support team
        #     # await self._send_escalation_notification(routing_decision)
        #     actions_taken.append(ActionType.ESCALATE)
        #
        # For the lab, you can log the escalation or return a special response.

        # TODO 4: Generate response using LLM with retrieved context
        #
        # Use the _generate_response() helper method:
        #
        # response_text = await self._generate_response(
        #     routing_decision=routing_decision,
        #     citations=citations
        # )
        # actions_taken.append(ActionType.RESPOND)
        #
        # The response should:
        # - Answer based on the retrieved KB content
        # - Include inline citation references [1], [2], etc.
        # - Acknowledge if information wasn't found
        # - Match the department's tone (technical, friendly, etc.)

        # TODO 5: Determine if follow-up is required
        #
        # follow_up_required = (
        #     len(citations) == 0  # No KB results found
        #     or routing_decision.requires_escalation
        #     or routing_decision.query_result.requires_clarification
        # )

        # TODO 6: Return ActionResponse with all information
        #
        # return ActionResponse(
        #     routing_decision=routing_decision,
        #     response_text=response_text,
        #     citations=citations,
        #     actions_taken=actions_taken,
        #     ticket_id=ticket_id,
        #     follow_up_required=follow_up_required,
        #     metadata={
        #         "search_results_count": len(citations),
        #         "escalated": routing_decision.requires_escalation,
        #     }
        # )

        # Placeholder return - replace with actual implementation
        return ActionResponse(
            routing_decision=routing_decision,
            response_text="",
            citations=citations,
            actions_taken=actions_taken,
            ticket_id=ticket_id,
            follow_up_required=False,
            metadata={}
        )

    async def _search_knowledge_base(self, query: str, top_k: int = 5) -> list[Citation]:
        """
        Search the knowledge base for relevant articles.

        This method integrates with Azure AI Search to perform hybrid search
        (combining vector similarity and keyword matching) for best results.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            List of Citation objects from search results.
        """
        # TODO: Implement knowledge base search using Azure AI Search
        #
        # 1. Create the search query using the SearchClient:
        #
        #    from azure.search.documents import SearchClient
        #    results = self.search_client.search(
        #        search_text=query,
        #        top=top_k,
        #        select=["id", "title", "content", "url"],
        #        # For hybrid search (if vector embeddings available):
        #        # vector_queries=[VectorizedQuery(
        #        #     vector=embedding,  # Get from embedding model
        #        #     k_nearest_neighbors=top_k,
        #        #     fields="content_vector"
        #        # )]
        #    )
        #
        # 2. Convert search results to Citation objects:
        #
        #    citations = []
        #    for i, result in enumerate(results, 1):
        #        # Filter low relevance results (score threshold)
        #        if result.get("@search.score", 0) < 0.5:
        #            continue
        #
        #        citations.append(Citation(
        #            source_id=str(i),
        #            title=result.get("title", f"Document {i}"),
        #            content_snippet=result.get("content", "")[:500],
        #            relevance_score=result.get("@search.score", 0.0),
        #            url=result.get("url"),
        #        ))
        #
        # 3. Return the citations list (may be empty if no good results)
        #
        # Hint: You can reuse the RetrieveAgent from Lab 04 if available

        raise NotImplementedError("Implement knowledge base search")

    async def _create_support_ticket(
        self,
        routing_decision: RoutingDecision
    ) -> str:
        """
        Create a support ticket based on the routing decision.

        In production, this would integrate with a ticketing system API
        (e.g., Zendesk, ServiceNow, Jira). For the lab, we generate a
        mock ticket ID.

        Args:
            routing_decision: The routing decision containing query details.

        Returns:
            The created ticket ID (e.g., "TKT-ABC12345").
        """
        # TODO: Implement ticket creation
        #
        # 1. Generate a unique ticket ID:
        #    import uuid
        #    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        #
        # 2. In production, call your ticketing system API:
        #    ticket_data = {
        #        "subject": routing_decision.query_result.original_query[:100],
        #        "description": routing_decision.query_result.original_query,
        #        "department": routing_decision.department.value,
        #        "priority": routing_decision.priority.value,
        #        "intent": routing_decision.query_result.intent.value,
        #        "entities": routing_decision.query_result.entities,
        #        "escalation_reason": routing_decision.escalation_reason,
        #    }
        #    # response = await ticketing_api.create_ticket(ticket_data)
        #    # ticket_id = response.ticket_id
        #
        # 3. Return the ticket ID
        #
        # For the lab, just generate and return a mock ID:
        #    return ticket_id

        raise NotImplementedError("Implement support ticket creation")

    async def _generate_response(
        self,
        routing_decision: RoutingDecision,
        citations: list[Citation]
    ) -> str:
        """
        Generate a user-facing response using LLM with RAG context.

        This is the core RAG response generation step. The LLM uses the
        retrieved citations to answer the user's query with grounded,
        verifiable information.

        Args:
            routing_decision: The routing decision with query context.
            citations: Retrieved citations from knowledge base.

        Returns:
            Formatted response text with inline citation references.
        """
        # TODO: Implement response generation with citations
        #
        # 1. Create a system prompt for RAG response:
        #
        #    system_prompt = """You are a helpful assistant answering questions
        #    based on a knowledge base.
        #
        #    IMPORTANT RULES:
        #    1. ONLY answer based on the provided context - do not make up information
        #    2. ALWAYS cite sources using [1], [2], [3], etc. corresponding to the
        #       context sections
        #    3. If the context doesn't contain enough information, say "I don't have
        #       enough information about that in my knowledge base"
        #    4. Be concise but thorough
        #    5. If multiple sources support a point, cite all of them
        #    """
        #
        # 2. Build the context from citations using _format_citations():
        #
        #    context = self._format_citations(citations)
        #    # This creates numbered sections like:
        #    # [1] Title 1
        #    # Content snippet 1
        #    # ---
        #    # [2] Title 2
        #    # Content snippet 2
        #
        # 3. Build the user message with context and query:
        #
        #    user_query = routing_decision.query_result.original_query
        #    user_message = f"Context:\n{context}\n\nQuestion: {user_query}"
        #
        # 4. Call Azure OpenAI to generate the response:
        #
        #    response = self.client.chat.completions.create(
        #        model=self.model,
        #        messages=[
        #            {"role": "system", "content": system_prompt},
        #            {"role": "user", "content": user_message}
        #        ],
        #        temperature=0.3,  # Lower temp for factual responses
        #        max_tokens=500,
        #    )
        #
        # 5. Return the generated response text:
        #    return response.choices[0].message.content

        raise NotImplementedError("Implement response generation")

    def _format_citations(self, citations: list[Citation]) -> str:
        """
        Format citations for inclusion in LLM prompt context.

        Creates a numbered list of citation content that the LLM can
        reference when generating its response.

        Args:
            citations: List of Citation objects to format.

        Returns:
            Formatted citation string with numbered sections.
        """
        # TODO: Implement citation formatting for the LLM context
        #
        # 1. Handle empty citations:
        #    if not citations:
        #        return "No relevant documents found in the knowledge base."
        #
        # 2. Build numbered sections for each citation:
        #
        #    parts = []
        #    for i, citation in enumerate(citations, 1):
        #        # Create a numbered section with title and content
        #        section = f"[{i}] **{citation.title}**\n{citation.content_snippet}"
        #
        #        # Optionally include URL if available
        #        if citation.url:
        #            section += f"\nSource: {citation.url}"
        #
        #        parts.append(section)
        #
        # 3. Join sections with separators:
        #    return "\n\n---\n\n".join(parts)
        #
        # Example output:
        # [1] **Password Reset Guide**
        # To reset your password, go to Settings > Security > Change Password...
        # Source: https://docs.example.com/password-reset
        #
        # ---
        #
        # [2] **Account Security FAQ**
        # If you've forgotten your password, you can request a reset link...
        # Source: https://docs.example.com/security-faq

        raise NotImplementedError("Implement citation formatting")
