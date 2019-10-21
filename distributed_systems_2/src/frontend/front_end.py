from flask import Flask, jsonify, abort
import requests
import code
import json
import socket
import itertools
import time
import config

app = Flask("front_end_server")

# Feed IP address and port number of Catalog server.

# catalog_ip = "128.119.243.147"
catalog1_ip = config.CATALOG1_IP
catalog1_port = config.CATALOG1_PORT
catalog2_ip = config.CATALOG2_IP
catalog2_port = config.CATALOG2_PORT
# Feed IP address and port number of Order server.
# order_ip = "128.119.243.164"
order1_ip = config.ORDER1_IP
order1_port = config.ORDER1_PORT
order2_ip = config.ORDER2_IP
order2_port = config.ORDER2_PORT

cache_hit  = [] #reports time for cache hit
cache_miss = [] #reports time for cache miss
cache_invalidate = [] #reports time for cache invalidation
catalog_failure = [] #reports time to detect failure of catalog server
order_failure = []  #reports time to detect failure of order server
catalog_switch = [] #reports time for switching from crashed catalog replica to healthy one
order_switch = [] #reports time for switching from crashed order replica to healthy one

# in-memory cache in form of dictionary. It stays valid
# until the server is on. It will be emptied when the
# server is shut down.
cached_data = dict()

# Allows to toggle between replicas per-request basis
catalog_replicas = itertools.cycle(['catalog1', 'catalog2'])
order_replicas = itertools.cycle(['order1', 'order2'])

# Implementation: Per-request load balancing by toggling between replicas
# Allocates one of the two catalog replicas.
# Checks for the heartbeat of the catalog server to see if it is alive.
# Assumption is- only one replica can fail.
# Output is IP and port number of an alive replica
def catalog_replica_allocation():
    selected_catalog = next(catalog_replicas)
    if selected_catalog == 'catalog1':
        try: # Check heartbeat of catalog1 server
            reply = requests.get('http://{}:{}/catalog/check_heartbeat'.format(catalog1_ip, catalog1_port))
            ip = catalog1_ip
            port = catalog1_port
            catalog_name = selected_catalog
        except: # if catalog1 is not alive then use catalog2
            ip = catalog2_ip
            port = catalog2_port
            catalog_name = 'catalog2'
    else:
        try: # Check heartbeat of catalog2 server
            reply = requests.get('http://{}:{}/catalog/check_heartbeat'.format(catalog2_ip, catalog2_port))
            ip = catalog2_ip
            port = catalog2_port
            catalog_name = 'catalog2'
        except: # if catalog2 is not alive then use catalog1
            ip = catalog1_ip
            port = catalog1_port
            catalog_name = 'catalog1'
    return catalog_name, ip, port

# Implementation: Per-request load balancing by toggling between replicas
# Allocates one of the two order replicas.
# Checks for the heartbeat of the order server to see if it is alive.
# Assumption is- only one replica can fail.
# Output is IP and port number of an alive replica
def order_replica_allocation():
    selected_order = next(order_replicas)
    if selected_order == 'order1':
        try: # Check heartbeat of order1 server
            reply = requests.get('http://{}:{}/catalog/check_heartbeat'.format(order1_ip, order1_port))
            ip = order1_ip
            port = order1_port
            order_name = selected_order
        except:# if order1 is not alive then use order2
            ip = order2_ip
            port = order2_port
            order_name = 'order2'
    else:
        try: # Check heartbeat of order2 server
            reply = requests.get('http://{}:{}/catalog/check_heartbeat'.format(order2_ip, order2_port))
            ip = order2_ip
            port = order2_port
            order_name = 'order2'
        except: # if order2 is not alive then use order1
            ip = order1_ip
            port = order1_port
            order_name = 'order1'
    return order_name, ip, port

# Search API used by client to search for books by their topics.
# It routes the search request to the catalog server.
# Input: topic.
# Output: JSON object containing relevant book titles, and
# their numbers. Forwards the output to client.
@app.route('/search/<topic>', methods=['GET'])
def search_request(topic):
    print("Received client search request for books on topic- {}".format(topic))
    try:
        # Selects which catalog replica to send the request to
        catalog_name, catalog_ip, catalog_port = catalog_replica_allocation()
        print("Sending subject-based query to the catalog server- {}.".format(catalog_name))
        r = requests.get('http://{}:{}/query_by_subject/{}'.format(catalog_ip, catalog_port, topic))
    except:
        catalog_name, catalog_ip, catalog_port = catalog_replica_allocation()
        print('Catalog server crashed. Re-issuing search request to different catalog server- {}.'.format(catalog_name))
        # catalog_search_switch_stop = time.time()
        r = requests.get('http://{}:{}/query_by_subject/{}'.format(catalog_ip, catalog_port, topic))
    try:
        r = json.loads(r.text)
        print("Forwarding search query results to the client.")
        return jsonify(r)
    except:
        print("Forwarding search query results to the client.")
        return jsonify(r)

