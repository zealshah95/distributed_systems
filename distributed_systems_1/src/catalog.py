from flask import Flask, jsonify, abort
import code
import json
import socket
import time, threading
import sqlite3
import os
import random
import requests

# ===============CREATE CATALOG DATABASE & INSERT LIST OF BOOKS =====================
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'catalogdb.db')


# Creates a new database if none exists.
# Database columns are: id, item number, topic, title, cost, and stock
def create_database():
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    books_sql = """
	CREATE TABLE IF NOT EXISTS books (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
	    item_number integer NOT NULL,
	    topic TEXT(80) NOT NULL,
	    title TEXT(80) NOT NULL,
	    cost INTEGER NOT NULL,
	    stock_count INTEGER NOT NULL)"""

    db_cursor.execute(books_sql)
    db_connection.commit()
    db_cursor.close()


# Returns a list of all the books with details from the database
def query_all_existing_books():
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    sql_query = "SELECT * FROM books"
    db_cursor.execute(sql_query)
    all_books = db_cursor.fetchall()
    db_cursor.close()
    return all_books


# Initial entries inserted into the database.
# Columns: Item number, topic, title, cost, stock.
# Rows: One entry for every book.
def insert_list_of_books():
    available_books = [(666, 'distributed_systems', 'How to get a good grade in 677 in 20 minutes a day', 10, 10),
                       (321, 'distributed_systems', 'RPCs for Dummies', 5, 8),
                       (768, 'graduate_school', 'Xen and the Art of Surviving Graduate School', 15, 12),
                       (546, 'graduate_school', 'Cooking for the Impatient Graduate Student', 8, 10)]

    all_books = query_all_existing_books()

    # if the database doesn't contain all the 4 books, then insert them into the database
    if len(all_books) < 4:
        db_connection = sqlite3.connect(DEFAULT_PATH)
        db_cursor = db_connection.cursor()
        db_cursor.executemany("INSERT INTO books VALUES (NULL,?,?,?,?,?)", available_books)
        db_connection.commit()
        db_cursor.close()


# create database and insert the books
create_database()
insert_list_of_books()


# ============================QUERY & UPDATE THE DATABASE==========================
# Query database by topics- distributed_systems, graduate_school
def query_by_topic(q_string):
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    sql_query = "SELECT * FROM books WHERE topic=?"
    db_cursor.execute(sql_query, [(q_string)])
    book_list = db_cursor.fetchall()
    db_cursor.close()
    return book_list


# Query database by item number i.e. unique ID associated with a book title
def query_by_book_number(bk_number):
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    sql_query = "SELECT * FROM books WHERE item_number=?"
    db_cursor.execute(sql_query, [(bk_number)])
    single_book = db_cursor.fetchone()
    db_cursor.close()
    return single_book


# Inputs: book number and the new stock count
# Output: Adds new stock (restocks) of a specific book number when called
def update_book_count(book_number, new_stock_count):
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    db_cursor.execute('''UPDATE books SET stock_count = ? WHERE item_number = ? ''', (new_stock_count, book_number))
    db_connection.commit()
    db_cursor.close()


# Inputs: book number and new cost value
# Output: updates the cost of a specific book by a specific cost value
def update_cost_of_one_book(book_number, new_book_cost):
    db_connection = sqlite3.connect(DEFAULT_PATH)
    db_cursor = db_connection.cursor()
    db_cursor.execute('''UPDATE books SET cost = ? WHERE item_number = ? ''', (new_book_cost, book_number))
    db_connection.commit()
    db_cursor.close()


# =========================CATALOG SERVER APPLICATION============================
app = Flask("catalog_server")


# Update interface. It provides 3 different API calls for performing 3 operations-
# "decrease_count": decrements stock count of a book by one when the order server
# sends in an update catalog request to the catalog server.
# "update_cost": updates cost of a book.
# "add_stock": Adds new stock for a specified book.
# NOTE: variable called "change" denotes the amount by which a quantity needs to
# be changed- incremented or decremented. For "decrease_count", order server
# explicity uses change value = 1. For "add_stock", change value is randomly
# selected from numbers between 6 to 15, which basically becomes, the
# updated newly added stock for a specific book.

