from deepgram.core.events import EventType
from deepgram import AsyncDeepgramClient
from app.Config.dataConfig import Config
from app.utils.logger import logger
from typing import Optional
import asyncio

settings = Config.Config.from_env()

class VoiceService:
    def __init__(self) -> None:
        self.client = AsyncDeepgramClient(api_key=settings.DEEPGRAM_API_KEY)

    async def transcribe_stream(
        self, 
        audio_queue: asyncio.Queue, 
        text_queue: asyncio.Queue
    ) -> None:
        """
        Connects to Deepgram Live Transcription and streams audio from audio_queue.
        Puts transcribed text into text_queue.
        """
        if not self.client:
            return

        try:
            async with self.client.listen.v1.connect(
                model=settings.TRANSCRIPTION_MODEL,
                language=settings.TRANSCRIPTION_LANGUAGE,
                smart_format=settings.TRANSCRIPTION_SMART_FORMAT,
                interim_results=settings.INTERIM_RESULTS,
                utterance_end_ms=settings.UTTERANCE_END_MS,
                vad_events=settings.INTERIM_RESULTS,
            ) as connection:

                async def on_message(result, **kwargs):
                    channel = getattr(result, 'channel', None)
                    if channel:
                        alternatives = getattr(channel, 'alternatives', [])
                        if alternatives:
                            transcript = alternatives[0].transcript
                            is_final = getattr(result, 'is_final', False)
                            
                            if transcript and len(transcript) > 0:
                                logger.info(f"Transcript: '{transcript}' (Final: {is_final})")
                                if is_final:
                                    await text_queue.put(transcript)
                                    logger.info(f"Put transcript in queue: {transcript}")
                    else:
                        pass

                async def on_error(error, **kwargs):
                    logger.error(f"Deepgram Error: {error}")

                # Register callbacks
                connection.on(EventType.MESSAGE, on_message)
                connection.on(EventType.ERROR, on_error)

                # Start the listener in a background task to receive messages
                # connection.start_listening() loops over the websocket
                listener_task = asyncio.create_task(connection.start_listening())

                try:
                    while True:
                        data = await audio_queue.get()
                        if data is None: # Sentinel to stop
                            break
                        await connection.send_media(data)
                except Exception as e:
                    logger.error(f"Error sending audio to Deepgram: {e}")
                finally:
                    # Stop the listener
                    listener_task.cancel()
                    try:
                        await listener_task
                    except asyncio.CancelledError:
                        pass
                    # Context manager handles closing the connection

        except Exception as e:
            logger.error(f"VoiceService Error: {e}")

    async def text_to_speech(
        self, 
        text: str
    ) -> Optional[bytes]:
        """
        Converts text to speech using Deepgram.
        Returns audio bytes.
        """
        if not self.client:
            return None

        try:  
            audio_data = bytearray()
            async for chunk in self.client.speak.v1.audio.generate(
                text=text,
                model=settings.TTS_MODEL
            ):
                audio_data.extend(chunk)
            
            return bytes(audio_data)
            
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return None
