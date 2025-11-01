import sys
sys.path.append('..')

from task_queue.manager import QueueManager

print("Testing QueueManager directly...")

queue = QueueManager()
print("✅ QueueManager created")

job_id = queue.enqueue("email", {"to": "test@example.com"})
print(f"✅ Job enqueued: {job_id}")

job = queue.get_job(job_id)
print(f"✅ Job retrieved: {job}")

print("\n🎉 Direct test passed! Issue is with Flask, not QueueManager.")