# app.py
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import logging, time
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

app = Flask(__name__)

# Structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'Request latency seconds', ['endpoint'])

# OpenTelemetry tracing (Console exporter for demo)
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)
FlaskInstrumentor().instrument_app(app)

@app.route('/')
def hello():
    start = time.time()
    with tracer.start_as_current_span("hello-handler"):
        REQUEST_COUNT.labels(request.method, '/', 200).inc()
        elapsed = time.time() - start
        REQUEST_LATENCY.labels('/').observe(elapsed)
        app.logger.info('hello served', extra={'path': '/', 'method': request.method})
        return jsonify({'message': 'Hello, DevOps!'}), 200

@app.route('/echo', methods=['POST'])
def echo():
    start = time.time()
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    payload = request.get_json()
    with tracer.start_as_current_span("echo-handler"):
        REQUEST_COUNT.labels(request.method, '/echo', 200).inc()
        REQUEST_LATENCY.labels('/echo').observe(time.time() - start)
        app.logger.info('echo', extra={'payload': payload})
        return jsonify({'you_sent': payload}), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
