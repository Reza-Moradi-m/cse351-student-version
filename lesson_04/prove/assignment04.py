"""
Course    : CSE 351
Assignment: 04
Student   : <your name here>

Instructions:
    - review instructions in the course

In order to retrieve a weather record from the server, Use the URL:

f'{TOP_API_URL}/record/{name}/{recno}

where:

name: name of the city
recno: record number starting from 0

"""

import time
import random
from common import *

from cse351 import *

THREADS = 200
WORKERS = 15
RECORDS_TO_RETRIEVE = 5000  # Don't change


# ---------------------------------------------------------------------------
def queue_put(queue, item, empty_semaphore, full_semaphore, lock):
    empty_semaphore.acquire()
    with lock:
        queue.put(item)
    full_semaphore.release()


# ---------------------------------------------------------------------------
def queue_get(queue, empty_semaphore, full_semaphore, lock):
    full_semaphore.acquire()
    with lock:
        item = queue.get()
    empty_semaphore.release()
    return item


# ---------------------------------------------------------------------------
def retrieve_weather_data(command_queue, data_queue, command_empty, command_full, command_lock, data_empty, data_full, data_lock):
    while True:
        command = queue_get(command_queue, command_empty, command_full, command_lock)

        if command is None:
            break

        city, recno = command
        url = f'{TOP_API_URL}/record/{city}/{recno}'
        data = get_data_from_server(url)

        if data and data.get('status') == 'OK':
            queue_put(data_queue, (city, data['date'], data['temp']), data_empty, data_full, data_lock)


# ---------------------------------------------------------------------------
# TODO - Create Worker threaded class
class Worker(threading.Thread):

    def __init__(self, data_queue, noaa, data_empty, data_full, data_lock):
        threading.Thread.__init__(self)
        self.data_queue = data_queue
        self.noaa = noaa
        self.data_empty = data_empty
        self.data_full = data_full
        self.data_lock = data_lock

    def run(self):
        while True:
            item = queue_get(self.data_queue, self.data_empty, self.data_full, self.data_lock)

            if item is None:
                break

            city, date, temp = item
            self.noaa.add_temp(city, temp)


# ---------------------------------------------------------------------------
# TODO - Complete this class
class NOAA:

    def __init__(self):
        self.temps = {city: [] for city in CITIES}
        self.lock = threading.Lock()

    def add_temp(self, city, temp):
        with self.lock:
            if city in self.temps:
                self.temps[city].append(temp)

    def get_temp_details(self, city):
        with self.lock:
            temps = self.temps.get(city, [])
            if not temps:
                return 0.0
            return sum(temps) / len(temps)


# ---------------------------------------------------------------------------
class Queue351():
    """ This is the queue object to use for this class. Do not modify!! """

    def __init__(self):
        self.__items = []
   
    def put(self, item):
        assert len(self.__items) <= 10
        self.__items.append(item)

    def get(self):
        return self.__items.pop(0)

    def get_size(self):
        """ Return the size of the queue like queue.Queue does -> Approx size """
        extra = 1 if random.randint(1, 50) == 1 else 0
        if extra > 0:
            extra *= -1 if random.randint(1, 2) == 1 else 1
        return len(self.__items) + extra


# ---------------------------------------------------------------------------
def verify_noaa_results(noaa):

    answers = {
        'sandiego': 14.5004,
        'philadelphia': 14.865,
        'san_antonio': 14.638,
        'san_jose': 14.5756,
        'new_york': 14.6472,
        'houston': 14.591,
        'dallas': 14.835,
        'chicago': 14.6584,
        'los_angeles': 15.2346,
        'phoenix': 12.4404,
    }

    print()
    print('NOAA Results: Verifying Results')
    print('===================================')
    for name in CITIES:
        answer = answers[name]
        avg = noaa.get_temp_details(name)

        if abs(avg - answer) > 0.00001:
            msg = f'FAILED  Expected {answer}'
        else:
            msg = f'PASSED'
        print(f'{name:>15}: {avg:<10} {msg}')
    print('===================================')


# ---------------------------------------------------------------------------
def main():

    log = Log(show_terminal=True, filename_log='assignment.log')
    log.start_timer()

    noaa = NOAA()

    # Start server
    data = get_data_from_server(f'{TOP_API_URL}/start')

    # Get all cities number of records
    print('Retrieving city details')
    city_details = {}
    name = 'City'
    print(f'{name:>15}: Records')
    print('===================================')
    for name in CITIES:
        city_details[name] = get_data_from_server(f'{TOP_API_URL}/city/{name}')
        print(f'{name:>15}: Records = {city_details[name]["records"]:,}')
    print('===================================')

    records = RECORDS_TO_RETRIEVE

    # TODO - Create any queues, semaphores, locks or barriers you need
    command_queue = Queue351()
    data_queue = Queue351()

    command_empty = threading.Semaphore(10)
    command_full = threading.Semaphore(0)
    command_lock = threading.Lock()

    data_empty = threading.Semaphore(10)
    data_full = threading.Semaphore(0)
    data_lock = threading.Lock()

    retrieve_threads = []
    for _ in range(THREADS):
        t = threading.Thread(
            target=retrieve_weather_data,
            args=(command_queue, data_queue, command_empty, command_full, command_lock, data_empty, data_full, data_lock)
        )
        retrieve_threads.append(t)
        t.start()

    worker_threads = []
    for _ in range(WORKERS):
        t = Worker(data_queue, noaa, data_empty, data_full, data_lock)
        worker_threads.append(t)
        t.start()

    for name in CITIES:
        for recno in range(records):
            queue_put(command_queue, (name, recno), command_empty, command_full, command_lock)

    for _ in range(THREADS):
        queue_put(command_queue, None, command_empty, command_full, command_lock)

    for t in retrieve_threads:
        t.join()

    for _ in range(WORKERS):
        queue_put(data_queue, None, data_empty, data_full, data_lock)

    for t in worker_threads:
        t.join()

    # End server - don't change below
    data = get_data_from_server(f'{TOP_API_URL}/end')
    print(data)

    verify_noaa_results(noaa)

    log.stop_timer('Run time: ')


if __name__ == '__main__':
    main()