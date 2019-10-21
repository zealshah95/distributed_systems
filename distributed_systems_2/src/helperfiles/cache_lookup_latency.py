import requests
import code
import json
import random
import time
import matplotlib.pyplot as plt
import numpy as np
import socket
import config

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
    return b.json()


# Client makes n sequential lookup requests. Parameters for every request like topic, book number
# are selected at random. This code serves one performance
# evaluation experiment: Evaluation of cache consistency overhead. The output will
# show peaks only for cache misses. It plots the end to end time of 50 lookup requests made
# by the client. Peaks in the output will denote cache misses.

if __name__ == '__main__':
    i = 0
    search_r = []
    lookup_r = []
    buy_r = []
    end_to_end_r = []
    n = 1000
    while i <= n:
        print(i)
        topic = random.choice(['distributed_systems', 'graduate_school'])

        search_start = time.time()
        search_output = search(topic)
        search_end = time.time()

        item_of_interest = random.choice(list(search_output['items'].values()))


        lookup_start = time.time()
        lookup(item_of_interest)
        lookup_end = time.time()


        search_r.append(search_end - search_start)
        lookup_r.append(lookup_end - lookup_start)

        i = i + 1

        time.sleep(0.15)  # This delay can be removed

    r = range(len(search_r))
    avg_search_time = [sum(search_r) / float(len(search_r))] * len(r)
    avg_lookup_time = [sum(lookup_r) / float(len(lookup_r))] * len(r)

    print("Average search response time: {} seconds".format(avg_search_time[0]))
    print("Average lookup response time: {} seconds".format(avg_lookup_time[0]))


    fig_1 = plt.figure(1)
    plt.plot(r, search_r, 'r', avg_search_time, 'b')
    plt.xlabel('Request Number')
    plt.ylabel('Search Query Response Time(s)')
    plt.title('Response-time for {} Search Requests'.format(n))
    plt.gca().legend(('Actual Response Time', 'Average Response Time'))
    plt.savefig('search_request.png')

    fig_2 = plt.figure(2)
    plt.plot(r, lookup_r, 'r', avg_lookup_time, 'b')
    plt.xlabel('Request Number')
    plt.ylabel('Lookup Query Response Time(s)')
    plt.title('Response-time for {} Lookup Requests'.format(n))
    plt.gca().legend(('Actual Response Time', 'Average Response Time'))
    plt.savefig('lookup_request.png')
    plt.show()
