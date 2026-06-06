"""
Structured logging konfigürasyonu — structlog ile.
JSON formatlı loglar ELK/Datadog ile uyumludur.
"""
import logging  # Uygulama loglama
import sys

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Uygulama geneli logging ayarlarını yapar.
    Development'ta okunabilir, production'da JSON formatı kullanır.
    """
    # Standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),   # Dev'de renkli, güzel format
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )


# Kullanım örneği:
# import structlog
# logger = structlog.get_logger(__name__)
# logger.info("rag_query", query="spor ayakkabı", results_count=5, duration_ms=342)