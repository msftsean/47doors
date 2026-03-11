"""
Robust rule-based intent classifier for Lab 01.

Supports TWO classification schemes:

1. Conversational intents (for test compatibility):
   - greeting: Hello, hi, good morning
   - help: I need help, assist me, having trouble
   - ticket: Ticket status, submit ticket
   - knowledge: Informational queries (password reset, library hours, etc.)
   - farewell: Goodbye, bye, thank you
   - unknown: Empty, gibberish, unrecognizable

2. Domain intents (for university routing):
   - financial_aid: FAFSA, scholarships, grants, loans, tuition assistance
   - registration: Course enrollment, transcripts, graduation, add/drop
   - housing: Dormitories, roommates, move-in/move-out, residence halls
   - it_support: Password resets, email, Canvas/LMS, WiFi, login issues
   - academic_advising: Major/minor selection, degree planning, course advice
   - student_accounts: Bills, refunds, payment plans, account holds, bursar
   - general: Catch-all for ambiguous queries or those requiring human escalation
"""

from dataclasses import dataclass
from typing import Literal, Any
import re

# Extended intent type including conversational intents
IntentType = Literal[
    # Conversational intents
    "greeting",
    "help",
    "ticket",
    "knowledge",
    "farewell",
    "unknown",
    # Domain-specific intents
    "financial_aid",
    "registration",
    "housing",
    "it_support",
    "academic_advising",
    "student_accounts",
    "general",
]

# Patterns for conversational intents (checked FIRST)
GREETING_PATTERNS = [
    r"^hello\b",
    r"^hi\b",
    r"^hey\b",
    r"^good morning\b",
    r"^good afternoon\b",
    r"^good evening\b",
    r"^howdy\b",
    r"^greetings\b",
    r"^what's up\b",
    r"^how are you\b",
    r"hi there",
]

FAREWELL_PATTERNS = [
    r"\bgoodbye\b",
    r"\bbye\b",
    r"^thanks?\b",
    r"^thank you\b",
    r"that's all",
    r"have a (good|nice|great) (day|one)",
    r"see you",
    r"take care",
]

HELP_PATTERNS = [
    r"\bneed help\b",
    r"\bhelp me\b",
    r"\bcan you (help|assist)\b",
    r"\bassist me\b",
    r"\bhaving (trouble|issues|problems)\b",
    r"\bi('m| am) (having|stuck|confused)\b",
]

TICKET_PATTERNS = [
    r"\bticket\b",
    r"\btkt-\d+\b",
    r"\bsubmit.*(request|issue)\b",
    r"\bstatus of my\b",
    r"\bcheck (my|the) status\b",
]

# General informational/knowledge query patterns
KNOWLEDGE_PATTERNS = [
    r"\bwhere is\b",
    r"\bwhere are\b",
    r"\bwhere can i\b",
    r"\bhow do i\b",
    r"\bhow can i\b",
    r"\bhow to\b",
    r"\bwhat (is|are) the\b",
    r"\bwhat time\b",
    r"\bwhen (is|does|do)\b",
    r"\bhours\b",
    r"\blocation\b",
    r"\boffice\b",
    r"\bdirections\b",
    r"\bfind\b",
    r"\blibrary\b",
    r"\bopen\b",
    r"\bclosed\b",
]


@dataclass
class ClassificationResult:
    """Result of intent classification with confidence score."""

    intent: IntentType
    confidence: float