@app.route('/update/<operation>/<int:change>/<int:book_number>', methods=['GET'])
def update(operation, change, book_number):
    book = query_by_book_number(book_number)
    if len(book) == 0:
        abort(404)

    if operation == 'decrease_count':
        if book[5] >= 1:  # stock count is at index 5
            print("Received update request from order server for book {}.".format(book_number))
            new_stock_count = book[5] - change
            update_book_count(book_number, new_stock_count)
            print("Updated stock count for book {} is {}.".format(book_number, new_stock_count))
            return jsonify({'new_count': new_stock_count})
        else:
            return "Not Possible."

    if operation == 'update_cost':
        new_book_cost = change
        update_cost_of_one_book(book_number, new_book_cost)
        return jsonify({'new_count': book[0].stock_count})

    if operation == 'add_stock':
        update_book_count(book_number, change)
        print("Added new stock for {}.".format(book_number))


# API to look for books in the database associated with the specified topic.
# Input: topic
# Output: JSON object containing books' titles and item number.
@app.route('/query_by_subject/<booktopic>', methods=['GET'])
def query_by_subject(booktopic):
    books = query_by_topic(booktopic)
    print("Looking for books related to topic in the catalog- {}.".format(booktopic))
    # If client searches for books related to a topic not in the database, then
    # send a message saying no relevant books present.
    if len(books) == 0:
        return jsonify("There is no relevant book available associated with topic- {}".format(booktopic))
    books_dict = {}
    for book_row in books:
        books_dict[book_row[3]] = book_row[1]
    print("Found the books. Forwarding the results to front end server.")
    return jsonify({'items': books_dict})


# API to look for a details of a specific book using item number or
# book number as a unique identifier.
# Input: item number or book number
# Output: JSON object containing book's number, stock count and cost
@app.route('/query_by_item/<int:book_number>', methods=['GET'])
def query_by_item(book_number):
    print("Looking for details of the book numbered {}.".format(book_number))
    book = query_by_book_number(book_number)
    # If client searches for a book number which is not in the database, send
    # a message regarding no availability of such a book.
    if book is None:
        return jsonify("There is no book available of number- {}".format(book_number))
    book_dict = {"item_number": book[1], "stock": book[5], "cost": book[4]}
    print("Book {} details- cost: ${}, and stock: {}".format(book_number, book[4], book[5]))
    return jsonify(book_dict)


# ====================PERIODIC CHECKS FOR STOCK UPDATES==========================
# Queries the database and checks if stock of any of the books is empty.
# If the stock of any book is empty, it uses the Update interface's
# "add_stock" operation to add new stock. New stock count is generated
# randomly and it could be any integer between 6 and 15.
def periodic_updates():
    allbooks = query_all_existing_books()
    for book in allbooks:
        stock_count = book[5]
        book_number = book[1]
        if stock_count == 0:
            new_stock_count = random.randint(6, 16)
            update('add_stock', new_stock_count, book_number)


# Timer threads are used for periodic checks. Checks are done after every
# n seconds. After every n seconds, timer_funct() will call periodic_updates().
# NOTE: It is preferrable to set n to a lower value (5 seconds) if sequential
# requests are sent without any delay between them.
def timer_funct():
    n = 5
    periodic_updates()
    threading.Timer(n, timer_funct).start()


timer_funct()


# ===========================NETWORK & SERVER DETAILS============================
# Obtain IP address of the local machine
def get_ip_address():
    try:
        localhost = socket.gethostbyname(socket.gethostname())
    except:
        localhost = '127.0.0.1'
    return localhost


if __name__ == '__main__':
    localhost = get_ip_address()
    # run the server
    app.run(host=localhost, port=12345, threaded=True)
