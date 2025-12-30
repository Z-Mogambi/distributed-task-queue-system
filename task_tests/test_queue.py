import sys
import os

# sys.path.append('..')  # So Python can find the queue module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from task_queue.manager import QueueManager
import time

def main():
    print("🚀 Starting Queue Tests\n")
    
    # Create queue manager
    queue = QueueManager()
    
    # Test 1: Enqueue a job
    print("=" * 50)
    print("Test 1: Enqueue a webhook job")
    print("=" * 50)
    job_id = queue.enqueue("webhook", {
        "url": "http://httpstat.us/200",
        "data": {"message": "Hello from test_queue!"}
    })
    print(f"Created job: {job_id}\n")
    time.sleep(1)
    
    # Test 2: Dequeue the job
    print("=" * 50)
    print("Test 2: Dequeue the job")
    print("=" * 50)
    job = queue.dequeue()
    if job:
        print(f"   Got job:")
        print(f"   ID: {job['id']}")
        print(f"   Type: {job['type']}")
        print(f"   Status: {job['status']}")
        print(f"   Payload: {job['payload']}\n")
    else:
        print("No job found\n")
    time.sleep(1)
    
    # Test 3: Complete the job
    print("=" * 50)
    print("Test 3: Complete the job")
    print("=" * 50)
    result = {"message_id": "abc123", "sent_at": int(time.time())}
    queue.complete_job(job['id'], result)
    print(f"Job {job['id'][:8]}... marked as completed\n")
    time.sleep(1)
    
    # Test 4: Try to dequeue from empty queue
    print("=" * 50)
    print("Test 4: Dequeue from empty queue (5 sec timeout)")
    print("=" * 50)
    print("Waiting for job... (this will timeout)")
    job = queue.dequeue()
    if job:
        print(f"Unexpected job: {job}")
    else:
        print("Queue is empty (as expected)\n")
    
    # Test 5: Enqueue and fail a job
    print("=" * 50)
    print("Test 5: Enqueue and fail a job")
    print("=" * 50)
    job_id = queue.enqueue("webhook", {
        "url": "http://httpstat.us/500",
        "data": {"message": "This will fail"}
    })
    print(f"Created job: {job_id}")
    
    job = queue.dequeue()
    print(f"Dequeued job: {job['id'][:8]}...")
    
    # The worker would process this and it would fail. Here we manually fail it for test simplicity.
    queue.fail_job(job['id'], "Simulated worker failure: Internal Server Error")
    print(f"Job marked as failed\n")
    
    # Test 6: Enqueue multiple jobs
    print("=" * 50)
    print("Test 6: Enqueue multiple webhook jobs")
    print("=" * 50)
    job_ids = []
    for i in range(3):
        job_id = queue.enqueue("webhook", {"url": f"http://httpstat.us/200?i={i}"})
        job_ids.append(job_id)
        print(f"Created job {i+1}: {job_id[:8]}...")
    
    print(f"\nAll {len(job_ids)} jobs enqueued")
    
    # Dequeue them all
    print("\nDequeuing all jobs:")
    for i in range(3):
        job = queue.dequeue()
        if job:
            print(f"  Job {i+1}: {job['type']} - {job['payload']}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