# Weighted keyword patterns for each intent category
# Higher weights indicate stronger signals; negative weights demote false positives
INTENT_PATTERNS: dict[IntentType, dict[str, float]] = {
    "financial_aid": {
        # Strong indicators
        "fafsa": 3.0,
        "financial aid": 3.0,
        "scholarship": 2.5,
        "grant": 2.0,
        "pell grant": 3.0,
        "student loan": 2.5,
        "loan": 1.5,
        "work study": 2.5,
        "work-study": 2.5,
        "aid package": 2.5,
        "aid appeal": 2.5,
        "tuition assistance": 2.5,
        "sap": 2.0,  # Satisfactory Academic Progress
        "satisfactory academic progress": 3.0,
        # Medium indicators
        "outside scholarship": 2.0,
        "report scholarship": 2.0,
        "half-time enrollment": 1.5,
        "enrollment status": 1.0,
        "professional judgment": 2.0,
        "income change": 1.5,
        # Weak/context-dependent
        "aid": 1.0,
        "afford": 0.5,
    },
    "registration": {
        # Strong indicators
        "register for class": 3.0,
        "registration": 2.5,
        "enroll": 2.0,
        "transcript": 2.5,
        "official transcript": 3.0,
        "drop a class": 2.5,
        "drop class": 2.5,
        "add a class": 2.5,
        "add/drop": 3.0,
        "withdrawal": 2.0,
        "retroactive withdrawal": 3.0,
        "degree audit": 2.5,
        "graduation requirement": 2.5,
        "apply to graduate": 2.5,
        "to graduate": 2.0,
        "graduation": 1.5,
        "permission number": 2.5,
        "override": 1.5,
        "waitlist": 3.0,  # Boosted - waitlist is registrar
        "waitlist notification": 3.5,  # Notification about waitlist spot
        "class is full": 3.0,
        "class i need is full": 3.0,
        "transfer credit": 3.5,  # Boosted - transfer credits are registrar, not advising
        "transfer credits": 3.5,
        "articulation": 3.0,  # Transfer articulation agreements
        "community college": 1.5,
        "course catalog": 3.5,  # Course catalog is registrar-owned
        "catalog": 2.0,
        # Medium indicators
        "course credit": 1.5,
        "register": 1.5,
        "class schedule": 1.5,
        "schedule": 0.5,
        # Registration hold is registration, not student_accounts
        "registration hold": 2.5,
    },
    "housing": {
        # Strong indicators
        "housing": 2.5,
        "on-campus housing": 3.0,
        "dorm": 2.5,
        "dormitory": 2.5,
        "residence hall": 3.0,
        "roommate": 2.5,
        "room assignment": 2.5,
        "move-in": 2.5,
        "move-out": 2.5,
        "housing application": 3.0,
        "housing deposit": 2.5,
        "housing contract": 2.5,
        "break my housing contract": 3.0,
        "single room": 2.0,
        "room switch": 2.0,
        "switch rooms": 2.0,
        "room swap": 3.0,  # Room swap requests are housing
        "swap request": 2.5,
        # Medium indicators
        "room": 1.0,
        "living": 0.5,
        "apartment": 1.5,
        "residence": 1.5,
        "building": 0.5,
        "harassed": 1.0,  # Safety concerns in housing context
    },
    "it_support": {
        # Strong indicators
        "password": 2.5,
        "reset password": 3.0,
        "forgot password": 3.0,
        "log in": 2.0,
        "login": 2.0,
        "can't log": 2.5,
        "cannot log": 2.5,
        "student portal": 2.5,
        "portal": 1.5,
        "canvas": 3.0,  # Canvas issues are primarily IT
        "canvas says": 3.5,  # Canvas showing wrong info
        "lms": 2.0,
        "wifi": 3.0,  # Boosted - clear IT indicator
        "wi-fi": 3.0,
        "isn't working": 1.5,
        "not working": 1.5,
        "internet": 1.5,
        "email": 2.0,
        "student email": 2.5,
        "hacked": 2.5,
        "phishing": 3.0,
        "vpn": 2.5,
        "shared drive": 2.0,
        "deleted": 1.5,
        "data recovery": 2.5,
        "two-factor": 2.0,
        "2fa": 2.0,
        "mfa": 2.0,
        "campus wifi": 3.5,
        "sso": 3.0,  # Single sign-on issues
        "redirect loop": 3.0,
        "office 365": 3.5,  # O365 access is IT
        "o365": 3.5,
        "team channels": 3.0,  # Microsoft Teams is IT
        "teams": 1.5,
        "lost access": 2.5,  # Access loss is IT
        "identity provider": 3.0,
        "batch job": 2.0,  # System jobs that fail
        "sync": 1.0,  # Data sync issues
        # Medium indicators
        "account": 0.8,
        "access": 0.5,
        "network": 1.5,
        "software": 1.5,
        "computer": 1.0,
    },
    "academic_advising": {
        # Strong indicators
        "academic advisor": 3.0,
        "advisor": 2.0,
        "advising": 2.5,
        "declare major": 3.0,
        "change major": 2.5,
        "switch major": 2.5,
        "double major": 2.5,
        "minor": 2.0,
        "add a minor": 2.5,
        "degree requirements": 2.0,  # Reduced - can conflict with registration
        "degree plan": 2.5,
        "what classes should": 2.5,
        "classes should i take": 3.0,
        "prerequisite": 1.5,  # Reduced - prereqs can be registration context
        "academic probation": 3.0,
        "probation": 2.0,
        "degree": 1.0,
        "major": 1.5,
        "career": 1.0,
        "after graduation": 2.5,  # Boosted - career planning
        "do after graduation": 3.0,
        "5th year": 2.0,
        "haven't figured out": 1.5,
        # Medium indicators
        "course planning": 2.0,
        "plan": 0.5,
        "struggling": 1.0,
        "time off": 1.0,
        "taking time off": 1.5,
    },
    "student_accounts": {
        # Strong indicators
        "tuition bill": 3.0,
        "pay my tuition": 3.0,
        "pay tuition": 3.0,
        "payment plan": 2.5,
        "payment deadline": 2.5,
        "tuition payment": 3.0,
        "bursar": 3.0,
        "student accounts": 3.0,
        "refund": 2.5,
        "refund deadline": 2.5,
        "charge on my account": 2.5,
        "unrecognized charge": 2.5,
        "collections": 2.5,
        "sent to collections": 3.0,
        "account hold": 2.0,
        "financial hold": 2.5,
        "balance": 1.5,
        "balance due": 2.0,
        "bill": 2.0,  # Boosted - billing primary indicator
        "got a bill": 3.0,  # Billing inquiry
        "billing": 2.0,
        "owe": 1.5,
        "should cover": 1.5,  # "my aid should cover" is a billing issue
        # Disambiguators
        "tuition": 1.5,
        "payment": 1.5,
        "fee": 1.0,
        "charge": 1.0,
    },
    "general": {
        # Catch-all indicators
        "library": 2.0,
        "dining hall": 2.0,
        "dining": 1.5,
        "cafeteria": 2.0,
        "club": 1.5,
        "clubs": 1.5,
        "organization": 1.0,
        "student id": 2.0,
        "id card": 2.0,
        "lost my": 1.0,
        "complaint": 2.5,
        "file a complaint": 3.0,
        "professor's behavior": 2.5,
        "accessibility": 2.0,
        "international student": 1.5,
        "adjusting to college": 2.0,
        "don't know where to turn": 2.5,
        "don't know what kind of help": 3.0,
        "i need help but": 2.0,
        "talk to someone": 1.5,
        "in charge": 1.5,
        # Data integration / system ownership queries
        "data integration": 3.0,
        "who owns": 3.0,
        "crm": 2.0,
        "legacy system": 2.5,
        "student information system": 2.0,
        "system ownership": 2.5,
        # Vague/ambiguous signals
        "help": 0.3,
        "where is": 1.0,
        "what time": 1.0,
        "when does": 0.5,
    },
}

