import requests
import code
import json
import random
import time
import matplotlib.pyplot as plt
import numpy as np
import socket

# Feed in IP address and port number of front end server.
frontend_ip = "128.119.243.168"
frontend_port = 12346


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
# the client attempts to buy a book in every request. This code serves four performance
# evaluation experiments for sequential requests: (1) End to end response time,
# (2) Search request response time, (3) Lookup request response time,
# (4) Buy request response time. Details regarding each experiment and their summary can
# be found in our lab 2 performance evaluation documentation.

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

        end_to_end_start = time.time()
        search_start = time.time()
        search_output = search(topic)
        search_end = time.time()

        book_1, book_2 = search_output['items'].values()
        item_of_interest = random.choice([book_1, book_2])
        for name, number in search_output['items'].items():
            if number == item_of_interest:
                book_name = name

        lookup_start = time.time()
        lookup(item_of_interest)
        lookup_end = time.time()

        trans_start = time.time()
        # buy regardless of the stock value returned by the lookup query.
        # NOTE: Test to check the output when client requests buy() even if
        # the stock was empty.
        trans_results = buy(item_of_interest)
        trans_end = time.time()

        end_to_end_end = time.time()

        search_r.append(search_end - search_start)
        lookup_r.append(lookup_end - lookup_start)
        buy_r.append(trans_end - trans_start)
        end_to_end_r.append(end_to_end_end - end_to_end_start)

        i = i + 1
        print(trans_results)
        if trans_results == "Transaction successful.":
            print("Bought book {}".format(book_name))
        time.sleep(0.15)  # This delay can be removed

    r = range(len(search_r))
    avg_search_time = [sum(search_r) / float(len(search_r))] * len(r)
    avg_lookup_time = [sum(lookup_r) / float(len(lookup_r))] * len(r)
    avg_buy_time = [sum(buy_r) / float(len(buy_r))] * len(r)
    avg_e2e_time = [sum(end_to_end_r) / float(len(end_to_end_r))] * len(r)

    print("Average search response time: {} seconds".format(avg_search_time[0]))
    print("Average lookup response time: {} seconds".format(avg_lookup_time[0]))
    print("Average buy response time: {} seconds".format(avg_buy_time[0]))
    print("Average e2e response time: {} seconds".format(avg_e2e_time[0]))

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

    fig_3 = plt.figure(3)
    plt.plot(r, buy_r, 'r', avg_buy_time, 'b')
    plt.xlabel('Request Number')
    plt.ylabel('Buy Request Response Time(s)')
    plt.title('Response-time for {} Buy Requests (includes Verification Query & Update)'.format(n))
    plt.gca().legend(('Actual Response Time', 'Average Response Time'))
    plt.savefig('buy_request.png')

    fig_4 = plt.figure(4)
    plt.plot(r, end_to_end_r, 'r', avg_e2e_time, 'b')
    plt.xlabel('Request Number')
    plt.ylabel('End-to-End Request Response Time(s)')
    plt.title('Total E2E Response-time for {} Requests'.format(n))
    plt.gca().legend(('Actual Response Time', 'Average Response Time'))
    plt.savefig('e2e_response.png')
    plt.show()
