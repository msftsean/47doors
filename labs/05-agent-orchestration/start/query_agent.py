"""
Query Agent Module

This agent is responsible for analyzing incoming user queries,
classifying intent, and extracting relevant entities.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Intent(Enum):
    """Enumeration of possible query intents."""
    QUESTION = "question"
    COMPLAINT = "complaint"
    REQUEST = "request"
    FEEDBACK = "feedback"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Represents an extracted entity from the query."""
    name: str
    value: str
    entity_type: str
    confidence: float


@dataclass
class QueryResult:
    """Structured result from query analysis."""
    original_query: str
    intent: Intent
    entities: list[Entity]
    confidence: float
    metadata: dict[str, Any]


class QueryAgent:
    """
    Agent responsible for analyzing user queries.

    This agent classifies the intent of incoming queries and extracts
    relevant entities for downstream processing by other agents.

    Attributes:
        client: The Azure OpenAI client for LLM calls.
        model: The model deployment name to use.
    """

    def __init__(self, client: Any, model: str = "gpt-4o") -> None:
        """
        Initialize the QueryAgent.

        Args:
            client: Azure OpenAI client instance.
            model: The model deployment name to use for analysis.
        """
        self.client = client
        self.model = model

    async def analyze(self, query: str) -> QueryResult:
        """
        Analyze a user query to classify intent and extract entities.

        This method processes the incoming query using an LLM to:
        1. Classify the user's intent (question, complaint, request, etc.)
        2. Extract relevant entities (product names, dates, amounts, etc.)
        3. Calculate a confidence score for the classification

        Args:
            query: The raw user query string to analyze.

        Returns:
            QueryResult containing intent, entities, and confidence score.

        Raises:
            ValueError: If the query is empty or invalid.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # TODO 1: Create a system prompt (SYSTEM_PROMPT constant or inline string)
        #
        # The system prompt should instruct the LLM to:
        # - Classify the query into ONE of the Intent enum values:
        #   QUESTION, COMPLAINT, REQUEST, FEEDBACK, UNKNOWN
        # - Extract relevant entities such as:
        #   - ticket_id: Support ticket IDs (e.g., "TKT-12345")
        #   - user_name: If user identifies themselves
        #   - topic: Main subject of the query
        #   - urgency: low, medium, or high based on language
        # - Provide a confidence score (0.0 to 1.0) for the classification
        # - Determine if clarification is needed before proceeding
        #
        # Request JSON output in this exact format:
        # {
        #     "intent": "<intent value>",
        #     "confidence": <0.0 to 1.0>,
        #     "entities": { "entity_name": "entity_value", ... },
        #     "entity_confidences": { "entity_name": <0.0 to 1.0>, ... },
        #     "requires_clarification": <true or false>,
        #     "clarification_question": "<question if needed, null otherwise>"
        # }
        #
        # Hint: See the solution for a comprehensive system prompt example

        # TODO 2: Build user prompt with optional conversation context
        #
        # Use the _build_classification_prompt() helper method to construct
        # the user message. If conversation_context is provided, include it
        # to help with follow-up questions like "tell me more about that".
        #
        # user_prompt = self._build_classification_prompt(query)

        # TODO 3: Call Azure OpenAI chat completions API
        #
        # response = self.client.chat.completions.create(
        #     model=self.model,
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ],
        #     temperature=0.1,  # Low temperature for consistent classification
        #     response_format={"type": "json_object"},  # Request JSON output
        #     max_tokens=500,
        # )

        # TODO 4: Parse the JSON response and handle potential errors
        #
        # result_json = json.loads(response.choices[0].message.content)
        #
        # Use _parse_entities() helper to convert the entities dict into
        # Entity objects. Handle missing fields with sensible defaults.
        # Map the intent string to the Intent enum (default to UNKNOWN if invalid).

        # TODO 5: Return a QueryResult with all extracted information
        #
        # return QueryResult(
        #     original_query=query,
        #     intent=intent,  # Intent enum value
        #     entities=entities,  # List of Entity objects
        #     confidence=confidence,  # Float from LLM response
        #     metadata={"urgency": result_json.get("urgency", "low")}
        # )

        # Placeholder return - replace with actual implementation
        return QueryResult(
            original_query=query,
            intent=Intent.UNKNOWN,
            entities=[],
            confidence=0.0,
            metadata={}
        )

    def _build_classification_prompt(
        self,
        query: str,
        conversation_context: str | None = None
    ) -> str:
        """
        Build the prompt for intent classification.

        Args:
            query: The user query to classify.
            conversation_context: Optional summary of previous conversation
                                 (helps with follow-up questions like "tell me more").

        Returns:
            Formatted prompt string for the LLM.
        """
        # TODO: Create a detailed user prompt that includes:
        #
        # 1. Conversation context (if available):
        #    - Include previous conversation summary to help with follow-ups
        #    - Format as: "## Conversation Context\n{context}\n"
        #
        # 2. The current user message:
        #    - Clearly mark it: "## Current User Message\n{query}\n"
        #
        # 3. Analysis instruction:
        #    - "Analyze this message and respond with JSON."
        #
        # Example implementation:
        # parts = []
        # if conversation_context:
        #     parts.append(f"## Conversation Context\n{conversation_context}\n")
        # parts.append(f"## Current User Message\n{query}\n")
        # parts.append("Analyze this message and respond with JSON.")
        # return "\n".join(parts)

        raise NotImplementedError("Implement classification prompt building")

    def _parse_entities(
        self,
        entities_dict: dict[str, str],
        confidences_dict: dict[str, float] | None = None
    ) -> list[Entity]:
        """
        Parse entity data from LLM response into Entity objects.

        Args:
            entities_dict: Dictionary mapping entity names to their values
                          (e.g., {"ticket_id": "TKT-12345", "topic": "password"})
            confidences_dict: Optional dictionary mapping entity names to confidence
                             scores (e.g., {"ticket_id": 0.95, "topic": 0.8})

        Returns:
            List of Entity objects extracted from the response.
        """
        # TODO: Convert entity dictionaries into Entity objects
        #
        # 1. Define a type mapping for common entity names:
        #    type_mapping = {
        #        "ticket_id": "identifier",
        #        "user_name": "name",
        #        "date": "date",
        #        "topic": "topic",
        #        "urgency": "attribute",
        #    }
        #
        # 2. Iterate through entities_dict and create Entity objects:
        #    entities = []
        #    for name, value in entities_dict.items():
        #        if value is None:
        #            continue  # Skip null values
        #
        #        confidence = confidences_dict.get(name, 0.8) if confidences_dict else 0.8
        #        entity_type = type_mapping.get(name, "unknown")
        #
        #        entities.append(Entity(
        #            name=name,
        #            value=str(value),
        #            entity_type=entity_type,
        #            confidence=float(confidence),
        #        ))
        #
        # 3. Optionally filter out low-confidence entities (< 0.5)
        #
        # 4. Return the list of Entity objects

        raise NotImplementedError("Implement entity parsing")
