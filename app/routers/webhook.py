from fastapi import APIRouter, Request, Response, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db, SessionLocal
from app.services.event_handler import EventHandler

router = APIRouter(prefix="/webhook", tags=["Webhook"])

@router.get("")
async def verify_webhook(request: Request):
    """Verificación obligatoria de Meta para activar el webhook."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Token de verificación inválido", status_code=403)

def run_event_processor(payload: dict):
    db = SessionLocal()
    try:
        import asyncio
        asyncio.run(EventHandler.process_incoming_payload(payload, db))
    finally:
        db.close()

@router.post("")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Recepción de eventos entrantes de WhatsApp."""
    payload = await request.json()
    background_tasks.add_task(run_event_processor, payload)
    return {"status": "queued"}