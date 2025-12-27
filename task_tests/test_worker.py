import sys
import os

# Add project root to Python path to allow importing task_queue
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from task_queue.manager import QueueManager
import time

def main():
    print("🚀 Starting Webhook Retry and Scale Test\n")
    
    queue = QueueManager()
    
    job_type = "flaky_service"
    payload = {"url": "http://httpstat.us/503"}
    num_jobs = 200
    
    print(f"Submitting {num_jobs} jobs of type '{job_type}'...")
    
    start_time = time.time()
    for i in range(num_jobs):
        job_id = queue.enqueue(job_type, payload)
        print(f"  Submitted job {i+1}/{num_jobs}: {job_id[:12]}...")
        
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ All {num_jobs} jobs submitted in {duration:.2f} seconds.")
    
    if duration > 0:
        jobs_per_second = num_jobs / duration
        print(f"   (Throughput: {jobs_per_second:.2f} jobs/sec)")

    print("\nNow, start the worker(s) to process the jobs and observe retries.")

if __name__ == "__main__":
    main()
