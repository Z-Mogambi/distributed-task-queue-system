import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from taskqueue import Worker
from task_workers.handlers import process_job

if __name__ == "__main__":
    # Allow custom worker name from command line
    worker_name = sys.argv[1] if len(sys.argv) > 1 else "Worker-1"

    # To achieve 1000 jobs/min, we need to handle ~17 jobs/sec.
    # If each job takes ~2s (network calls), we need at least 34 workers.
    # We add a buffer for safety. Let's start with 50.
    worker = Worker(name=worker_name, max_workers=50, handler=process_job)
    worker.run()
