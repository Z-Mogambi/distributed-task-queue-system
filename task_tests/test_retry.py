import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from task_queue.manager import QueueManager


def main():
    print("Testing Retry Logic\n")

    queue = QueueManager()
    queue.redis.flushdb()
    print("Redis flushed — starting clean\n")

    max_retries = 3

    # Enqueue a calculation job and manually fail it to exercise retry/dead-letter logic
    job_id = queue.enqueue("calculation", {"numbers": [1, 2, 3]}, max_retries=max_retries)
    print(f"Submitted job: {job_id[:8]}")

    for attempt in range(1, max_retries + 2):
        job = queue.get_job(job_id)
        print(f"\n[Attempt {attempt}] Status: {job['status']}, Attempts so far: {job['attempts']}")

        if job["status"] in ("completed", "failed"):
            break

        # Dequeue and simulate a failure
        dequeued = queue.dequeue()
        if dequeued and dequeued["id"] == job_id:
            still_retrying = queue.fail_job(job_id, f"Simulated failure on attempt {attempt}")
            if not still_retrying:
                print(f"\nJob exhausted all {max_retries} retries — moved to dead-letter queue.")
                break
            else:
                # Move the delayed job immediately back to pending so the test doesn't have to wait
                queue.redis.zrem(queue.delayed_queue_key, job_id)
                queue.redis.lpush(queue.queue_key, job_id)
                # Reset status so it can be dequeued again
                job_data = queue.get_job(job_id)
                job_data["status"] = "pending"
                import json
                queue.redis.hset(f"job:{job_id}", "data", json.dumps(job_data))
        else:
            print("Could not dequeue expected job — is another worker running?")
            break

    final = queue.get_job(job_id)
    print(f"\nFinal state — Status: {final['status']}, Attempts: {final['attempts']}")
    print(f"Last error: {final.get('last_error')}")

    stats = queue.get_stats()
    print(f"\nQueue stats: {stats}")


if __name__ == "__main__":
    main()