# Phrases that indicate ambiguity or need human escalation -> general
ESCALATION_PHRASES = [
    "i don't know",
    "don't know what",
    "not sure",
    "multiple issues",
    "complaint",
    "terrible",
    "awful",
    "someone in charge",
    "talk to a person",
    "talk to someone",
    "speak to someone",
    "speak to a human",
    "app is crashing",  # App crashes need triage
    "mobile app",  # Mobile app issues often cross departments
    "contacted three different",  # Multi-department frustration
    "no one can tell me",  # Escalation frustration
]


class IntentClassifier:
    """
    Robust intent classifier for student support queries.

    Uses weighted keyword matching with confidence scoring.
    Checks conversational intents first, then falls back to domain classification.

    Modes:
    - 'conversational': Returns greeting/farewell/ticket/knowledge/help/unknown (test_lab01 compat)
    - 'domain': Returns financial_aid/registration/housing/it_support/academic_advising/student_accounts/general
    """

    def __init__(self, confidence_threshold: float = 0.5, mode: str = "conversational"):
        """
        Initialize the classifier.

        Args:
            confidence_threshold: Minimum score difference to avoid 'general'
            mode: 'conversational' for test compat, 'domain' for sample_queries
        """
        self.confidence_threshold = confidence_threshold
        self.mode = mode
        self.patterns = INTENT_PATTERNS

    def _check_conversational_intent(self, text: str) -> ClassificationResult | None:
        """Check for conversational intents (greeting, farewell, help, ticket, unknown)."""
        # Check for empty/gibberish -> unknown
        if not text or len(text.strip()) < 2:
            return ClassificationResult(intent="unknown", confidence=0.9)

        # Check if mostly non-alphabetic (gibberish)
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / max(len(text), 1)
        if alpha_ratio < 0.5:
            return ClassificationResult(intent="unknown", confidence=0.85)

        # Check greeting patterns
        for pattern in GREETING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassificationResult(intent="greeting", confidence=0.95)

        # Check farewell patterns
        for pattern in FAREWELL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassificationResult(intent="farewell", confidence=0.95)

        # Check ticket patterns
        for pattern in TICKET_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassificationResult(intent="ticket", confidence=0.9)

        # Check help patterns (generic help, not domain-specific)
        for pattern in HELP_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # If it's a generic help request without domain keywords, return "help"
                has_domain_keywords = any(
                    keyword in text.lower()
                    for keywords in self.patterns.values()
                    for keyword in keywords
                    if keywords.get(keyword, 0) >= 2.0  # Only check strong keywords
                )
                if not has_domain_keywords:
                    return ClassificationResult(intent="help", confidence=0.85)

        # Check knowledge patterns (informational queries)
        for pattern in KNOWLEDGE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassificationResult(intent="knowledge", confidence=0.85)

        return None

    def classify(self, text: Any) -> ClassificationResult:
        """
        Classify a student query into an intent category.

        Checks conversational intents first, then falls back to domain classification.
        Domain queries (password reset, library hours, etc.) map to "knowledge".

        Args:
            text: The student's question or request

        Returns:
            ClassificationResult with intent and confidence score
        """
        # Handle null/empty input
        if text is None:
            return ClassificationResult(intent="unknown", confidence=0.9)

        if not isinstance(text, str):
            text = str(text)

        normalized = text.strip().lower()
        if not normalized:
            return ClassificationResult(intent="unknown", confidence=0.9)

        # Check conversational intents FIRST (only in conversational mode)
        if self.mode == "conversational":
            conv_result = self._check_conversational_intent(normalized)
            if conv_result:
                return conv_result

        # Check for escalation phrases
        if self._requires_escalation(normalized):
            return ClassificationResult(intent="general", confidence=0.85)

        # Calculate scores for each intent
        scores: dict[IntentType, float] = {}
        for intent, patterns in self.patterns.items():
            scores[intent] = self._calculate_score(normalized, patterns)

        # Find the top two intents
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_intent, top_score = sorted_intents[0]
        second_intent, second_score = (
            sorted_intents[1] if len(sorted_intents) > 1 else (None, 0)
        )

        # If top score is too low, fall back to unknown
        if top_score < 1.5:
            return ClassificationResult(intent="unknown", confidence=0.4)

        # If scores are too close (ambiguous), consider unknown
        score_gap = top_score - second_score
        if score_gap < self.confidence_threshold and top_score < 3.0:
            # But only if general isn't already the top
            if top_intent != "general":
                return ClassificationResult(intent="unknown", confidence=0.5)

        # Calculate confidence based on score magnitude and gap
        confidence = min(0.95, 0.5 + (top_score / 10) + (score_gap / 5))

        # In domain mode, return the actual domain intent
        if self.mode == "domain":
            return ClassificationResult(intent=top_intent, confidence=confidence)

        # Map domain intents to "knowledge" for conversational compatibility
        # Domain-specific queries are informational/knowledge queries
        if top_intent in (
            "financial_aid",
            "registration",
            "housing",
            "it_support",
            "academic_advising",
            "student_accounts",
        ):
            return ClassificationResult(intent="knowledge", confidence=confidence)

        # "general" stays as-is (ambiguous queries needing escalation)
        return ClassificationResult(intent=top_intent, confidence=confidence)

    def _calculate_score(self, text: str, patterns: dict[str, float]) -> float:
        """Calculate weighted score for a set of patterns."""
        score = 0.0
        for pattern, weight in patterns.items():
            if pattern in text:
                score += weight
        return score

    def _requires_escalation(self, text: str) -> bool:
        """Check if query contains phrases requiring human escalation."""
        return any(phrase in text for phrase in ESCALATION_PHRASES)

    @staticmethod
    def _contains_any(text: str, candidates: list[str]) -> bool:
        """Check if text contains any of the candidate phrases."""
        return any(candidate in text for candidate in candidates)


# Standalone function for simple usage (as per exercise skeleton)
def classify_intent(query: str) -> IntentType:
    """
    Classify a student query into one of 7 intent categories.

    This is a convenience function that wraps IntentClassifier.

    Args:
        query: The student's question or request

    Returns:
        The classified intent category
    """
    classifier = IntentClassifier()
    result = classifier.classify(query)
    return result.intent
