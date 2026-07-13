# DDoS Protection and Malicious Request Filtering

from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Rate limiting configuration
REQUEST_LIMIT = 100  # Max requests per minute
request_counts = {}
blocklist = set()

def is_blocked(ip):
    return ip in blocklist

def add_to_blocklist(ip):
    blocklist.add(ip)

def clear_old_requests():
    current_time = time.time()
    for ip in list(request_counts.keys()):
        request_counts[ip] = [timestamp for timestamp in request_counts[ip] if current_time - timestamp < 60]
        if len(request_counts[ip]) == 0:
            del request_counts[ip]

@app.before_request
def limit_requests():
    ip = request.remote_addr
    clear_old_requests()
    
    if is_blocked(ip):
        return jsonify({"error": "Your IP has been blocked due to suspicious activity."}), 403

    if ip not in request_counts:
        request_counts[ip] = []
    
    request_counts[ip].append(time.time())
    
    if len(request_counts[ip]) > REQUEST_LIMIT:
        add_to_blocklist(ip)
        return jsonify({"error": "Too many requests. You have been blocked."}), 429

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"data": "This is protected data."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
