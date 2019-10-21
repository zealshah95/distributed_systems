from flask import Flask, jsonify, abort
import requests
import json
import code
import pandas as pd
import datetime
import socket
import os

app = Flask("order_server")

# Feed in IP address and port number of catalog server.
catalog_ip = "128.119.243.147"
catalog_port = 12345

# Creates a CSV database file if it does not exist already.
# Columns: item number, status, date, remaining stock
# "Status" will say if a transaction was successful or not.
# "date" will display the time and date when the transaction
# was attempted.


def create_data_file():
    file_exists = os.path.isfile(os.getcwd() + '/order_logs.csv')
    if file_exists is False:
        pd.DataFrame(columns=['Item Number', 'Status', 'Date', 'Remaining Stock']).to_csv('order_logs.csv', index=False)

# API used by order server to verify a book's availability
# and then to process the order if it is available.
# Input: book number
# Output: Decrements the stock if it is not 0. Sends a message
# if the transaction was succesful or not.


@app.route('/buy/<int:item_number>', methods=['GET'])
def buy_request(item_number):
    order_logs = pd.read_csv('order_logs.csv')
    print("Received buy request for book {}.".format(item_number))
    print("Sending availability verification query to the catalog server.")
    # Queries the catalog server to check if the stock is not empty
    check_stock = requests.get('http://{}:{}/query_by_item/{}'.format(catalog_ip, catalog_port, item_number))
    current_stock = check_stock.json()['stock']
    if current_stock > 0:
        print("{} is in stock. Continuing with the transaction.".format(item_number))
        # If the stock is not empty then it uses the update interface
        # of catalog server to decrease the stock count by 1.
        # NOTE: change value = 1 is explicitly stated in the message.
        n = requests.get('http://{}:{}/update/decrease_count/1/{}'.format(catalog_ip, catalog_port, item_number))
        print("Sold book {}".format(item_number))
        order_logs = order_logs.append({'Item Number': item_number, 'Status': 'Order Completed',
                                        'Date': datetime.datetime.now(),
                                        'Remaining Stock': str(current_stock - 1)}, ignore_index=True)
        order_logs.to_csv('order_logs.csv', index=False)

        return jsonify("Transaction successful.")
    else:
        # Usually the client will only attempt to buy a book if the stock is not empty.
        # But there can be a scenario where the buy request was being forwarded, and
        # in the meanwhile, some other client made a purchase, and the
        # initially non-zero stock went empty.
        # It also takes care of the scenario when the client sends a buy request even if the
        # item was not in stock.
        order_logs = order_logs.append({'Item Number': item_number, 'Status': 'Order Failed',
                                        'Date': datetime.datetime.now(),
                                        'Remaining Stock': str(current_stock)}, ignore_index=True)
        order_logs.to_csv('order_logs.csv', index=False)
        return jsonify("Oops! We ran out of {}'s stock. Please try again after sometime.".format(item_number))

# Obtain IP address of the local machine


def get_ip_address():
    try:
        localhost = socket.gethostbyname(socket.gethostname())
    except:
        localhost = '127.0.0.1'
    return localhost


if __name__ == '__main__':
    create_data_file()
    localhost = get_ip_address()
    app.run(host=localhost, port=12347, threaded=True)
