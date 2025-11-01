from flask import Flask, request, jsonify
import time
import sys

sys.path.append('..')

from task_queue.manager import QueueManager

app = Flask(__name__)
queue = QueueManager()

@app.route('/health', methods=['GET'])
def health():
    #health check
    return jsonify({
        "status": "healthy",
        "service": "task-queue_api"
    }), 200

@app.route('/jobs', methods=['POST'])
def create_job():
    """Submit a new job."""
    print("got a POST request to /jobs") #debug

    data = request.get_json()
    print(f"request data: {data}") #debug

    if not data:
        return jsonify({"error": "request body must be json"}), 400
    #validating 'type' and 'payload exist'
    job_type = data.get('type')
    payload = data.get('payload')
    print(f"job type: {job_type}, payload: {payload}") #debug

    if not job_type:
        return jsonify({"error": "missing required field: 'type'"}), 400
    if not payload:
        return jsonify({"error": "missing required field: 'payload'"}), 400
    
    #validate if job_type is supported?

    #enqueueing the job
    try:
        print("about to enqueu job") #debug
        job_id = queue.enqueue(job_type, payload)
        print(f"job enqueued with ID: {job_id}") #debug
        return jsonify({
            "job_id": job_id,
            "status": "queued"
        }), 201
    except Exception as e:
        print(f"error enqueueing: {e}") #debug
        return jsonify({"error": f"failed to enqueue job: {str(e)}"}), 500
    

@app.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """ Get job status """

    job = queue.get_job(job_id)
    if job is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Get queue metrics by counting jobs in pending queue, returning JSON with queue depth
    and status 200
    """
    pending_count = queue.redis.llen("jobs:pending")
    return jsonify({
        "pending": pending_count,
        "timestamp": int(time.time())
    }), 200

if __name__ == '__main__':
    print("\nStarting Task Queue API...")
    print("API running on http://localhost:5000")
    print("\nEndpoints:")
    print("  POST   /jobs       - Submit job")
    print("  GET    /jobs/:id   - Get job status")
    print("  GET    /health     - Health check")
    print("  GET    /metrics    - Queue stats")
    app.run(debug=True, port=5000)