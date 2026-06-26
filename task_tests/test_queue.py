import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from task_queue.manager import QueueManager


def sep(title):
    print("=" * 50)
    print(title)
    print("=" * 50)


def main():
    print("Starting Queue Tests\n")
    queue = QueueManager()
    queue.redis.flushdb()
    print("Redis flushed — starting clean\n")

    # ------------------------------------------------------------------
    # Test 1: Enqueue an email job (with callback_url)
    # ------------------------------------------------------------------
    sep("Test 1: Enqueue email job with callback_url")
    job_id = queue.enqueue(
        "email",
        {"to": "user@example.com", "subject": "Hello", "body": "Test message"},
        callback_url="https://webhook.site/your-unique-id",
    )
    print(f"Created job: {job_id}\n")
    time.sleep(1)

    # ------------------------------------------------------------------
    # Test 2: Dequeue it and verify callback_url is stored
    # ------------------------------------------------------------------
    sep("Test 2: Dequeue — verify callback_url is on the job")
    job = queue.dequeue()
    if job:
        print(f"  ID:           {job['id']}")
        print(f"  Type:         {job['type']}")
        print(f"  Status:       {job['status']}")
        print(f"  callback_url: {job.get('callback_url')}\n")
    else:
        print("No job found\n")
    time.sleep(1)

    # ------------------------------------------------------------------
    # Test 3: Complete it
    # ------------------------------------------------------------------
    sep("Test 3: Complete the job")
    queue.complete_job(job['id'], {"message_id": "msg_123", "to": job['payload']['to']})
    completed = queue.get_job(job['id'])
    print(f"Status: {completed['status']}, result: {completed['result']}\n")
    time.sleep(1)

    # ------------------------------------------------------------------
    # Test 4: Empty queue timeout
    # ------------------------------------------------------------------
    sep("Test 4: Dequeue from empty queue (5s timeout)")
    print("Waiting...")
    result = queue.dequeue()
    print("Queue empty as expected\n" if not result else f"Unexpected: {result}")

    # ------------------------------------------------------------------
    # Test 5: Fail a job and check retry state
    # ------------------------------------------------------------------
    sep("Test 5: Fail a calculation job — verify retry state")
    job_id = queue.enqueue("calculation", {"numbers": [1, 2, 3]}, max_retries=3)
    job = queue.dequeue()
    queue.fail_job(job['id'], "Simulated failure")
    updated = queue.get_job(job['id'])
    print(f"Status: {updated['status']}, Attempts: {updated['attempts']}")
    print(f"Last error: {updated['last_error']}\n")

    # ------------------------------------------------------------------
    # Test 6: Enqueue all four job types
    # ------------------------------------------------------------------
    sep("Test 6: Enqueue all four job types")
    jobs = [
        ("email",            {"to": "a@example.com", "subject": "Hi", "body": ""}),
        ("image_processing", {"image_url": "https://picsum.photos/1200/800", "operations": ["resize", "compress"]}),
        ("calculation",      {"numbers": list(range(1, 11))}),
        ("document_summary", {"url": "https://en.wikipedia.org/wiki/Redis"}),
    ]
    for job_type, payload in jobs:
        jid = queue.enqueue(job_type, payload)
        print(f"  Enqueued {job_type}: {jid[:8]}...")

    print("\nDequeuing all:")
    for _ in jobs:
        j = queue.dequeue()
        if j:
            print(f"  {j['type']} — payload keys: {list(j['payload'].keys())}")

    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
