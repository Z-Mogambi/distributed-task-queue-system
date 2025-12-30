import sys
sys.path.append('..')

from task_queue.manager import QueueManager
import time

def main():
    print("Testing Retry Logic\n")
    
    queue = QueueManager()
    
    # Submiting a flaky job that will fail and retry
    print("Submitting flaky job (will fail ~50% of the time)...")
    # This URL has a 50% chance of returning 200 OK and 50% chance of 503 Service Unavailable
    job_id = queue.enqueue("flaky_service", {"url": "http://httpstat.us/random/200,503"}, max_retries=3)
    print(f"Job submitted: {job_id[:8]}\n")
    
    print("   Start worker in another terminal to see retry behavior")
    print("   cd worker")
    print("   python3 worker.py\n")
    
    # Monitor job status
    for i in range(20):
        time.sleep(2)
        job = queue.get_job(job_id)
        if job:
            status = job['status']
            attempts = job['attempts']
            print(f"[{i*2}s] Status: {status}, Attempts: {attempts}")
            
            if status == "completed":
                print("Job completed!")
                break
            elif status == "failed":
                print("Job permanently failed")
                break

if __name__ == "__main__":
    main()
