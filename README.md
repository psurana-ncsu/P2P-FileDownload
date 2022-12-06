Team Members:
Rohit Nair (rsnair)
Pritesh Surana (psurana)

First run the server.py file, navigate to Server folder run the following command:
python3 server.py

Navigate to Client folder, before starting the client, we need to change the server's hostname in variable serverName on line number 98. Put the hostname of the machine where you are running the server.py (first file).

python3 client.py

We can start another client on another or the same host where the client was spawned, similar to first client we need to change the server's hostname.

python3 client.py

RFC should be present in the Client folder if we want to ADD a RFC. 
RFC will be downloaded  in the Client floder when a Get RFC operation is performed.