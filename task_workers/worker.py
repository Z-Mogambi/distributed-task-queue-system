import sys
sys.path.append('..')  # So Python can find queue module

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
        
        print(f"{self.name} started...")

        while self.running:
            job = self.queue.dequeue()
            if not job:
                continue

            job_id = job.get('id', 'uknown')
            print(f"{self.name} processing job {job_id}...")

            try:
                result = process_job(job)
                self.queue.complete_job(job_id, result)
                print(f"{self.name} completed job {job_id}")
            except Exception as e:
                error_message = str(e)
                self.queue.fail_job(job_id, error_message)
                print(f"{self.name} failed job {job_id}: {error_message}")

        print(f"{self.name} stopped")


if __name__ == "__main__":
    # Allow custom worker name from command line
    worker_name = sys.argv[1] if len(sys.argv) > 1 else "Worker-1"
    
    worker = Worker(name=worker_name)
    worker.run()