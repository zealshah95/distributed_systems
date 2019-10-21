# 677 Lab 2

NOTE: We have hard-coded IP addresses of the EdLab machines in our servers' code instead of using a configuration file.
In order to ensure correct operation of our system, please make sure that the servers are run on the exact
same EdLab machines as specified in the steps given below.

Steps to run the setup on distributed machines:
1. Copy the lab-2-stima folder to EdLab 1.
2. Ensure that flask, pandas and matplotlib modules are installed on EdLab 1, EdLab 2, EdLab 3 and EdLab 7.
3. All the files should be run with Python3 as python3 {file_name.py}. The reason behind this instruction
    is that in EdLab, the modules in step 2 get installed under python 3 instead of python 2.7.
4. Start the servers in the following order; catalog.py MUST be started on EdLab 1, order.py MUST be started
    on EdLab 2, front_end.py MUST be started on EdLab 3 and then all the client files
    (client.py, sequential_requests_time.py, concurrent_requests.py) MUST be run on EdLab 7.
5. To run functional tests for front_end.py, the file test_frontend.py MUST reside on the
    same server as front_end.py, in this case, EdLab 3.

