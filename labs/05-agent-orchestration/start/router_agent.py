"""
Router Agent Module

This agent is responsible for routing analyzed queries to the
appropriate department or action handler based on intent and entities.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from query_agent import QueryResult


class Department(Enum):
    """Enumeration of possible routing destinations."""
    SALES = "sales"
    SUPPORT = "support"
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


class Priority(Enum):
    """Priority levels for routed requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class RoutingDecision:
    """Structured routing decision for a query."""
    query_result: QueryResult
    department: Department
    priority: Priority
    requires_escalation: bool
    escalation_reason: str | None
    suggested_actions: list[str]
    metadata: dict[str, Any]


class RouterAgent:
    """
    Agent responsible for routing queries to appropriate departments.

    This agent analyzes the QueryResult from the QueryAgent and determines
    the best department, priority level, and any escalation requirements.

    Attributes:
        client: The Azure OpenAI client for LLM calls.
        model: The model deployment name to use.
        escalation_keywords: Keywords that trigger automatic escalation.
    """

    def __init__(
        self,
        client: Any,
        model: str = "gpt-4o",
        escalation_keywords: list[str] | None = None
    ) -> None:
        """
        Initialize the RouterAgent.

        Args:
            client: Azure OpenAI client instance.
            model: The model deployment name to use for routing decisions.
            escalation_keywords: List of keywords that trigger escalation.
        """
        self.client = client
        self.model = model
        self.escalation_keywords = escalation_keywords or [
            "urgent", "emergency", "lawsuit", "legal", "executive"
        ]

    async def route(self, query_result: QueryResult) -> RoutingDecision:
        """
        Route a query to the appropriate department.

        This method analyzes the QueryResult and determines:
        1. Which department should handle the query
        2. The priority level of the request
        3. Whether escalation to a human is required
        4. Suggested actions for the handling agent

        Args:
            query_result: The analyzed query from QueryAgent.

        Returns:
            RoutingDecision with department, priority, and actions.

        Raises:
            ValueError: If query_result is invalid.
        """
        if query_result is None:
            raise ValueError("Query result cannot be None")

        # TODO 1: Check for automatic escalation triggers FIRST
        #
        # Escalation triggers take precedence over normal routing because they
        # indicate situations requiring human attention. Use the helper method:
        #
        # escalation_result = self._check_escalation_triggers(query_result)
        # if escalation_result:
        #     return escalation_result
        #
        # Check for keywords like: "lawyer", "urgent", "emergency", "human",
        # "supervisor", "manager", "complaint", etc.
        # Safety keywords should get URGENT priority: "suicide", "harm", "hurt myself"
        # Legal keywords should get HIGH priority: "lawyer", "attorney", "legal"

        # TODO 2: Handle clarification requests from QueryAgent
        #
        # If the QueryAgent determined it needs more information, route to
        # the clarification agent:
        #
        # if query_result.requires_clarification:
        #     return RoutingDecision(
        #         query_result=query_result,
        #         department=Department.GENERAL,  # or create a CLARIFICATION department
        #         priority=Priority.MEDIUM,
        #         requires_escalation=False,
        #         escalation_reason=None,
        #         suggested_actions=["clarification_agent"],
        #         metadata={"clarification_question": query_result.clarification_question}
        #     )

        # TODO 3: Check confidence level - low confidence needs clarification
        #
        # Define a threshold (e.g., CONFIDENCE_THRESHOLD = 0.6)
        # If query_result.confidence < threshold, route to clarification:
        #
        # if query_result.confidence < 0.6:
        #     return RoutingDecision(
        #         query_result=query_result,
        #         department=Department.GENERAL,
        #         priority=Priority.MEDIUM,
        #         requires_escalation=False,
        #         escalation_reason=None,
        #         suggested_actions=["clarification_agent"],
        #         metadata={"reason": f"Low confidence ({query_result.confidence:.2f})"}
        #     )

        # TODO 4: Look up route in routing table based on intent
        #
        # Create a ROUTING_TABLE mapping Intent -> Department:
        # ROUTING_TABLE = {
        #     Intent.QUESTION: Department.SUPPORT,
        #     Intent.COMPLAINT: Department.SUPPORT,  # with higher priority
        #     Intent.REQUEST: Department.GENERAL,
        #     Intent.FEEDBACK: Department.GENERAL,
        #     Intent.UNKNOWN: Department.GENERAL,
        # }
        #
        # department = ROUTING_TABLE.get(query_result.intent, Department.GENERAL)

        # TODO 5: Determine priority using _determine_priority() helper
        #
        # priority = self._determine_priority(query_result, department)
        #
        # Consider: intent type (complaints = higher), urgency metadata,
        # customer history (if available)

        # TODO 6: Build suggested actions list based on department
        #
        # suggested_actions = []
        # if department == Department.SUPPORT:
        #     suggested_actions.append("search_kb")
        # if query_result.intent == Intent.COMPLAINT:
        #     suggested_actions.append("create_ticket")
        # etc.

        # TODO 7: Return RoutingDecision with all routing information
        #
        # return RoutingDecision(
        #     query_result=query_result,
        #     department=department,
        #     priority=priority,
        #     requires_escalation=False,
        #     escalation_reason=None,
        #     suggested_actions=suggested_actions,
        #     metadata={"reasoning": f"Intent '{query_result.intent.value}' with confidence {query_result.confidence:.2f}"}
        # )

        # Placeholder return - replace with actual implementation
        return RoutingDecision(
            query_result=query_result,
            department=Department.GENERAL,
            priority=Priority.MEDIUM,
            requires_escalation=False,
            escalation_reason=None,
            suggested_actions=[],
            metadata={}
        )

    def _check_escalation_triggers(self, query_result: QueryResult) -> RoutingDecision | None:
        """
        Check if the query requires automatic escalation.

        Escalation triggers indicate situations that require human intervention
        regardless of the classified intent. These include:
        - Legal concerns (lawyer, sue, attorney)
        - Safety concerns (suicide, harm, hurt myself)
        - Strong frustration (complaint, manager, supervisor)
        - Explicit human requests (human, real person)

        Args:
            query_result: The analyzed query to check.

        Returns:
            RoutingDecision for escalation if triggers found, None otherwise.
        """
        # TODO: Implement escalation trigger detection
        #
        # 1. Define escalation keywords list:
        #    ESCALATION_TRIGGERS = [
        #        # Legal
        #        "lawyer", "attorney", "legal", "sue", "lawsuit",
        #        # Safety (URGENT priority)
        #        "suicide", "harm", "hurt myself", "kill", "die",
        #        # Frustration
        #        "supervisor", "manager", "complaint", "incompetent",
        #        # Urgency
        #        "emergency", "urgent", "immediately", "right now",
        #        # Explicit requests
        #        "human", "real person", "speak to someone",
        #    ]
        #
        # 2. Convert query to lowercase for case-insensitive matching:
        #    query_lower = query_result.original_query.lower()
        #
        # 3. Find all triggered keywords:
        #    triggered = [kw for kw in ESCALATION_TRIGGERS if kw in query_lower]
        #
        # 4. If triggers found, determine priority:
        #    - Safety triggers -> Priority.URGENT
        #    - Legal triggers -> Priority.HIGH
        #    - Other triggers -> Priority.HIGH
        #
        # 5. Return RoutingDecision with:
        #    - department=Department.SUPPORT (or dedicated escalation dept)
        #    - requires_escalation=True
        #    - escalation_reason="Safety concern" or "Legal concern" etc.
        #    - suggested_actions=["escalation_agent"]
        #
        # 6. Return None if no triggers found

        raise NotImplementedError("Implement escalation trigger checking")

    def _determine_priority(
        self,
        query_result: QueryResult,
        department: Department
    ) -> Priority:
        """
        Determine the priority level for a routed query.

        Priority is derived from:
        1. Urgency metadata from QueryAgent (if extracted)
        2. Intent type (complaints typically higher priority)
        3. Specific entity values (e.g., "ASAP" in topic)

        Args:
            query_result: The analyzed query with metadata.
            department: The target department.

        Returns:
            Priority enum value.
        """
        # TODO: Implement priority determination logic
        #
        # 1. Check urgency from query metadata:
        #    urgency = query_result.metadata.get("urgency", "low")
        #
        # 2. Map urgency string to Priority enum:
        #    urgency_to_priority = {
        #        "high": Priority.HIGH,
        #        "medium": Priority.MEDIUM,
        #        "low": Priority.LOW,
        #    }
        #    priority = urgency_to_priority.get(urgency, Priority.MEDIUM)
        #
        # 3. Override based on intent type:
        #    - COMPLAINT intent -> at least Priority.MEDIUM
        #    - ESCALATION intent -> Priority.HIGH
        #
        # 4. Check for urgency keywords in original query:
        #    if any(kw in query_result.original_query.lower()
        #           for kw in ["urgent", "asap", "immediately"]):
        #        priority = Priority.HIGH
        #
        # 5. Return the determined priority

        raise NotImplementedError("Implement priority determination")

    def _build_routing_prompt(self, query_result: QueryResult) -> str:
        """
        Build the prompt for routing decision (optional LLM-based routing).

        Note: The solution uses rule-based routing via a static ROUTING_TABLE
        for most cases. This method is provided for complex routing scenarios
        that require LLM reasoning.

        Args:
            query_result: The query to route.

        Returns:
            Formatted prompt string for the LLM.
        """
        # TODO: Create a detailed prompt for LLM-based routing (OPTIONAL)
        #
        # For simple intent-to-department mapping, use a static routing table
        # instead of LLM calls (faster and more predictable).
        #
        # If you need LLM-based routing for complex cases:
        #
        # 1. Describe each department's responsibilities:
        #    departments_desc = """
        #    - SALES: Product inquiries, pricing, purchasing
        #    - SUPPORT: Technical issues, how-to questions, troubleshooting
        #    - BILLING: Payment issues, refunds, invoices
        #    - TECHNICAL: Complex technical problems, escalations
        #    - GENERAL: General inquiries, greetings, unclear requests
        #    """
        #
        # 2. Include query context:
        #    query_context = f"""
        #    Intent: {query_result.intent.value}
        #    Confidence: {query_result.confidence}
        #    Entities: {query_result.entities}
        #    Original Query: {query_result.original_query}
        #    """
        #
        # 3. Request structured output:
        #    output_format = """
        #    Respond with JSON:
        #    {
        #        "department": "<department name>",
        #        "priority": "<low|medium|high|urgent>",
        #        "reasoning": "<why this routing>",
        #        "suggested_actions": ["action1", "action2"]
        #    }
        #    """
        #
        # 4. Combine into full prompt

        raise NotImplementedError("Implement routing prompt building")
