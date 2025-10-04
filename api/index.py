import json
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from mangum import Mangum

# Initialize the Flask application
app = Flask(__name__)

# Enable CORS for the /metrics endpoint to accept POST requests from any origin.
# This directly addresses the requirement: "Enable CORS for POST requests from any origin"
CORS(app, resources={r"/metrics": {"origins": "*"}})


@app.route('/metrics', methods=['POST'])
def get_metrics():
    """
    This endpoint calculates performance metrics for specified regions.
    It reads the request JSON, loads data from a file, calculates metrics,
    and returns them in the specified format.
    """
    try:
        # 1. Load the raw data from the JSON file
        with open('data.json', 'r') as f:
            all_records = json.load(f)

        # 2. Get the JSON body from the incoming POST request
        #    Example body: {"regions": ["apac", "emea"], "threshold_ms": 170}
        request_data = request.get_json()
        if not request_data or 'regions' not in request_data or 'threshold_ms' not in request_data:
            return jsonify({"error": "Invalid request body. 'regions' and 'threshold_ms' are required."}), 400

        requested_regions = request_data['regions']
        threshold_ms = request_data['threshold_ms']

        # 3. Process the data and calculate metrics for each requested region
        response_metrics = {}

        for region in requested_regions:
            # Filter the records for the current region
            region_records = [record for record in all_records if record.get('region') == region]

            # If no records found for this region, skip it
            if not region_records:
                continue

            # Create lists of latencies and uptimes for easy calculation
            latencies = [r['latency_ms'] for r in region_records]
            uptimes = [r['uptime_percent'] for r in region_records]

            # Calculate the required metrics using numpy for efficiency
            # avg_latency (mean)
            # p95_latency (95th percentile)
            # avg_uptime (mean)
            # breaches (count of records above threshold)
            metrics = {
                "avg_latency": np.mean(latencies),
                "p95_latency": np.percentile(latencies, 95),
                "avg_uptime": np.mean(uptimes),
                "breaches": sum(1 for lat in latencies if lat > threshold_ms)
            }
            
            response_metrics[region] = metrics

        # 4. Return the results as a JSON response
        return jsonify(response_metrics)

    except FileNotFoundError:
        return jsonify({"error": "data.json not found on the server"}), 500
    except Exception as e:
        # Generic error handler for any other issues
        return jsonify({"error": str(e)}), 500


handler = Mangum(app)
