import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 30
accesslog = "/var/log/beslove/access.log"
errorlog = "/var/log/beslove/error.log"
loglevel = "info"
