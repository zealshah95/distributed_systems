import unittest
import json
from front_end import app

"""
Functional tests for the front_end.py
Tests three functions, ie search for a particular topic,
look up a particular book, based on the booj number and
finally, buy a particular book, given it's book number
"""


class TestFrontEnd(unittest.TestCase):
    # set up unit tests. this will be run for each of the three tests
    def setUp(self):
        self.client = app.test_client()
        # print('setting up client')

    # helper function for decoding json response
    # returns a decoded json response
    def json_of_response(self, response):
        return json.loads(response.data.decode('utf8'))

    # tests the search_request(topic) function in front_end.py
    # input/output: none, but assertions will fail if the request topic is not available
    def test_search_request(self):
        response = self.client.get('/search/{}'.format('graduate_school'))
        data = self.json_of_response(response)
        book1_title, book2_title = data['items'].keys()
        book1_number, book2_number = data['items'].values()
        self.assertEqual(response.status_code, 200)
        self.assertIn(book1_title,
                      ['Cooking for the Impatient Graduate Student', 'Xen and the Art of Surviving Graduate School'])
        self.assertIn(int(book2_number), [546, 768])

    # tests the lookup_request(item_number) function
    # input/output: none, but assertions will fail if the book with a given book number is not available
    def test_lookup_request(self):
        # print("Running test for looking a certain book by item number")
        response = self.client.get('/lookup/{}'.format(768))
        data = self.json_of_response(response)
        item_number = data.get('item_number')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(item_number, 768)

    # tests buy(item_number) function
    # input/output: none, but assertions will indicate whether the transaction was successful or the book is not
    # in stock
    def test_buy(self):
        item_number = 546
        response = self.client.get('/buy/{}'.format(item_number))
        response_text = self.json_of_response(response)
        self.assertEqual(response.status_code, 200)
        not_available = "Oops! We ran out of {}'s stock. Please try again after sometime.".format(item_number)
        self.assertIn(response_text, ['Transaction successful.', not_available])

    # clean up the tests for a particular test session
    def tearDown(self):
        # printed to separate the different print tests of different classes
        print('-------------------------------------')


if __name__ == '__main__':
    print('Starting tests...')
    unittest.main()
