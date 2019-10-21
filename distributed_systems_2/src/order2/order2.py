from flask import Flask, jsonify, abort
import requests
import json
import code
import datetime
import socket
import os
import sqlite3
import random
import requests
import itertools
import time
import ast
import config

app = Flask("order2_server")

front_end_ip = config.FRONT_END_IP
front_end_port = config.FRONT_END_PORT

catalog1_ip = config.CATALOG1_IP
catalog1_port = config.CATALOG1_PORT

catalog2_ip = config.CATALOG2_IP
catalog2_port = config.CATALOG2_PORT

order1_ip = config.ORDER1_IP
order1_port = config.ORDER1_PORT

# global array to temporarily hold logs if one of the replicas is off
transaction_logs_array = []

catalog_replicas = itertools.cycle(['catalog1', 'catalog2'])


# Allocates one of the two catalog replicas.
# Checks for the heartbeat of the catalog server to see if it is alive.
# Assumption is- only one replica can fail.
def catalog_replica_allocation():
    selected_catalog = next(catalog_replicas)
    if selected_catalog == 'catalog1':
        try:  # Check heartbeat of catalog1 server
            reply = requests.get('http://{}:{}/catalog/check_heartbeat'.format(catalog1_ip, catalog1_port))
            ip = catalog1_ip
            port = catalog1_port
            catalog_name = selected_catalog
        except:  # if catalog1 is not alive then use catalog2
            ip = catalog2_ip
            port = catalog2_port
            catalog_name = 'catalog2'
    else:
        try:  # Check heartbeat of catalog2 server
            reply = requests.get('http://{}:{}/catalog/check_heartbeat'.format(catalog2_ip, catalog2_port))
            ip = catalog2_ip
            port = catalog2_port
            catalog_name = 'catalog2'
        except:  # if catalog2 is not alive then use catalog1
            ip = catalog1_ip
            port = catalog1_port
            catalog_name = 'catalog1'
    return catalog_name, ip, port


# ===============CREATE ORDERS DATABASE =====================
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'ordersdb2.db')


# Creates a new database if none exists.
# Database columns are: id, item number, status, order_date, remaining_stock
def create_database():
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    books_sql = """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_number integer NOT NULL,
        status TEXT(80) NOT NULL,
        order_date TEXT(80) NOT NULL,
        remaining_stock INTEGER NOT NULL)"""

    db_cursor.execute(books_sql)
    db_connection.commit()
    db_cursor.close()


create_database()


def insert_transaction_logs(current_logs):
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    db_cursor.execute("INSERT INTO orders VALUES (NULL,?,?,?,?)", current_logs)
    db_connection.commit()
    db_cursor.close()
    send_logs_to_replicas(current_logs)


# Helper function for inserting transaction logs
# from the replica into the current database.
def insert_transaction_logs_from_replicas(transReplica_logs):
    db_connection = sqlite3.connect(DEFAULT_PATH)
    for index, row in enumerate(transReplica_logs):
        temp_log = tuple(row)
        db_cursor = db_connection.cursor()
        db_cursor.execute("INSERT INTO orders VALUES (NULL,?,?,?,?)", temp_log)
        db_connection.commit()
        db_cursor.close()

# helper function for querying all logs
def query_all_transaction_logs():
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    sql_query = "SELECT * FROM orders"
    db_cursor.execute(sql_query)
    all_orders = db_cursor.fetchall()
    db_cursor.close()
    return all_orders

# ======== FUNCTIONS ASSOCIATED WITH REPLICAS ======================
# when a transaction log is inserted into the database,
# this function is called so that it update the replica's database
# with the same transaction log
def send_logs_to_replicas(logs2send):
    transaction_logs_array.append(logs2send)
    try:
        response = requests.get(
            'http://{}:{}/logstransactions_replicas/{}'.format(order1_ip, order1_port, transaction_logs_array))
        transaction_logs_array.clear()
    except:
        None

# API end point called by the other order server to update the
# transaction logs of the replica.
@app.route('/logstransactions_replicas/<logs2save>', methods=['GET'])
def receive_logs_from_replicas(logs2save):
    logs2process = ast.literal_eval(logs2save)
    if len(logs2process) != 0:
        insert_transaction_logs_from_replicas(logs2process)

    return jsonify(str(query_all_transaction_logs()))


@app.route('/order/check_heartbeat', methods=['GET'])
def heartbeat():
    return jsonify("Yes")


