"""Safe provider-neutral classification of Agentic Ingestion failures."""

from __future__ import annotations


def classify_pipeline_failure(error: BaseException) -> str:
    """Return one stable secret-free operational failure reason."""

    status_code = getattr(error, "status_code", None)
    name = type(error).__name__.lower()

    if status_code == 401 or "authentication" in name:
        return "llm_authentication_failed"
    if status_code == 403 or "permission" in name:
        return "llm_permission_denied"
    if status_code == 429 or "ratelimit" in name:
        return "llm_rate_limited"
    if "timeout" in name:
        return "llm_timeout"
    if "connection" in name:
        return "llm_connection_failed"
    if isinstance(status_code, int):
        if 400 <= status_code < 500:
            return "llm_request_rejected"
        if status_code >= 500:
            return "llm_provider_unavailable"
    return "team_agentic_ingestion_failed"
