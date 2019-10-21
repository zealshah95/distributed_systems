# 677 Lab 3

This is the Git repo for 677 Lab 3. See http://lass.cs.umass.edu/~shenoy/courses/spring19/labs/lab3.html for a description of the lab. The lab is due on April 24, 23:55 hrs. Prior to submitting your project, replace this README file with the one that explains how to setup and run your code. Be sure to provide enough details fo us to run it in order to grade it.

How to Run the Application?

NOTE:
1. We use a configuration file named config.py in the src folder of the project folder to specify the IP addresses of the different servers.
2. Make sure that the configuration file is copied to each of the server folders before running.
3. We changed the file structure so that it would be easy to dockerize the different servers. instead of putting all the files for creating servers under one parent directory (src), they are in child directories under src, that is src/catalog1 for catalog1, src/catalog2 for catalog2, etc.

Steps to run the setup on distributed machines:

- Step 1: Copy lab-3-stima folder to EdLab 1.
- Step 2: Ensure that flask, pandas and matplotlib modules are installed on EdLab 1, EdLab 2, EdLab 3 and EdLab 7.
- Step 3: Change the IP addresses in the configuration files to reflect which machines you want to run them on, assuming you intend to run them on separate EdLab machines. You can leave the port numbers un-changed
- Step 4: Change into the sub-directory corresponding to the server you want to start, for example cd catalog1 . All the files should be run with Python3 as cp .. \config.py && python3 {file_name.py}. The reason behind this instruction is that in EdLab, the modules in step 2 get installed under python 3 instead of python 2.7. Also, note the first part of the command which copies the configuration file into the specific server folder.
- Step 5: To run clients, change to the helper files, and follow repeat step (4).
- Step 6: Make sure that the servers are run on the EdLab machines corresponding to the IP addresses specified in the configuration files, otherwise you'll get errors.

How to Run Dockerized Application?

- Step 1: Make sure that you have docker installed on the machine that you'll dockerize the servers from.
- Step 2: Ensure that flask, pandas and matplotlib modules are installed on the machine.
- Step 3: Change the IP addresses in the configuration files to reflect which machines you want to run them on, assuming you intend to run them on separate EdLab machines. You can leave the port numbers un-changed. Note that if you are planning on running docker on localhost, docker for Mac OS doesn't recognize "localhost". Thus, you have to use "host.docker.internal".
- Step 4: Change into the specific directory under src corresponding the the server you want to dockerize, eg catalog1, catalog2, order1, etc and run the command cp .. \config.py && docker build -t docker_image_name e.g catalog1server. Note the name of the docker image you have create. Repeat this for all the servers you wish to dockerize.
- Step 5: To create the docker container and put the server online, run the command docker run -p portnumber:portnumber docker_image e.g docker run -p 12345:12345 catalog1server. If you want to run the server as a background service, pass -d as a parameter when you run the above command.
- Step 6: To see the list of running dockerized servers, run the command docker container ls -a