# ====== RESYNC DATABASES BEFORE GOING ONLINE ==========================
# Function that resyncs the current orders database with that of the replicas
# This is called whenever the server starts, but has not yet gone online.
# if the other replica is already online, it will have accumulated transaction logs
# that will be synced, otherwise, none.
def resync_log_dabases():
    try:
        response = requests.get('http://{}:{}/resync_log_replicas/{}'.format(order1_ip, order1_port, "all"))
        synced_logs = response.json()
        synced_logs = ast.literal_eval(synced_logs)
        insert_transaction_logs_from_replicas(synced_logs)
    except:
        print("no data to sync")
    return True

# API endpoint that is called by the replicas to resync the order databases
# once the replica starts, but has not yet gone online.
# returns an array of logs to be synced and it should be noted
# that this action assumes a weak database consistency
@app.route('/resync_log_replicas/<count>', methods=["GET"])
def resync_replica_log_dbs(count):
    temp_logs = transaction_logs_array.copy()
    transaction_logs_array.clear()
    return jsonify(str(temp_logs))


# ====================== INTERMEDIARY FUNCTIONS =======================
# API used by order server to verify a book's availability
# and then to process the order if it is available.
# Input: book number
# Output: Decrements the stock if it is not 0. Sends a message
# if the transaction was succesful or not.
@app.route('/buy/<int:item_number>', methods=['GET'])
def buy_request(item_number):
    # time.sleep(10)
    print("Received buy request for book {}.".format(item_number))
    # Queries the catalog server to check if the stock is not empty
    try:  # if one replica fails while processing a request, it is forwarded to the other
        # Selects which one of the two catalog replicas to forward the request to
        catalog_name, catalog_ip, catalog_port = catalog_replica_allocation()
        print("Sending availability verification query to the catalog server- {}".format(catalog_name))
        check_stock = requests.get('http://{}:{}/query_by_item/{}'.format(catalog_ip, catalog_port, item_number))
    except:
        catalog_name, catalog_ip, catalog_port = catalog_replica_allocation()
        print('Catalog server crashed. Re-issuing verification request to different catalog server- {}.'.format(
            catalog_name))
        check_stock = requests.get('http://{}:{}/query_by_item/{}'.format(catalog_ip, catalog_port, item_number))

    current_stock = check_stock.json()['stock']
    if current_stock > 0:
        print("{} is in stock. Continuing with the transaction.".format(item_number))
        print("Invalidating Cache for book {}.".format(item_number))
        # Invalidate cache before making any changes to the stock- uses server push
        m = requests.get('http://{}:{}/cache/invalidate/{}'.format(front_end_ip, front_end_port, item_number))
        print(m.json())
        # Proceed with transaction only after cache has been invalidated
        if m.json() == 'Cache data invalidated.':
            # If the stock is not empty then it uses the update interface
            # of catalog server to decrease the stock count by 1.
            # NOTE: change value = 1 is explicitly stated in the message.
            n = requests.get('http://{}:{}/update/decrease_count/1/{}'.format(catalog_ip, catalog_port, item_number))
            print("Sold book {}".format(item_number))
            order_status = 'Order Completed'
            order_date = str(datetime.datetime.now())
            rem_stock = str(current_stock - 1)
            current_logs = (item_number, order_status, order_date, rem_stock)
            insert_transaction_logs(current_logs)
            return jsonify("Transaction successful.")
        else:
            print("Cannot invalidate cache data.")
            return jsonify("Cannot invalidate cache data.")
    else:
        # Usually the client will only attempt to buy a book if the stock is not empty.
        # But there can be a scenario where the buy request was being forwarded, and
        # in the meanwhile, some other client made a purchase, and the
        # initially non-zero stock went empty.
        # It also takes care of the scenario when the client sends a buy request even if the
        # item was not in stock.
        order_status = 'Order Failed'
        order_date = str(datetime.datetime.now())
        current_logs = (item_number, order_status, order_date, current_stock)
        insert_transaction_logs(current_logs)
        return jsonify("Oops! We ran out of {}'s stock. Please try again after sometime.".format(item_number))


# Obtain IP address of the local machine
def get_ip_address():
    try:
        localhost = socket.gethostbyname(socket.gethostname())
    except:
        localhost = '127.0.0.1'
    return localhost


if __name__ == '__main__':
    localhost = get_ip_address()
    resync_start = time.time()
    # resync the logs database before going online
    sync_completed = resync_log_dabases()

    if sync_completed == True:
        resync_stop = time.time()
        resync_time = resync_stop - resync_start
        app.run(host=localhost, port=12351, threaded=True)

# code.interact(local = locals())
