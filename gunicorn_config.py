"""
Gunicorn configuration file for rpi-epd-server
"""

import multiprocessing
import os
from logger import setup_logging

# Server socket
bind = f"{os.getenv('FLASK_HOST', '0.0.0.0')}:{os.getenv('FLASK_PORT', '5000')}"

# Worker processes
# Use 1 worker for e-ink display to avoid concurrent display access issues
workers = 1

# Worker class
worker_class = "sync"

# Timeout for requests (in seconds)
# Set higher timeout for display operations which may take several seconds
timeout = 120

# Logging
loglevel = "info"
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'


def on_starting(server):
    """Called just before the master process is initialized."""
    setup_logging()


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    setup_logging()

# Process naming
proc_name = "rpi-epd-server"

# Daemon mode
daemon = False

# Preload app for faster worker spawning
preload_app = True

# Restart workers after this many requests (to prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50
