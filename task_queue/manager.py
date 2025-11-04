import random
import redis
import json
import uuid
import time
import os
from typing import Optional, Dict, Any

class QueueManager:
    def __init__(self, host=None, port=None):
        """Connect to Redis."""
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            redis_host = host or os.getenv('REDIS_HOST', 'localhost')
            redis_port = port or int(os.getenv('REDIS_PORT', 6379))

            self.redis = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True
            )
        self.queue_key = "queue:pending"
    
    def enqueue(self, job_type: str, payload: Dict[str, Any], max_retries: int=3) -> str:
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
            "created_at": int(time.time()),
            "attempts": 0,
            "max_retries": max_retries,
            "last_error": None
        }
        
        self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
        
        self.redis.lpush(self.queue_key, str(job_id))
        
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
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """get job data by ID"""
        job_data = self.redis.hget(f"job:{job_id}", "data")

        if job_data is None:
            return None
        return json.loads(job_data)
    
    def fail_job(self, job_id: str, error: str) -> bool:
        """marking job as failed and retrying in under max_retries"""

        job_data = self.redis.hget(f"job:{job_id}", "data")
        job_dict = json.loads(job_data)

        #increment attemps
        job_dict["attempts"] += 1
        current_attempts = job_dict["attempts"]
        max_retries = job_dict.get("max_retries", 3)

        job_dict["last_error"] = {
            "message": error,
            "timestamp": int(time.time()),
            "attempt": current_attempts
        }
        
        #retry logic
        if current_attempts < max_retries:
            #exponential backoff delay
            base_delay = 1000
            max_delay = 6000
            jitter = random.uniform(0, 1000)
            delay = min((base_delay * (2 ** current_attempts)) + jitter, max_delay)
            
            #updating status and saving updated job
            job_dict["status"] = "retrying"
            job_dict["retry_at"] = time.time() + (delay/1000)
            self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))

            time.sleep(delay/1000)
            
            self.redis.lpush(self.queue_key, job_id)

            print(f"job {job_id[:8]} failed (attempt {current_attempts}/{max_retries}). Retrying...")
            return True
        else:
            job_dict["status"] = "failed"
            job_dict["failed_at"] = int(time.time())

            self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
            self.redis.lpush("queue:dead_letter", job_id)

            print(f"Job {job_id[:8]}, parmanently failed after {current_attempts} attemps")
            return False
