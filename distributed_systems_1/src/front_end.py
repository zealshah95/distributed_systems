from flask import Flask, jsonify, abort
import requests
import code
import json
import socket

app = Flask("front_end_server")

# Feed IP address and port number of Catalog server.
catalog_ip = "128.119.243.147"
catalog_port = 12345
# Feed IP address and port number of Order server.
order_ip = "128.119.243.164"
order_port = 12347

# Search API used by client to search for books by their topics.
# It routes the search request to the catalog server.
# Input: topic.
# Output: JSON object containing relevant book titles, and
# their numbers. Forwards the output to client.


@app.route('/search/<topic>', methods=['GET'])
def search_request(topic):
    print("Received client search request for books on topic- {}".format(topic))
    print("Sending subject-based query to the catalog server.")
    r = requests.get('http://{}:{}/query_by_subject/{}'.format(catalog_ip, catalog_port, topic))
    try:
        r = json.loads(r.text)
        print("Forwarding query results to the client.")
        return jsonify(r)
    except:
        print("Forwarding query results to the client.")
        return jsonify(r.text)

# Lookup API used by client to look for details of a specific book.
# It routes the lookup request to the catalog server.
# Input: book number.
# Output: JSON object containing relevant information like
# book cost, and stock count. Forwards the output to client.


@app.route('/lookup/<int:item_number>', methods=['GET'])
def lookup_request(item_number):
    print("Received client lookup request for details of book numbered {}.".format(item_number))
    print("Sending item-based query to the catalog server.")
    m = requests.get('http://{}:{}/query_by_item/{}'.format(catalog_ip, catalog_port, item_number))
    try:
        m = json.loads(m.text)
        print("Forwarding query results to the client.")
        return jsonify(m)
    except:
        print("Forwarding query results to the client.")
        return jsonify(m.text)

# Buy API used by client to buy a specific book.
# Request is sent to the order server.
# Input: book number
# Output: Returns a message regarding transaction success/failure.


@app.route('/buy/<int:item_number>', methods=['GET'])
def buy(item_number):
    print("Client wants to buy book numbered {}".format(item_number))
    print("Sending buy request to the order server.")
    b = requests.get('http://{}:{}/buy/{}'.format(order_ip, order_port, item_number))
    response = json.loads(b.text)
    return jsonify(response)

# Obtain IP address of the local machine


def get_ip_address():
    try:
        localhost = socket.gethostbyname(socket.gethostname())
    except:
        localhost = '127.0.0.1'
    return localhost


if __name__ == '__main__':
    localhost = get_ip_address()
    app.run(host=localhost, port=12346, threaded=True)
