"""
Course: CSE 351 
Lesson: L03 team activity
File:   team.py
Author: <Add name here>

Purpose: Retrieve Star Wars details from a server

Instructions:

- This program requires that the server.py program be started in a terminal window.
- The program will retrieve the names of:
    - characters
    - planets
    - starships
    - vehicles
    - species

- the server will delay the request by 0.5 seconds

TODO
- Create a threaded function to make a call to the server where
  it retrieves data based on a URL.  The function should have a method
  called get_name() that returns the name of the character, planet, etc...
- The threaded function should only retrieve one URL.
- Create a queue that will be used between the main thread and the threaded functions

- Speed up this program as fast as you can by:
    - creating as many as you can
    - start them all
    - join them all

"""

from datetime import datetime, timedelta
import threading
import queue

from common import *

# Include cse 351 common Python files
from cse351 import *

# global

call_count = 0

def worker(q):
    """Threaded function that pulls URLs from the queue and fetches names."""
    global call_count
    while True:
        url = q.get()                    # Get work from queue (blocks if empty)
        if url is None:                  # Sentinel value = stop
            q.task_done()
            break
        
        item = get_data_from_server(url)
        call_count += 1
        print(f" - {item['name']}")
        
        q.task_done()                    # Tell queue we're done with this item

def main():
    global call_count
    log = Log(show_terminal=True)
    log.start_timer('Starting to retrieve data from the server')

    # Get film 6 data (this is still sequential - only one call)
    film6 = get_data_from_server(f'{TOP_API_URL}/films/6')
    call_count += 1
    print_dict(film6)

    # Create the shared queue
    work_queue = queue.Queue()

    # Create worker threads (you can increase this number for more speed)
    NUM_WORKERS = 15
    threads = []
    for _ in range(NUM_WORKERS):
        t = threading.Thread(target=worker, args=(work_queue,))
        threads.append(t)
        t.start()

    # Put ALL URLs into the queue (main thread does this quickly)
    categories = ['characters', 'planets', 'starships', 'vehicles', 'species']
    for kind in categories:
        urls = film6[kind]
        for url in urls:
            work_queue.put(url)

    # Put sentinel values so each worker knows when to stop
    for _ in range(NUM_WORKERS):
        work_queue.put(None)

    # Wait for all workers to finish
    for t in threads:
        t.join()

    log.stop_timer('Total Time To complete')
    log.write(f'There were {call_count} calls to the server')

if __name__ == "__main__":
    main()