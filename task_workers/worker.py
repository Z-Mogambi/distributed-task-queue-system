import sys

from task_queue.manager import QueueManager
from task_workers.handlers import process_job
import signal

class Worker:
    def __init__(self, name="Worker-1"):
    
        self.name = name
        self.queue = QueueManager()
        self.running = True

    
    def handle_shutdown(self, signum, frame):
        # handling Ctrl+C gracefully.
        print(f"\n{self.name} shutting down...")
        self.running = False
    
         
    def run(self):
        """
        Main worker loop.
        
        TODO:
        1. Register signal handler for SIGINT (Ctrl+C)
        2. Print "Worker started" message
        3. Loop while self.running is True:
           a. Dequeue job (this blocks for 5 seconds)
           b. If no job, continue (just loop again)
           c. If job exists:
              - Print "Processing job {job_id}..."
              - Try to process it
              - If success: complete_job with result
              - If error: fail_job with error message
        4. Print "Worker stopped" when loop exits
        """
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        print(f"{self.name} Worker started...")
        print(f"{self.name} is waiting for jobs...")

        while self.running:
            job = self.queue.dequeue()
            if job is None:
                continue

            print(f"{self.name} processing job {job['id'][:8]}... (type: {job['type']}, attempt: {job['attempts'] + 1})")

            try:
                result = process_job(job)
                self.queue.complete_job(job['id'], result)
                print(f"{self.name} completed job {job['id'][:8]}")

            except Exception as e:
                self.queue.fail_job(job['id'], str(e))
                print(f"{self.name} failed job {job['id'][:8]}: {e}")

        print(f"{self.name} Worker stopped")


if __name__ == "__main__":
    # Allow custom worker name from command line
    worker_name = sys.argv[1] if len(sys.argv) > 1 else "Worker-1"
    
    worker = Worker(name=worker_name)
    worker.run()
