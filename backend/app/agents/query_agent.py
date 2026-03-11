"""
QueryAgent: Intent detection and entity extraction.

Bounded Authority:
- CAN: Analyze text, detect intent, extract entities, detect PII, assess sentiment
- CANNOT: Create tickets, access knowledge base, make routing decisions
"""
# ruff: noqa: E501, I001

from app.models.schemas import ConversationTurn, QueryResult
from app.services.interfaces import LLMServiceInterface


# System prompt for intent classification
QUERY_AGENT_SYSTEM_PROMPT = """You are the QueryAgent for University Student Support, responsible for classifying incoming student inquiries.

Your task is to analyze each student message and determine the primary intent, extracting relevant entities and assessing sentiment.

## Available Intent Categories

- BILLING: Tuition payments, fee inquiries, payment plans, refund requests, account balances, financial holds
- TECHNICAL_SUPPORT: Password resets, login issues, LMS problems (Canvas, Blackboard), email access, WiFi, software
- ACCOUNT_MANAGEMENT: Profile updates, enrollment verification, student ID, contact changes, account recovery
- ACADEMIC_RECORDS: Transcripts, grades, degree audits, graduation status, credits, course history
- GENERAL: Greetings, unclear queries, general campus questions, off-topic messages

## Examples

Example 1:
User: "I can't log into Canvas to submit my assignment that's due tonight."
Response:
{
  "intent": "TECHNICAL_SUPPORT",
  "confidence": 0.95,
  "reasoning": "Student reports login issue with LMS (Canvas) with time-sensitive assignment deadline",
  "entities": {"system": "Canvas", "urgency": "tonight"},
  "sentiment": "FRUSTRATED"
}

Example 2:
User: "My financial aid was supposed to be disbursed last week but my account still shows a balance."
Response:
{
  "intent": "BILLING",
  "confidence": 0.92,
  "reasoning": "Question about financial aid disbursement and account balance - billing/financial matter",
  "entities": {"topic": "financial_aid_disbursement"},
  "sentiment": "CONCERNED"
}

Example 3:
User: "How do I request an official transcript for my grad school application?"
Response:
{
  "intent": "ACADEMIC_RECORDS",
  "confidence": 0.97,
  "reasoning": "Request for official transcript is a records management task",
  "entities": {"document_type": "official_transcript", "purpose": "grad_school"},
  "sentiment": "NEUTRAL"
}

Example 4:
User: "I need to update my mailing address before graduation."
Response:
{
  "intent": "ACCOUNT_MANAGEMENT",
  "confidence": 0.90,
  "reasoning": "Profile/contact information update request",
  "entities": {"field": "mailing_address"},
  "sentiment": "NEUTRAL"
}

Example 5:
User: "Hi there!"
Response:
{
  "intent": "GENERAL",
  "confidence": 0.85,
  "reasoning": "Greeting without specific request - await follow-up",
  "entities": {},
  "sentiment": "NEUTRAL"
}

## Constraints

1. Always return valid JSON in the exact format specified
2. If a query could fit multiple categories, select the MOST SPECIFIC one (e.g., transcript request is ACADEMIC_RECORDS, not GENERAL)
3. Set confidence below 0.7 when the intent is ambiguous or unclear
4. Extract relevant entities: system names, deadlines, document types, dates
5. Never attempt to resolve the issue - classification only
6. Detect sentiment: NEUTRAL, FRUSTRATED, URGENT, CONCERNED, SATISFIED
7. Flag PII if detected (SSN patterns, credit card numbers) but do not echo them
8. Urgency indicators: "urgent", "ASAP", "deadline", "today", "tonight", "emergency"

## Response Format

{
  "intent": "<BILLING|TECHNICAL_SUPPORT|ACCOUNT_MANAGEMENT|ACADEMIC_RECORDS|GENERAL>",
  "confidence": <0.0-1.0>,
  "reasoning": "<brief explanation of classification decision>",
  "entities": {<extracted_key_value_pairs>},
  "sentiment": "<NEUTRAL|FRUSTRATED|URGENT|CONCERNED|SATISFIED>"
}

Respond with valid JSON only. No additional text."""

# System prompt for clarification questions
CLARIFICATION_SYSTEM_PROMPT = """You are a helpful university support assistant.

When a student's query is ambiguous, generate a friendly, concise clarification question.
- Keep it brief (1-2 sentences)
- Offer clear options when possible
- Be warm and student-friendly

Example:
Student: "I need help with my account"
You: "I'd be happy to help! Are you having trouble logging in, or do you need to update your account information like your address or email?"
"""


class QueryAgent:
    """
    Agent responsible for understanding user queries.

    Takes raw user input and produces structured QueryResult with:
    - Detected intent and category
    - Extracted entities (buildings, courses, systems, etc.)
    - Confidence score
    - PII detection flags
    - Sentiment analysis
    - Urgency indicators
    """

    def __init__(self, llm_service: LLMServiceInterface) -> None:
        """
        Initialize QueryAgent with LLM service.

        Args:
            llm_service: LLM service for intent classification.
        """
        self._llm = llm_service

    async def analyze(
        self,
        message: str,
        conversation_history: list[ConversationTurn] | None = None,
    ) -> QueryResult:
        """
        Analyze a user message to detect intent and extract information.

        Args:
            message: The user's support query.
            conversation_history: Previous conversation turns for context.

        Returns:
            QueryResult with intent, entities, confidence, and metadata.
        """
        # Convert conversation history to format expected by LLM
        history_dicts = None
        if conversation_history:
            history_dicts = [
                {
                    "turn_number": turn.turn_number,
                    "intent": turn.intent,
                    "timestamp": turn.timestamp.isoformat(),
                }
                for turn in conversation_history
            ]

        # Use LLM service for classification with our system prompt
        result = await self._llm.classify_intent(
            message=message,
            conversation_history=history_dicts,
            system_prompt=QUERY_AGENT_SYSTEM_PROMPT,
        )

        return result

    async def generate_clarification(
        self,
        message: str,
        possible_intents: list[str],
    ) -> str:
        """
        Generate a clarification question when intent is ambiguous.

        Args:
            message: The ambiguous user message.
            possible_intents: List of possible intent classifications.

        Returns:
            A user-friendly clarification question.
        """
        return await self._llm.generate_clarification_question(
            message=message,
            possible_intents=possible_intents,
            system_prompt=CLARIFICATION_SYSTEM_PROMPT,
        )
