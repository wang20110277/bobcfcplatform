"""Artifact generation service using Gemini."""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def generate_artifact_content(artifact_type: str, name: str) -> tuple[bytes, str]:
    """
    Generate artifact content using Gemini based on type.
    Returns (content_bytes, content_type).
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    from app.config import get_settings

    settings = get_settings()
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.gemini_api_key)

    if artifact_type == "PPT":
        prompt = (
            f"Create a PowerPoint presentation outline for '{name}'. "
            "Return it as a structured text outline with slide titles and bullet points. "
            "Format each slide with --- separator."
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.encode("utf-8")
        return content, "text/plain"

    elif artifact_type == "AUDIO":
        prompt = (
            f"Generate a script for an audio narration about '{name}'. "
            "Return it as plain text suitable for text-to-speech."
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.encode("utf-8")
        return content, "text/plain"

    elif artifact_type == "SUMMARY":
        prompt = (
            f"Create a concise summary document for '{name}'. "
            "Return it as plain text with clear sections."
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.encode("utf-8")
        return content, "text/plain"

    else:
        content = f"Generated artifact: {name} (type: {artifact_type})".encode("utf-8")
        return content, "text/plain"
