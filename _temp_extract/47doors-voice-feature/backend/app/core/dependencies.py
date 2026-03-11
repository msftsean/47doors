from __future__ import annotations
"""
Dependency injection container for the Front Door Support Agent.
Provides service instances based on configuration (mock vs production).
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.interfaces import (
    AuditLogInterface,
    BrandingServiceInterface,
    KnowledgeServiceInterface,
    LLMServiceInterface,
    RealtimeServiceInterface,
    SessionStoreInterface,
    TicketServiceInterface,
)


@lru_cache
def get_llm_service(settings: Settings | None = None) -> LLMServiceInterface:
    """Get LLM service instance (mock or production)."""
    if settings is None:
        settings = get_settings()

    if settings.use_mock_services:
        from app.services.mock.llm_service import MockLLMService
        return MockLLMService()
    else:
        from app.services.azure.llm_service import AzureOpenAILLMService
        return AzureOpenAILLMService(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
        )


@lru_cache
def get_ticket_service(settings: Settings | None = None) -> TicketServiceInterface:
    """Get ticket service instance (mock or production)."""
    if settings is None:
        settings = get_settings()

    if settings.use_mock_services:
        from app.services.mock.ticket_service import MockTicketService
        return MockTicketService()
    else:
        # TODO: Implement ServiceNow service
        from app.services.mock.ticket_service import MockTicketService
        return MockTicketService()


@lru_cache
def get_knowledge_service(settings: Settings | None = None) -> KnowledgeServiceInterface:
    """Get knowledge service instance (mock or production)."""
    if settings is None:
        settings = get_settings()

    if settings.use_mock_services:
        from app.services.mock.knowledge_service import MockKnowledgeService
        return MockKnowledgeService()
    else:
        # TODO: Implement Azure AI Search service
        from app.services.mock.knowledge_service import MockKnowledgeService
        return MockKnowledgeService()


@lru_cache
def get_session_store(settings: Settings | None = None) -> SessionStoreInterface:
    """Get session store instance (mock or production)."""
    if settings is None:
        settings = get_settings()

    if settings.use_mock_services:
        from app.services.mock.session_store import MockSessionStore
        return MockSessionStore()
    else:
        # TODO: Implement Cosmos DB session store
        from app.services.mock.session_store import MockSessionStore
        return MockSessionStore()


@lru_cache
def get_audit_log(settings: Settings | None = None) -> AuditLogInterface:
    """Get audit log instance (mock or production)."""
    if settings is None:
        settings = get_settings()

    if settings.use_mock_services:
        from app.services.mock.audit_log import MockAuditLog
        return MockAuditLog()
    else:
        # TODO: Implement Cosmos DB audit log
        from app.services.mock.audit_log import MockAuditLog
        return MockAuditLog()


@lru_cache
def get_branding_service(settings: Settings | None = None) -> BrandingServiceInterface:
    """Get branding service instance (mock or production)."""
    if settings is None:
        settings = get_settings()

    if settings.use_mock_services:
        from app.services.mock.branding_service import MockBrandingService
        return MockBrandingService()
    else:
        # TODO: Implement Cosmos DB branding service
        from app.services.mock.branding_service import MockBrandingService
        return MockBrandingService()


# FastAPI dependency annotations
SettingsDep = Annotated[Settings, Depends(get_settings)]
LLMServiceDep = Annotated[LLMServiceInterface, Depends(get_llm_service)]
TicketServiceDep = Annotated[TicketServiceInterface, Depends(get_ticket_service)]
KnowledgeServiceDep = Annotated[KnowledgeServiceInterface, Depends(get_knowledge_service)]
SessionStoreDep = Annotated[SessionStoreInterface, Depends(get_session_store)]
AuditLogDep = Annotated[AuditLogInterface, Depends(get_audit_log)]
BrandingServiceDep = Annotated[BrandingServiceInterface, Depends(get_branding_service)]


def get_realtime_service(settings: Settings | None = None) -> RealtimeServiceInterface:
    """Get realtime service instance (mock or production)."""
    if settings is None:
        settings = get_settings()

    llm = get_llm_service()
    tickets = get_ticket_service()
    knowledge = get_knowledge_service()
    session_store = get_session_store()

    if settings.use_mock_services:
        from app.services.mock.realtime_service import MockRealtimeService
        return MockRealtimeService(
            llm_service=llm,
            ticket_service=tickets,
            knowledge_service=knowledge,
            session_store=session_store,
        )
    else:
        from app.services.azure.realtime_service import AzureRealtimeService
        return AzureRealtimeService(
            endpoint=settings.azure_openai_realtime_endpoint or settings.azure_openai_endpoint,
            api_key=settings.azure_openai_realtime_api_key or settings.azure_openai_api_key,
            deployment=settings.azure_openai_realtime_deployment,
            api_version=settings.azure_openai_realtime_api_version,
            llm_service=llm,
            ticket_service=tickets,
            knowledge_service=knowledge,
            session_store=session_store,
            voice=settings.realtime_voice,
            vad_threshold=settings.realtime_vad_threshold,
        )


RealtimeServiceDep = Annotated[RealtimeServiceInterface, Depends(get_realtime_service)]


def clear_service_caches() -> None:
    """Clear all cached service instances (for testing)."""
    get_llm_service.cache_clear()
    get_ticket_service.cache_clear()
    get_knowledge_service.cache_clear()
    get_session_store.cache_clear()
    get_audit_log.cache_clear()
    get_branding_service.cache_clear()
