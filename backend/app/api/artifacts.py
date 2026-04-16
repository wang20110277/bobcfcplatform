from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.artifact import Artifact
from app.services.artifact_service import generate_artifact_content
from app.services.minio_service import upload_object, ensure_bucket

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

ARTIFACT_TOPIC = "artifact-topic"


@router.get("")
async def list_artifacts(
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        return []
    result = await db.execute(select(Artifact).order_by(Artifact.created_at.desc()))
    artifacts = result.scalars().all()
    output = []
    for a in artifacts:
        created = a.created_at
        if isinstance(created, datetime) and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        output.append({
            "id": a.id,
            "sessionId": a.session_id,
            "name": a.name,
            "type": a.type,
            "status": a.status,
            "createdAt": created.isoformat(),
            "storagePath": a.storage_path,
        })
    return output


@router.post("/generate")
async def generate_artifact(
    body: dict,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    artifact_type = body.get("type")
    session_id = body.get("sessionId") or str(current_user.id)
    name = body.get("name") or f"Generated {artifact_type}"

    # Create artifact with PENDING status
    artifact = Artifact(
        id=str(uuid4()),
        session_id=session_id,
        name=name,
        type=artifact_type,
        status="PENDING",
    )
    db.add(artifact)
    await db.commit()

    # Generate content synchronously (for simplicity; can be moved to RocketMQ)
    try:
        ensure_bucket()
        content_bytes, content_type = await generate_artifact_content(artifact_type, name)
        object_path = f"{artifact_type}/{artifact.id}/{name.replace(' ', '_')}.txt"
        upload_object("artifacts", object_path, content_bytes, content_type)

        artifact.status = "COMPLETED"
        artifact.storage_path = object_path
        await db.commit()
    except Exception as e:
        artifact.status = "FAILED"
        await db.commit()

    created = artifact.created_at
    if isinstance(created, datetime) and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    return {
        "id": artifact.id,
        "sessionId": artifact.session_id,
        "name": artifact.name,
        "type": artifact.type,
        "status": artifact.status,
        "createdAt": created.isoformat(),
        "storagePath": artifact.storage_path,
    }
