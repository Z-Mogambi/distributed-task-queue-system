import signal
import requests
from concurrent.futures import ThreadPoolExecutor

from taskqueue.manager import QueueManager

class Worker:
    def __init__(self, name="Worker-1", max_workers=10, handler=None):
        """`handler` is a callable taking a job dict and returning its result."""
        if handler is None:
            raise ValueError("Worker requires a handler callable")

        self.name = name
        self.queue = QueueManager()
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.handler = handler

    
    def handle_shutdown(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print(f"\n{self.name} shutting down, waiting for running jobs to finish...")
        self.running = False
        self.executor.shutdown(wait=True)

    def _fire_callback(self, job, data, success):
        """POST the job result to callback_url if one was provided."""
        callback_url = job.get("callback_url")
        if not callback_url:
            return
        try:
            requests.post(
                callback_url,
                json={
                    "job_id": job["id"],
                    "type": job["type"],
                    "status": "completed" if success else "failed",
                    "result": data,
                },
                timeout=5,
            )
            print(f"{self.name} callback fired for job {job['id'][:8]} -> {callback_url}")
        except Exception as e:
            print(f"{self.name} callback failed for job {job['id'][:8]}: {e}")

    def _process_job_task(self, job):
        """Task executed by a thread pool worker to process a single job."""
        print(f"{self.name} processing job {job['id'][:8]}... (type: {job['type']}, attempt: {job['attempts'] + 1})")
        try:
            result = self.handler(job)
            self.queue.complete_job(job['id'], result)
            print(f"{self.name} completed job {job['id'][:8]}")
            self._fire_callback(job, result, success=True)
        except Exception as e:
            still_retrying = self.queue.fail_job(job['id'], str(e))
            if not still_retrying:
                self._fire_callback(job, {"error": str(e)}, success=False)
         
    def run(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        print(f"{self.name} started with {self.executor._max_workers} threads...")

        while self.running:
            # Check for delayed jobs that are ready to be re-queued
            try:
                requeued_count = self.queue.requeue_delayed_jobs()
                if requeued_count > 0:
                    print(f"{self.name} re-queued {requeued_count} delayed jobs.")
            except Exception as e:
                print(f"Error re-queuing delayed jobs: {e}")

            # Fetch a job. This blocks for up to 5 seconds.
            job = self.queue.dequeue()
            if job is None:
                # If dequeue times out, loop continues and checks for delayed jobs again.
                continue

            # Submit the job to the thread pool for processing
            self.executor.submit(self._process_job_task, job)

        print(f"\n{self.name} worker has stopped.")
