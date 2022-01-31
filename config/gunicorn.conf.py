import multiprocessing

# Server Socket
bind = "0.0.0.0:8080"

# Worker Processes
threads = multiprocessing.cpu_count() * 2 + 1
timeout = 3600

# Logging
loglevel = 'info'
accesslog = '/var/log/gunicorn-access.log'
errorlog = '/var/log/gunicorn-error.log'