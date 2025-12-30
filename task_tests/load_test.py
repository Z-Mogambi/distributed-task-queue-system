import requests
import time
import argparse
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://api:8000/jobs"

def submit_job(job_type, payload):
    """Submits a single job to the API and returns the response time and status."""
    start_time = time.time()
    try:
        response = requests.post(API_URL, json={"type": job_type, "payload": payload}, timeout=10)
        duration = time.time() - start_time
        if response.status_code == 201:
            return (True, duration)
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return (False, duration)
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        print(f"Request failed: {e}")
        return (False, duration)

def main():
    parser = argparse.ArgumentParser(description="Task Queue Load Tester.")
    parser.add_argument("--num-jobs", type=int, default=1000, help="Total number of jobs to submit.")
    parser.add_argument("--concurrency", type=int, default=50, help="Number of concurrent clients.")
    parser.add_argument("--job-type", type=str, default="webhook", choices=["webhook", "flaky_service"], help="Type of job to submit.")
    args = parser.parse_args()

    print(f"Starting load test with {args.num_jobs} '{args.job_type}' jobs using {args.concurrency} concurrent clients...")

    # Payloads for different job types
    payloads = {
        "webhook": {"url": "http://httpstat.us/200"},
        "flaky_service": {"url": "http://httpstat.us/200"}  # Success URL
    }

    job_type = args.job_type
    payload = payloads[job_type]
    
    success_count = 0
    error_count = 0
    total_time = 0

    overall_start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        # Submit all jobs
        futures = [executor.submit(submit_job, job_type, payload) for _ in range(args.num_jobs)]
        
        for i, future in enumerate(as_completed(futures)):
            success, duration = future.result()
            if success:
                success_count += 1
            else:
                error_count += 1
            total_time += duration
            
            # Print progress
            print(f"\rProgress: {i + 1}/{args.num_jobs} (Success: {success_count}, Errors: {error_count})", end="")

    overall_duration = time.time() - overall_start_time
    
    print("\n\n" + "=" * 50)
    print("Load Test Summary")
    print("=" * 50)
    print(f"Total jobs submitted: {args.num_jobs}")
    print(f"Concurrency level:    {args.concurrency}")
    print(f"Successful requests:  {success_count}")
    print(f"Failed requests:      {error_count}")
    
    if success_count > 0:
        avg_latency = (total_time / success_count) * 1000
        print(f"Average latency:      {avg_latency:.2f} ms")
    
    if overall_duration > 0:
        jobs_per_sec = success_count / overall_duration
        print(f"Throughput:           {jobs_per_sec:.2f} jobs/sec")
    print("=" * 50)
    print("\nCheck the dashboard at http://localhost:8000 to see job processing status.")

if __name__ == "__main__":
    main()
