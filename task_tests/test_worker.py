import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from task_queue.manager import QueueManager


JOBS = [
    ("email",            {"to": "worker-test@example.com", "subject": "Worker Test", "body": "Batch test"}),
    ("image_processing", {"image_url": "https://picsum.photos/1200/800", "operations": ["resize", "compress"]}),
    ("calculation",      {"numbers": list(range(1, 101))}),
    ("document_summary", {"url": "https://en.wikipedia.org/wiki/Distributed_computing"}),
]


def main():
    print("Starting Worker Scale Test\n")

    queue = QueueManager()
    queue.redis.flushdb()
    print("Redis flushed — starting clean\n")

    num_jobs = 40  # 10 of each type

    print(f"Submitting {num_jobs} jobs (10 of each type)...")

    start_time = time.time()
    for i in range(num_jobs):
        job_type, payload = JOBS[i % len(JOBS)]
        job_id = queue.enqueue(job_type, payload)
        print(f"  [{i+1}/{num_jobs}] {job_type}: {job_id[:12]}...")

    duration = time.time() - start_time
    print(f"\nAll {num_jobs} jobs submitted in {duration:.2f}s ({num_jobs / duration:.2f} jobs/sec)")

    stats = queue.get_stats()
    print(f"Queue stats: {stats}")
    print("\nStart worker(s) to process them and observe throughput.")


if __name__ == "__main__":
    main()
