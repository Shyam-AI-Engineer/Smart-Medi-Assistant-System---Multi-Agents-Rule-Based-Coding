"""Voice Agent — speech-to-text transcription via Whisper.

Accepts raw audio bytes, sends to Whisper API, returns transcript.
Uses OPENAI_API_KEY if set (OpenAI Whisper directly), otherwise falls
back to EURI_API_KEY with the Euri base URL (OpenAI-compatible).
"""

import io
import os
import logging
from typing import Optional
from openai import OpenAI, APIError

logger = logging.getLogger(__name__)

# Whisper supports these container formats
SUPPORTED_MIME_TYPES = {
    "audio/webm", "audio/ogg", "audio/mpeg", "audio/mp4",
    "audio/wav", "audio/x-wav", "audio/mp3", "audio/m4a",
    "video/webm", "video/mp4",
}
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB (Whisper API limit)


class VoiceAgent:
    """Speech-to-text transcription using OpenAI Whisper."""

    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        euri_key = os.getenv("EURI_API_KEY")

        if openai_key:
            # Prefer direct OpenAI for Whisper
            self.client = OpenAI(api_key=openai_key)
            logger.info("VoiceAgent: using OpenAI Whisper (OPENAI_API_KEY)")
        elif euri_key:
            # Fall back to Euri (OpenAI-compatible endpoint)
            self.client = OpenAI(
                api_key=euri_key,
                base_url=os.getenv("EURI_BASE_URL", "https://api.euron.one/api/v1/euri"),
            )
            logger.info("VoiceAgent: using Euri endpoint for Whisper")
        else:
            raise ValueError("Neither OPENAI_API_KEY nor EURI_API_KEY is set")

        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
        self.agent_name = "voice"

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "recording.webm",
        language: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio file content
            filename:    Original filename (used for MIME detection by Whisper)
            language:    Optional ISO-639-1 language hint (e.g. "en")

        Returns:
            {
                "transcript": str,
                "language":   str,
                "agent_used": "voice",
                "error":      False,
            }
        """
        try:
            if len(audio_bytes) > MAX_AUDIO_BYTES:
                raise ValueError(
                    f"Audio file too large ({len(audio_bytes) // (1024*1024)} MB). "
                    f"Maximum allowed is 25 MB."
                )

            logger.info(
                f"Transcribing audio: {len(audio_bytes)} bytes, file={filename}"
            )

            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            kwargs: dict = {
                "model": self.whisper_model,
                "file": audio_file,
                "response_format": "json",
            }
            if language:
                kwargs["language"] = language

            response = self.client.audio.transcriptions.create(**kwargs)

            transcript = response.text.strip() if response.text else ""
            detected_language = getattr(response, "language", language or "en")

            logger.info(
                f"Transcription complete: {len(transcript)} chars, "
                f"language={detected_language}"
            )

            return {
                "transcript": transcript,
                "language": detected_language,
                "agent_used": self.agent_name,
                "error": False,
            }

        except ValueError as e:
            logger.warning(f"Voice agent validation error: {e}")
            raise

        except APIError as e:
            logger.error(f"Whisper API error: {e}")
            return {
                "transcript": "",
                "language": language or "en",
                "agent_used": self.agent_name,
                "error": True,
                "error_message": "Speech-to-text service temporarily unavailable. Please type your message.",
            }

        except Exception as e:
            logger.error(f"Unexpected transcription error: {e}", exc_info=True)
            return {
                "transcript": "",
                "language": language or "en",
                "agent_used": self.agent_name,
                "error": True,
                "error_message": "Could not transcribe audio. Please try again or type your message.",
            }


_voice_agent: Optional[VoiceAgent] = None


def get_voice_agent() -> VoiceAgent:
    """Return shared VoiceAgent singleton."""
    global _voice_agent
    if _voice_agent is None:
        _voice_agent = VoiceAgent()
    return _voice_agent
