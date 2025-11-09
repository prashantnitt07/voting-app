"""
app.py
-----------------------------
A simple Flask-based voting app with Prometheus metrics integration.

Endpoints:
  - GET  /        -> HTML form to vote
  - POST /vote    -> Submit a vote
  - GET  /result  -> Get current voting results (JSON)
  - GET  /metrics -> Expose Prometheus metrics

Metrics exposed:
  - voting_app_request_count{endpoint, method}
  - voting_app_response_time_seconds{endpoint}
"""

from flask import Flask, request, jsonify, Response
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Create Flask app
app = Flask(__name__)

# ---------------------------
# Prometheus Metrics
# ---------------------------

# Counter: Count total requests per endpoint and method
REQUEST_COUNT = Counter(
    'voting_app_request_count',
    'Total number of HTTP requests by endpoint and method',
    ['endpoint', 'method']
)

# Histogram: Track response time in seconds per endpoint
RESPONSE_TIME = Histogram(
    'voting_app_response_time_seconds',
    'Response time in seconds by endpoint',
    ['endpoint']
)

# ---------------------------
# In-memory vote store
# ---------------------------
votes = {"Python": 0, "Java": 0, "Go": 0}

# ---------------------------
# Decorator to measure metrics
# ---------------------------
def track_metrics(endpoint_name):
    """Decorator to count and measure request metrics"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            REQUEST_COUNT.labels(endpoint=endpoint_name, method=request.method).inc()
            start = time.time()
            response = func(*args, **kwargs)
            duration = time.time() - start
            RESPONSE_TIME.labels(endpoint=endpoint_name).observe(duration)
            return response
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# ---------------------------
# Routes
# ---------------------------

@app.route("/", methods=["GET"])
@track_metrics(endpoint_name="/")
def home():
    """Show a simple HTML form"""
    return """
    <h2>Vote for your favorite language</h2>
    <form action="/vote" method="post">
        <input type="radio" name="language" value="Python"> Python<br>
        <input type="radio" name="language" value="Java"> Java<br>
        <input type="radio" name="language" value="Go"> Go<br>
        <input type="submit" value="Vote">
    </form>
    <br>
    <a href='/result'>View Results (JSON)</a>
    """

@app.route("/vote", methods=["POST"])
@track_metrics(endpoint_name="/vote")
def vote():
    """Register a vote"""
    language = request.form.get("language") or (request.json or {}).get("language")
    if not language:
        return jsonify({"error": "No language provided"}), 400
    if language not in votes:
        return jsonify({"error": f"Invalid choice. Valid: {list(votes.keys())}"}), 400

    votes[language] += 1
    return jsonify({"message": f"Vote for {language} recorded!", "votes": votes}), 200

@app.route("/result", methods=["GET"])
@track_metrics(endpoint_name="/result")
def result():
    """Return current voting results"""
    return jsonify(votes), 200

@app.route("/metrics", methods=["GET"])
def metrics():
    """Expose Prometheus metrics"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# ---------------------------
# Entry point (for local testing)
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
