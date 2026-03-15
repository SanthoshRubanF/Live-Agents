"""
Session Manager for Gemini Live Agent.

Manages active WebSocket connections, ADK runners, and session metadata.
Provides functionality for tracking session duration, turn counts, current status,
and running background cleanup tasks to reap stale or abandoned sessions.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages concurrent user sessions for the Live Agent.
    Tracks WebSocket sessions, ADK runners, and session metadata for logging/debugging.
    """
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def create_session(self, ws_id: str, runner: Any, adk_session_id: str) -> Dict[str, Any]:
        """
        Create a new session entry.
        
        Args:
            ws_id: Unique WebSocket identifier.
            runner: The ADK runner instance for this session.
            adk_session_id: The underlying ADK session ID.
            
        Returns:
            The created session dictionary.
        """
        now = time.time()
        session_data = {
            "ws_id": ws_id,
            "runner": runner,
            "adk_session_id": adk_session_id,
            "created_at": now,
            "turn_count": 0,
            "last_activity": now,
            "status": "idle"
        }
        
        async with self.lock:
            self.sessions[ws_id] = session_data
            
        logger.info(f"Created new session {ws_id}. Total sessions: {len(self.sessions)}")
        return session_data

    async def get_session(self, ws_id: str) -> Optional[Dict[str, Any]]:
        """
        Return session dict or None.
        
        Args:
            ws_id: Unique WebSocket identifier.
            
        Returns:
            The session dictionary if found, else None.
        """
        async with self.lock:
            return self.sessions.get(ws_id)

    async def update_status(self, ws_id: str, status: str):
        """
        Update session status and refresh last_activity.
        
        Args:
            ws_id: Unique WebSocket identifier.
            status: The new status ("listening", "thinking", "speaking", "idle").
        """
        async with self.lock:
            if ws_id in self.sessions:
                self.sessions[ws_id]["status"] = status
                self.sessions[ws_id]["last_activity"] = time.time()
            else:
                logger.warning(f"Attempted to update status for unknown session {ws_id}")

    async def increment_turns(self, ws_id: str):
        """
        Increment turn_count for the session and refresh last_activity.
        
        Args:
            ws_id: Unique WebSocket identifier.
        """
        async with self.lock:
            if ws_id in self.sessions:
                self.sessions[ws_id]["turn_count"] += 1
                self.sessions[ws_id]["last_activity"] = time.time()
            else:
                logger.warning(f"Attempted to increment turns for unknown session {ws_id}")

    async def close_session(self, ws_id: str):
        """
        Clean up session: close runner, remove from dict, log stats.
        
        Args:
            ws_id: Unique WebSocket identifier.
        """
        async with self.lock:
            session = self.sessions.pop(ws_id, None)
            
        if not session:
            logger.warning(f"Attempted to close unknown session {ws_id}")
            return

        now = time.time()
        duration = now - session["created_at"]
        turn_count = session["turn_count"]

        # Gracefully handle runner teardown if supported
        runner = session.get("runner")
        if runner:
            try:
                # If there's an explicit cleanup or close method on the runner
                if hasattr(runner, 'close') and callable(getattr(runner, 'close')):
                    if asyncio.iscoroutinefunction(runner.close):
                        await runner.close()
                    else:
                        runner.close()
            except Exception as e:
                logger.error(f"Error closing runner for session {ws_id}: {e}")

        logger.info(
            f"Closed session {ws_id} - "
            f"Duration: {duration:.2f}s, "
            f"Total turns: {turn_count}, "
            f"Remaining sessions: {len(self.sessions)}"
        )

    async def get_all_stats(self) -> Dict[str, Any]:
        """
        Return summary of all active sessions (for /health endpoint).
        
        Returns:
            Dictionary containing aggregated statistics.
        """
        async with self.lock:
            total_active = len(self.sessions)
            status_counts = {"listening": 0, "thinking": 0, "speaking": 0, "idle": 0}
            total_turns_active = 0
            
            for s in self.sessions.values():
                status = s.get("status", "idle")
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
                total_turns_active += s.get("turn_count", 0)

            return {
                "active_sessions": total_active,
                "status_distribution": status_counts,
                "total_turns_in_progress": total_turns_active
            }

    async def cleanup_stale_sessions(self, max_idle_seconds: int = 300):
        """
        Close sessions idle longer than max_idle_seconds.
        Should be run periodically as a background task.
        
        Args:
            max_idle_seconds: Maximum allowed idle time before a session is reaped.
        """
        now = time.time()
        stale_ws_ids = []
        
        async with self.lock:
            for ws_id, session in self.sessions.items():
                if now - session["last_activity"] > max_idle_seconds:
                    stale_ws_ids.append(ws_id)
        
        for ws_id in stale_ws_ids:
            logger.info(f"Session {ws_id} flagged as stale (idle > {max_idle_seconds}s). Reaping.")
            await self.close_session(ws_id)
            
    def start_cleanup_task(self, max_idle_seconds: int = 300, interval_seconds: float = 60.0):
        """
        Starts cleanup_stale_sessions as an asyncio background task.
        
        Args:
            max_idle_seconds: Threshold for identifying stale sessions.
            interval_seconds: Frequency to run the cleanup check.
        """
        async def _cleanup_loop():
            logger.info(f"Starting session cleanup background task (interval={interval_seconds}s, threshold={max_idle_seconds}s)")
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    await self.cleanup_stale_sessions(max_idle_seconds)
                except asyncio.CancelledError:
                    logger.info("Session cleanup background task cancelled.")
                    break
                except Exception as e:
                    logger.error(f"Error in session cleanup task: {e}")

        # ensure we don't start multiple instances unintentionally
        if self._cleanup_task and not self._cleanup_task.done():
            logger.warning("Cleanup task is already running.")
            return

        # It's generally best to attach this to the running event loop
        loop = asyncio.get_running_loop()
        self._cleanup_task = loop.create_task(_cleanup_loop())

# Global instance for easy import across modules
session_manager = SessionManager()
