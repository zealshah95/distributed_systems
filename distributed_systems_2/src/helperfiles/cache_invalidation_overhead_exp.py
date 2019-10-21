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


# Client makes n sequential requests. Parameters for every request like topic, book number
# are selected at random. Regardless of the stock availability,
# the client attempts to buy a book in every request. This code serves one performance
# evaluation experiment: Evaluation of overhead due to cache invalidation. This program's
# output is an end to end buy request response time graph. The invalidation time
# graph is obtained using front end server.

if __name__ == '__main__':
    i = 0
    buy_r = []
    n = 50
    while i <= n:
        print(i)
        topic = random.choice(['distributed_systems', 'graduate_school'])
        search_output = search(topic)
        item_of_interest = random.choice(list(search_output['items'].values()))

        lookup(item_of_interest)

        trans_start = time.time()
        # buy regardless of the stock value returned by the lookup query.
        # NOTE: Test to check the output when client requests buy() even if
        # the stock was empty.
        trans_results = buy(item_of_interest)
        trans_end = time.time()

        buy_r.append(trans_end - trans_start)

        i = i + 1
        time.sleep(0.15)  # This delay can be removed

    r = range(len(buy_r))
    avg_buy_time = [sum(buy_r) / float(len(buy_r))] * len(r)


    print("Average buy response time: {} seconds".format(avg_buy_time[0]))

    fig_1 = plt.figure(1)
    plt.plot(r, buy_r, 'r', avg_buy_time, 'b')
    plt.xlabel('Request Number')
    plt.ylabel('Buy Request Response Time(s)')
    plt.title('Response-time for {} Buy Requests (includes Verification Query & Update)'.format(n))
    plt.gca().legend(('Actual Response Time', 'Average Response Time'))
    plt.savefig('buy_request.png')
    plt.show()

