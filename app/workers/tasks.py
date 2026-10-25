import asyncio
import httpx
from app.core.config import get_settings
from app.services.reports import build_report
from app.workers.celery_app import celery_app

@celery_app.task(name="app.workers.tasks.generate_report")
def generate_report(records: list[dict], title: str) -> dict[str, str]:
    return {"path": str(build_report(records, title)), "title": title}

@celery_app.task(name="app.workers.tasks.daily_report")
def daily_report() -> dict[str, str]:
    return generate_report([], "Scheduled Daily Enterprise Report")

@celery_app.task(name="app.workers.tasks.publish_outbound_event")
def publish_outbound_event(event_type: str, payload: dict) -> None:
    url = get_settings().outbound_webhook_url
    if not url:
        return
    async def publish() -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"event_type": event_type, "payload": payload})
    asyncio.run(publish())
