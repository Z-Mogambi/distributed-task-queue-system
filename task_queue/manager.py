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
        self.delayed_queue_key = "queue:delayed"
    
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

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the queues."""
        return {
            "pending": self.redis.llen(self.queue_key),
            "delayed": self.redis.zcard(self.delayed_queue_key),
            "dead_letter": self.redis.llen("queue:dead_letter")
        }

    def requeue_delayed_jobs(self) -> int:
        """Move jobs from delayed queue back to pending if their retry time has come."""
        now = time.time()
        
        # This Lua script atomically moves ready jobs from the delayed zset to the pending list.
        lua_script = """
            local jobs = redis.call('zrangebyscore', KEYS[1], '-inf', ARGV[1])
            if #jobs == 0 then return 0 end
            redis.call('zrem', KEYS[1], unpack(jobs))
            redis.call('lpush', KEYS[2], unpack(jobs))
            return #jobs
        """
        try:
            # redis-py eval signature: script, numkeys, *keys_and_args
            requeued_count = self.redis.eval(lua_script, 2, self.delayed_queue_key, self.queue_key, now)
            return requeued_count or 0
        except Exception:
            # Fallback for older Redis versions or other issues.
            job_ids = self.redis.zrangebyscore(self.delayed_queue_key, 0, now)
            if not job_ids:
                return 0
            pipe = self.redis.pipeline()
            pipe.zrem(self.delayed_queue_key, *job_ids)
            pipe.lpush(self.queue_key, *job_ids)
            results = pipe.execute()
            return results[1] # Return count from lpush
    
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
            # Exponential backoff delay in seconds
            base_delay_s = 1
            max_delay_s = 60
            jitter_s = random.uniform(0, 1)
            delay_s = min(
                (base_delay_s * (2 ** (current_attempts - 1))) + jitter_s, 
                max_delay_s
            )
            
            retry_at = time.time() + delay_s
            
            # Update job status and save it
            job_dict["status"] = "retrying"
            job_dict["retry_at"] = retry_at
            self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))

            # Add to delayed queue (sorted set) to be picked up later
            self.redis.zadd(self.delayed_queue_key, {job_id: retry_at})

            print(f"Job {job_id[:8]} failed (attempt {current_attempts}/{max_retries}). Retrying in {delay_s:.2f}s...")
            return True
        else:
            # Job has failed permanently
            job_dict["status"] = "failed"
            job_dict["failed_at"] = int(time.time())

            self.redis.hset(f"job:{job_id}", "data", json.dumps(job_dict))
            
            # Move to dead-letter queue
            self.redis.lpush("queue:dead_letter", job_id)

            print(f"Job {job_id[:8]} permanently failed after {current_attempts} attempts.")
            return False
