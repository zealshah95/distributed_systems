import requests
import code
import json
import random
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


if __name__ == '__main__':
    # Client randomly selects one of the two topics to search for.
    topic = random.choice(['distributed_systems', 'graduate_school'])
    # topic = 'random_topic' #Uncomment and use this to test for correctness of search output.
    print("I am looking for books on topic {}.".format(topic))
    print("Search output is:")
    search_output = search(topic)
    print(search_output)
    # Exception handling for the case when client looks for book topic not present
    # in the database.
    try:
        # Client randomly selects one of the books from the list it received
        # from the search response.
        item_of_interest = random.choice(list(search_output['items'].values()))

        for name, number in search_output['items'].items():
            if number == item_of_interest:
                book_name = name
        # item_of_interest = 555 #uncomment & use this to test for correctness of lookup output.
        # Client looks up for details regarding the selected book like price and stock availability.
        print("I would like to look up the details regarding item number {}.".format(item_of_interest))
        print("The details for item number {} are as follows:".format(item_of_interest))
        lookup_output = lookup(item_of_interest)
        print(lookup_output)
        # Exception handling for the case when client looks for a wrong book number.
        try:
            current_stock = lookup_output['stock']
            # Check if the stock is empty or not. Client doesn't proceed with buying if the item is
            # not in stock. NOTE: Even if the client proceeds with buying an unavailable item
            # the order server will not allow the transaction to take place.
            if current_stock > 0:
                print("{} book is available in stock".format(item_of_interest))
                print("I want to buy item number {}.".format(item_of_interest))
                # Client sends the buy request only if the stock is not empty.

                trans_results = buy(item_of_interest)
                print(trans_results)
                if trans_results == "Transaction successful.":
                    print("Bought book {}".format(book_name))
            else:
                # Client gets an empty stock message if the stock is empty.
                print("Item not in stock. Please try again later.")
        except:
            None

    except:
        None
    # code.interact(local=locals())
