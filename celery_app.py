import os
import ssl
from celery import Celery
from kombu import Queue


def _coerce_rediss(url: str) -> str:
    try:
        if os.getenv("REDIS_USE_SSL", "0") == "1" and url and url.startswith("redis://"):
            return "rediss://" + url[len("redis://"):]
    except Exception:
        pass
    return url


def make_celery() -> Celery:
    broker = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    broker = _coerce_rediss(broker)
    backend = _coerce_rediss(backend)

    app = Celery("inventorysbo", broker=broker, backend=backend, include=["tasks", "snb_tasks"])
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "2")),
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        broker_transport_options={
            "visibility_timeout": int(os.getenv("CELERY_VISIBILITY_TIMEOUT", "3600")),
            # Keepalive and health options for Redis/kombu
            "socket_keepalive": True,
            "socket_keepalive_options": {  # values in seconds
                # Platform defaults if not provided
            },
            "retry_on_timeout": True,
            "max_retries": int(os.getenv("CELERY_BROKER_MAX_RETRIES", "100")),
            "interval_start": float(os.getenv("CELERY_BROKER_RETRY_START", "0")),
            "interval_step": float(os.getenv("CELERY_BROKER_RETRY_STEP", "0.2")),
            "interval_max": float(os.getenv("CELERY_BROKER_RETRY_MAX", "5")),
        },
        result_expires=3600,
        broker_connection_retry_on_startup=True,
        task_default_queue=os.getenv("LLM_QUEUE", "celery"),
    )
    # Declare queues explicitly
    default_q = os.getenv("LLM_QUEUE", "celery")
    app.conf.task_queues = (
        Queue(default_q),
        Queue("pdf"),
        Queue("chat"),
    )

    # Enable SSL for Render external Redis (rediss://) or when forced by env
    try:
        if broker.startswith("rediss://") or backend.startswith("rediss://") or os.getenv("REDIS_USE_SSL", "0") == "1":
            ssl_opts = {"ssl_cert_reqs": ssl.CERT_NONE}
            app.conf.broker_use_ssl = ssl_opts
            app.conf.redis_backend_use_ssl = ssl_opts
    except Exception:
        pass
    return app


celery = make_celery()


