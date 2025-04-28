from prometheus_client import Counter, Histogram, Gauge, Summary

class Metrics:
    def __init__(self):
        # User metrics
        self.user_created = Counter('user_created_total', 'Total number of users created')
        self.user_updated = Counter('user_updated_total', 'Total number of users updated')
        self.user_deleted = Counter('user_deleted_total', 'Total number of users deleted')
        
        # Validation metrics
        self.validation_attempts = Counter('validation_attempts_total', 'Total number of validation attempts',
                                         ['validation_type'])  # cnpj or cep
        self.validation_errors = Counter('validation_errors_total', 'Total number of validation errors',
                                       ['validation_type', 'error_type'])
        
        # Performance metrics
        self.request_latency = Histogram('request_duration_seconds', 'Request latency in seconds',
                                       ['endpoint'], buckets=[0.1, 0.5, 1, 2, 5])
        self.response_size = Summary('response_size_bytes', 'Response size in bytes',
                                   ['endpoint'])
        
        # Resource metrics
        self.active_requests = Gauge('active_requests', 'Number of active requests',
                                   ['endpoint'])
        self.db_connections = Gauge('db_connections_active', 'Number of active database connections')
        
        # API metrics
        self.api_requests = Counter('api_requests_total', 'Total API requests',
                                  ['method', 'endpoint', 'status'])
        self.api_errors = Counter('api_errors_total', 'Total API errors',
                                ['endpoint', 'error_type'])

    # User metrics methods
    def inc_user_created(self):
        self.user_created.inc()

    def inc_user_updated(self):
        self.user_updated.inc()

    def inc_user_deleted(self):
        self.user_deleted.inc()

    # Validation metrics methods
    def inc_validation_attempt(self, validation_type: str):
        self.validation_attempts.labels(validation_type=validation_type).inc()

    def inc_validation_error(self, validation_type: str, error_type: str):
        self.validation_errors.labels(validation_type=validation_type, error_type=error_type).inc()

    # Performance tracking methods
    def observe_request_latency(self, endpoint: str, duration: float):
        self.request_latency.labels(endpoint=endpoint).observe(duration)

    def observe_response_size(self, endpoint: str, size: int):
        self.response_size.labels(endpoint=endpoint).observe(size)

    # Resource tracking methods
    def inc_active_requests(self, endpoint: str):
        self.active_requests.labels(endpoint=endpoint).inc()

    def dec_active_requests(self, endpoint: str):
        self.active_requests.labels(endpoint=endpoint).dec()

    def set_db_connections(self, count: int):
        self.db_connections.set(count)

    # API metrics methods
    def inc_api_request(self, method: str, endpoint: str, status: int):
        self.api_requests.labels(method=method, endpoint=endpoint, status=status).inc()

    def inc_api_error(self, endpoint: str, error_type: str):
        self.api_errors.labels(endpoint=endpoint, error_type=error_type).inc()

metrics = Metrics() 