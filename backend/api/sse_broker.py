"""Server-Sent Events (SSE) Broker.

Asynchronous in-memory pub/sub broker streaming real-time container logs,
status transitions, and containment events to connected frontend clients.
"""

import asyncio
import json
from typing import Dict, Set


class SSEBroker:
    """Manages active SSE client subscriber queues per task."""

    def __init__(self):
        self._task_subscribers: Dict[str, Set[asyncio.Queue]] = {}

    def subscribe(self, task_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if task_id not in self._task_subscribers:
            self._task_subscribers[task_id] = set()
        self._task_subscribers[task_id].add(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        if task_id in self._task_subscribers:
            self._task_subscribers[task_id].discard(queue)
            if not self._task_subscribers[task_id]:
                del self._task_subscribers[task_id]

    async def broadcast(self, task_id: str, event_type: str, data: dict):
        if task_id in self._task_subscribers:
            formatted_event = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            for q in list(self._task_subscribers[task_id]):
                await q.put(formatted_event)
