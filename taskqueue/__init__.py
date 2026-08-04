"""Redis-backed distributed task queue.

Public API:
    QueueManager — enqueue/dequeue jobs, retry with exponential backoff,
                   dead-letter queue, stats.
    Worker       — thread-pool job consumer. Takes a `handler` callable that
                   receives a job dict and returns its result.
"""

from taskqueue.manager import QueueManager
from taskqueue.worker import Worker

__version__ = "1.0.0"

__all__ = ["QueueManager", "Worker", "__version__"]
