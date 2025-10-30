import redis
import json
import uuid
import time
from typing import Optional, Dict, Any

class QueueManager:
    def __init__(self, host='localhost', port=6379):
        """Connect to Redis."""
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
        self.queue_key = "jobs:pending"
    
    def enqueue(self, job_type: str, payload: Dict[str, Any]) -> str:
        """
        Add a job to the queue.
        
        TODO for you:
        1. Generate a unique job_id (use uuid.uuid4())
        2. Create a job dict with: id, type, payload, status="pending", created_at
        3. Store job data: redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
        4. Add job_id to queue: redis.lpush(self.queue_key, job_id)
        5. Return job_id
        """
        #my code
        job_id = uuid.uuid4()
        
        job_dict = {
            "id": str(job_id),
            "type": job_type,
            "payload": payload,
            "status": "pending",
            "created_at": int(time.time())
        }
        
        self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
        
        self.redis.lpush(self.queue_key, job_id)
        
        return str(job_id)
        
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get next job from queue (blocking with 5 second timeout).
        
        TODO for you:
        1. Pop job_id from queue: redis.brpop(self.queue_key, timeout=5)
        2. If None (queue empty), return None
        3. Get job data: redis.hget(f"job:{job_id}", "data")
        4. Parse JSON: job_dict = json.loads(job_data)
        5. Update status to "processing" (we'll keep it simple for now)
        6. Return job_dict
        """
        # my code
        result = self.redis.brpop(self.queue_key, timeout=5)
        
        if result is None:
            return None
            
        queue_name, job_id = result
            
        job_data = self.redis.hget(f"job:{job_id}", "data")
        job_dict = json.loads(job_data)
        
        job_dict["status"] = "processing"
        job_dict["started_at"] = int(time.time())
        
        self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
        return job_dict
        
    
    def complete_job(self, job_id: str, result: Any) -> bool:
        """
        Mark job as completed.
        
        TODO for you:
        1. Get current job data from redis
        2. Update status to "completed"
        3. Add result and completed_at timestamp
        4. Save back to redis
        5. Return True
        """
        # my code
        job_data = self.redis.hget(f"job:{job_id}", "data")
        job_dict = json.loads(job_data)
        
        job_dict["status"] = "completed"
        job_dict["result"] = result
        job_dict["completed_at"] = int(time.time())
        
        self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
        
        return True
    
    def fail_job(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed.
        
        TODO for you:
        1. Get current job data
        2. Update status to "failed"
        3. Add error message
        4. Save back to redis
        5. Return True
        
        (We'll add retry logic later)
        """
        # my code
        job_data = self.redis.hget(f"job:{job_id}", "data")
        job_dict = json.loads(job_data)
        
        job_dict["status"] = "failed"
        job_dict["error"] = error
        job_dict["failed_at"] = int(time.time())
        
        self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
        return True
