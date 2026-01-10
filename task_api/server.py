from flask import Flask, request, jsonify # type: ignore
import time
import sys

sys.path.append('..')

from task_queue.manager import QueueManager

app = Flask(__name__)
queue = QueueManager()

@app.route('/', methods=['GET'])
def dashboard():
    """Show a simple dashboard with queue stats."""
    stats = queue.get_stats()
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Task Queue Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }}
            h1 {{ color: #333; }}
            .stats-container {{ display: flex; gap: 20px; }}
            .stat-box {{ background-color: #fff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .stat-box h2 {{ margin-top: 0; color: #555; }}
            .stat-box .count {{ font-size: 3em; color: #007BFF; font-weight: bold; }}
            .timestamp {{ margin-top: 30px; font-size: 0.9em; color: #888; }}
        </style>
    </head>
    <body>
        <h1>Task Queue Dashboard</h1>
        <div class="stats-container">
            <div class="stat-box">
                <h2>Pending Jobs</h2>
                <div class="count">{stats['pending']}</div>
            </div>
            <div class="stat-box">
                <h2>Delayed Jobs</h2>
                <div class="count">{stats['delayed']}</div>
            </div>
            <div class="stat-box">
                <h2>Dead-Letter Jobs</h2>
                <div class="count">{stats['dead_letter']}</div>
            </div>
            <div class="stat-box">
                <h2>Completed Jobs</h2>
                <div class="count" style="color: #28a745;">{stats.get('completed', 0)}</div>
            </div>
            <div class="stat-box">
                <h2>Failed Jobs</h2>
                <div class="count" style="color: #dc3545;">{stats.get('failed', 0)}</div>
            </div>
        </div>
        <div class="timestamp">Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}</div>
    </body>
    </html>
    """
    return html, 200

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
            "status": "queued",
            "type": job_type
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
    print("API running on http://localhost:8000")
    print("\nEndpoints:")
    print("  GET    /           - Dashboard")
    print("  POST   /jobs       - Submit job")
    print("  GET    /jobs/:id   - Get job status")
    print("  GET    /health     - Health check")
    print("  GET    /metrics    - Queue stats")

    app.run(host="0.0.0.0", port=8000, debug=True)
