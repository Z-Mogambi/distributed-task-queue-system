import sys
sys.path.append('..')

from task_queue.manager import QueueManager
import time

def main():
    print("Submitting test jobs to queue...\n")
    
    queue = QueueManager()
    
    # Submit 5 test jobs
    jobs = [
        ("email", {"to": "alice@example.com", "subject": "Welcome", "body": "Hello Alice!"}),
        ("calculation", {"numbers": [1, 2, 3, 4, 5]}),
        ("image_processing", {"image_url": "https://example.com/photo.jpg", "operations": ["resize", "compress"]}),
        ("email", {"to": "bob@example.com", "subject": "Update", "body": "Hello Bob!"}),
        ("calculation", {"numbers": [10, 20, 30, 40, 50]}),
    ]
    
    for job_type, payload in jobs:
        job_id = queue.enqueue(job_type, payload)
        print(f"Submitted {job_type} job: {job_id[:8]}...")
    
    print(f"\nTotal jobs submitted: {len(jobs)}")
    print("\n Now start the worker in another terminal:")
    print("   cd worker")
    print("   python worker.py")
    print("\n Watching jobs get processed...\n")
    
    # Monitor for 30 seconds
    for i in range(30):
        time.sleep(1)
        # query Redis here to check job statuses?
    
    print("\n Test complete!")

if __name__ == "__main__":
    main()