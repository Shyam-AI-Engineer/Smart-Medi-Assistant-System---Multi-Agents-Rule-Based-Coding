"""Voice API endpoint.

Routes:
  POST /api/v1/voice/transcribe  – audio → text via Whisper
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from pydantic import BaseModel

from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from app.agents.voice_agent import get_voice_agent, SUPPORTED_MIME_TYPES, MAX_AUDIO_BYTES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

ALLOWED_EXTENSIONS = {".mp3", ".mp4", ".wav", ".webm", ".m4a", ".ogg", ".mpeg"}


class TranscribeResponse(BaseModel):
    transcript: str
    language: str
    agent_used: str


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio to text",
    description="Upload an audio file and receive a text transcript via Whisper.",
)
@limiter.limit("10/minute")
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(..., description="Audio file (webm, wav, mp3, m4a, ogg — max 25 MB)"),
    current_user: dict = Depends(get_current_user),
) -> TranscribeResponse:
    """
    Transcribe an audio recording to text.

    Accepts multipart/form-data with a single 'audio' field.
    Supported formats: webm, wav, mp3, mp4, m4a, ogg.
    Maximum file size: 25 MB.

    Returns the transcript text ready to be pasted into the chat input.

    Raises:
        400: No audio data, file too large, or unsupported format
        401: Not authenticated
        503: Whisper API unavailable
    """
    try:
        # Validate content type
        content_type = (audio.content_type or "").lower()
        filename = audio.filename or "recording.webm"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if content_type and content_type not in SUPPORTED_MIME_TYPES:
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported audio format '{content_type}'. "
                           f"Use webm, wav, mp3, m4a, or ogg.",
                )

        # Read bytes
        audio_bytes = await audio.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty.",
            )

        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio file too large ({len(audio_bytes) // (1024*1024)} MB). Maximum is 25 MB.",
            )

        logger.info(
            f"Transcription request from user {current_user['user_id']}: "
            f"{len(audio_bytes)} bytes, type={content_type}"
        )

        agent = get_voice_agent()
        result = agent.transcribe(audio_bytes=audio_bytes, filename=filename)

        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result.get(
                    "error_message",
                    "Speech-to-text service temporarily unavailable.",
                ),
            )

        logger.info(
            f"Transcription success for user {current_user['user_id']}: "
            f"{len(result['transcript'])} chars"
        )

        return TranscribeResponse(
            transcript=result["transcript"],
            language=result.get("language", "en"),
            agent_used=result["agent_used"],
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in transcribe endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process audio. Please try again.",
        )
