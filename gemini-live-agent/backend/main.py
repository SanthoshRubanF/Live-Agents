"""
FastAPI WebSocket Server for Gemini Live Agent.

Handles bidirectional audio and vision streaming via WebSockets.
Integrates with Google ADK to process PCM audio, Base64 images, and text.
"""

import asyncio
import base64
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.genai import types as genai_types

from backend.agent import root_agent
from backend.session_manager import session_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler to log startup and shutdown."""
    logger.info("Starting up Gemini Live Agent Server...")
    
    # Start session manager background cleanup task
    session_manager.start_cleanup_task()
    
    yield
    logger.info("Shutting down Gemini Live Agent Server...")

app = FastAPI(lifespan=lifespan)

# Allow CORS for development and production
# NOTE: Replace "https://your-cloud-run-url.run.app" once deployed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "https://gemini-live-agent-*.a.run.app", # Wildcard for cloud run formats
        "https://your-cloud-run-url.run.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_index():
    """Mount frontend/index.html to serve as the main UI."""
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    """Health endpoint returning standard status payload."""
    # Get active session stats
    stats = await session_manager.get_all_stats()
    
    return {
        "status": "ok", 
        "model": "gemini-3.1-pro-preview", 
        "version": "1.0.0",
        "sessions": stats
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for bidirectional audio/video/text streaming.
    Sets up an ADK runner session and maintains communication loops.
    """
    await websocket.accept()
    session_id = f"session_{id(websocket)}"
    logger.info(f"WebSocket connected. Session ID: {session_id}")
    
    # Initialize ADK runner and session
    session_service = InMemorySessionService()
    APP_NAME = "gemini_live_agent"
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    adk_session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id
    )
        
    await session_manager.create_session(session_id, runner, getattr(adk_session, 'id', str(id(adk_session))))
    
    run_config = RunConfig(
        response_modalities=["AUDIO"],
        streaming_mode=StreamingMode.BIDI
    )

    # LiveRequestQueue bridges WebSocket data into the ADK live stream
    live_request_queue = LiveRequestQueue()


    async def process_runner_output():
        """Receive chunks from ADK runner and forward them to the WebSocket."""
        try:
            async for event in runner.run_live(
                user_id=session_id,
                session_id=adk_session.id,
                live_request_queue=live_request_queue,
                run_config=run_config,
            ):
                # 1. Audio data
                if (event.server_content and
                        event.server_content.model_turn and
                        event.server_content.model_turn.parts):
                    for part in event.server_content.model_turn.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if part.inline_data.mime_type.startswith('audio/'):
                                await websocket.send_bytes(part.inline_data.data)
                        if hasattr(part, 'text') and part.text:
                            await websocket.send_json({
                                "type": "transcript",
                                "role": "agent",
                                "text": part.text
                            })

                # 2. Turn complete signal
                if event.server_content and event.server_content.turn_complete:
                    await websocket.send_json({"type": "status", "state": "listening"})
                    await session_manager.update_status(session_id, "listening")

        except asyncio.CancelledError:
            logger.info("Runner output loop cancelled.")
        except Exception as e:
            logger.error(f"Error in runner output loop: {e}")
            try:
                await websocket.send_json({"type": "error", "message": f"Runner error: {str(e)}"})
            except Exception:
                pass

    runner_task = asyncio.create_task(process_runner_output())
    
    turn_count = 0
    start_time = asyncio.get_event_loop().time()

    try:
        while True:
            # Wait for any incoming messages from the frontend client
            message = await websocket.receive()
            
            if "bytes" in message:
                # Binary frame → raw PCM Int16 audio at 16kHz from microphone
                pcm_bytes = message["bytes"]
                blob = genai_types.Blob(
                    data=pcm_bytes, 
                    mime_type="audio/pcm;rate=16000"
                )
                live_request_queue.send_realtime(blob)

            elif "text" in message:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    
                    if msg_type == "image":
                        # JSON {type: "image", data: "<base64_jpeg>"} → camera frame
                        base64_data = data.get("data", "")
                        if base64_data:
                            # Remove data URI scheme prefix if present (e.g., 'data:image/jpeg;base64,')
                            if "," in base64_data:
                                base64_data = base64_data.split(",", 1)[1]
                            
                            img_bytes = base64.b64decode(base64_data)
                            blob = genai_types.Blob(
                                data=img_bytes, 
                                mime_type="image/jpeg"
                            )
                            live_request_queue.send_realtime(blob)
                    
                    elif msg_type == "text":
                        # JSON {type: "text", content: "..."} → typed text input
                        content = data.get("content", "")
                        if content:
                            await websocket.send_json({
                                "type": "transcript", 
                                "role": "user", 
                                "text": content
                            })
                            live_request_queue.send_realtime(genai_types.Blob(data=content.encode(), mime_type="text/plain"))
                            await session_manager.update_status(session_id, "listening")
                            
                    elif msg_type == "interrupt":
                        # User is speaking, stop agent
                        await websocket.send_json({"type": "status", "state": "listening"})
                        await session_manager.update_status(session_id, "listening")
                        
                        # Note: precise interruption logic in ADK may require a specific payload
                        # Assuming an 'interrupt' command or canceling runner output
                        if hasattr(runner, 'cancel_turn'):
                            runner.cancel_turn(session_id)
                        
                    elif msg_type == "end_turn":
                        # User finished speaking
                        await session_manager.increment_turns(session_id)
                        await websocket.send_json({"type": "status", "state": "thinking"})
                        await session_manager.update_status(session_id, "thinking")
                        
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON over WebSocket.")
                except Exception as e:
                    logger.error(f"Error handling text message: {e}")
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket {session_id} disconnected gracefully.")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
    finally:
        # Session Cleanup
        live_request_queue.close()
        runner_task.cancel()
        
        await session_manager.close_session(session_id)
