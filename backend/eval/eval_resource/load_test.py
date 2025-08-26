import requests
import time
import threading

URL = "http://localhost:30080"  # NodePort for test-app
CONCURRENCY = 20                # number of parallel threads
DURATION = 60                   # test duration in seconds

def worker():
    while True:
        try:
            requests.get(URL, timeout=2)
        except:
            pass

threads = []
start = time.time()
for i in range(CONCURRENCY):
    t = threading.Thread(target=worker)
    t.daemon = True
    threads.append(t)
    t.start()

print(f"Running load test for {DURATION} seconds with {CONCURRENCY} threads...")
time.sleep(DURATION)
print("Load test finished.")