# Lookup API used by client to look for details of a specific book.
# It routes the lookup request to the catalog server.
# Input: book number.
# Output: JSON object containing relevant information like
# book cost, and stock count. Forwards the output to client.
@app.route('/lookup/<int:item_number>', methods=['GET'])
def lookup_request(item_number):
    print("Received client lookup request for details of book numbered {}.".format(item_number))
    # Check if the data is available in cache. If yes, then forward results to the client.
    try: # Cache Hit Scenario
        # cache_hit_start = time.time()
        m = cached_data[item_number]
        print('Data found in cache.')
        # cache_hit_stop = time.time()
        # cache_hit.append(cache_hit_stop - cache_hit_stop)
        print("Forwarding lookup query results to the client.")
        return jsonify(m)
    # If data is not available in the cache, forward the request to the catalog server.
    except: # Cache Miss Scenario
        # catalog_failure_start = time.time()
        # cache_miss_start = time.time()
        try: # if one replica fails while processing a request, it is forwarded to the other
            # Selects which one of the two catalog replicas to forward the request to
            catalog_name, catalog_ip, catalog_port = catalog_replica_allocation()
            print('Data not found in cache. Forwarding request to catalog server- {}.'.format(catalog_name))
            m = requests.get('http://{}:{}/query_by_item/{}'.format(catalog_ip, catalog_port, item_number))
        except: #initial replica has failed. Switches to healthy replica

            # catalog_failure_end = time.time()
            # catalog_failure.append(catalog_failure_end - catalog_failure_start)
            # catalog_switch_start = time.time()
            catalog_name, catalog_ip, catalog_port = catalog_replica_allocation()
            print('Catalog server crashed. Re-issuing lookup request to different catalog server- {}.'.format(catalog_name))
            # catalog_switch_end = time.time()
            # catalog_switch.append(catalog_switch_end - catalog_switch_start)
            m = requests.get('http://{}:{}/query_by_item/{}'.format(catalog_ip, catalog_port, item_number))
        # cache_miss_stop = time.time()
        # cache_miss.append(cache_miss_stop - cache_miss_start)
        try:
            m = json.loads(m.text)
            print("Caching Data.")
            data_to_cache = {'item_number':m['item_number'], 'cost':m['cost'], 'stock':m['stock']}
            cached_data[item_number] = data_to_cache #Cache data
            # print(cached_data)
            print("Forwarding lookup query results to the client.")
            return jsonify(m)
        except:
            print("Forwarding lookup query results to the client.")
            return jsonify(m) #might need to change m to m.text or vice versa if it doesnt work

# Invalidates a cache item by removing a specific outdated item from the cache.
@app.route('/cache/invalidate/<int:item_number>')
def invalidate_cache(item_number):
    # cache_invalidate_start = time.time()
    print("Invalidating cache data for item number- {}".format(item_number))
    cached_data.pop(item_number, None) #Invalidate entry by removing it from the cache
    # cache_invalidate_stop = time.time()
    # cache_invalidate.append(cache_invalidate_stop - cache_invalidate_start)
    return jsonify("Cache data invalidated.")

# Buy API used by client to buy a specific book.
# Request is sent to the order server.
# Input: book number.
# Output: Returns a message regarding transaction success/failure.
@app.route('/buy/<int:item_number>', methods=['GET'])
def buy(item_number):
    print("Client wants to buy book numbered {}".format(item_number))
    # order_failure_start = time.time()
    try: # if a server fails while processing a request, it gets forwarded to another server
        # Selects an order server to forward the request to
        order_name, order_ip, order_port = order_replica_allocation()
        print("Sending buy request to the order server- {}".format(order_name))
        b = requests.get('http://{}:{}/buy/{}'.format(order_ip, order_port, item_number))
    except: #Initial replica has failed. Switch over to the other replica.

        # order_failure_end = time.time()
        # order_failure.append(order_failure_end - order_failure_start)
        # order_switch_start = time.time()
        order_name, order_ip, order_port = order_replica_allocation()
        print("Order server crashed. Re-issuing buy request to another order server- {}".format(order_name))
        # order_switch_end = time.time()
        # order_switch.append(order_switch_end - order_switch_start)
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
# Use it to access the time reporting lists for cache hit, miss, invalidation
# and also for replica fail switch-over
# code.interact(local=locals())
