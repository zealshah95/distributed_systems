import requests
import code
import json
import random
import time
import threading
import multiprocessing
import logging
import matplotlib.pyplot as plt
import sys
import config

# Logging threads' status- creation, beginning, exiting, termination.
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s)'
                    )
# Feed in IP address and port number of front end server.
frontend_ip = config.FRONT_END_IP
frontend_port = config.FRONT_END_PORT


# Uses frontend's search API to look for books under a specific topic.
# Input: topic
# Output: JSON object containing relevant book titles, and
# their numbers.
def search(topic):
    r = requests.get('http://{}:{}/search/{}'.format(frontend_ip, frontend_port, topic))
    return r.json()


# Uses frontend's lookup API to look for details of a specific book
# by its book number.
# Input: book number.
# Output: JSON object containing relevant information like
# book cost, and stock count.
def lookup(item_number):
    t = requests.get('http://{}:{}/lookup/{}'.format(frontend_ip, frontend_port, item_number))
    return t.json()


# Uses frontend's buy API to send a buy request for a specific book.
# Input: book number.
# Output: Receives a message regarding the success or failure of
# requested transaction.
def buy(item_number):
    b = requests.get('http://{}:{}/buy/{}'.format(frontend_ip, frontend_port, item_number))
    return b.text


def client():
    while True:
        logging.debug('Starting')
        topic = random.choice(['distributed_systems', 'graduate_school'])
        search_output = search(topic)
        item_of_interest = random.choice(list(search_output['items'].values()))
        for name, number in search_output['items'].items():
            if number == item_of_interest:
                book_name = name
        lookup(item_of_interest)
        trans_results = buy(item_of_interest)
        logging.debug('Exiting')
        global stop_threads
        if stop_threads:
            break


# This code is used to evaluate performance of the system in terms of handling
# concurrent requests. We increase the number of clients making concurrent
# requests from 1 to 100. In the process, we record the average end-to-end response
# time observed for every group of clients. Plots, summary, and details of this
# experiment can be found in our lab 2 and lab 3 performance evaluation document.

if __name__ == '__main__':
    n = 0
    avg_resp_time = []
    while n <= 100:
        time_arr = []
        threads = []
        start = time.time()
        stop_threads = False
        for i in range(0, n):
            currentThread = threading.Thread(target=client)
            threads.append(currentThread)
            currentThread.start()
        # Trade-off: Once all the threads have been generated, we give them 0.5 seconds
        # time to finish their work. After 0.5 seconds, we kill all the threads.
        time.sleep(0.5)
        stop_threads = True
        for t in threads:
            t.join()
            # print('thread killed')
        end = time.time()
        time_arr.append(end - start)
        avg_resp_time.append(sum(time_arr) / float(len(time_arr)))
        n = n + 1
        # We introduce a delay of 0.15 seconds between consecutive sets of
        # concurrent requests.
        time.sleep(0.15)

    avg_resp_ops = []
    for i in range(0, 100, 10):
        avg_resp_ops.append(avg_resp_time[i])

    print(avg_resp_ops)
    fig_1 = plt.figure(1)
    plt.plot(avg_resp_time)
    plt.xlabel('Total Number of Clients Making Concurrent Requests')
    plt.ylabel('Average Response Time (s)')
    plt.title('Average End-to-End Response Time for Concurrent Requests')
    plt.savefig('concurrent_requests.png')
    plt.show()
