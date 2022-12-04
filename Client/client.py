import socket
import threading
import os
import re
import random
import platform
import datetime
import traceback


def get_rfc(peer_host, peer_port, get_message):
    clientDownloadSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientDownloadSocket.connect((peer_host, peer_port))
    clientDownloadSocket.sendall(get_message.encode())
    raw_response = clientDownloadSocket.recv(1024)
    response = raw_response.decode()
    # Find out the length of the data being sent first, and then call receive again
    response_lines = response.split("\n")
    if re.search(r"200 OK", response_lines[0]):
        # Content length is on line 4
        data_length = int(re.sub(r"CONTENT-LENGTH: ", "", response_lines[4]))
        # Find the header length
        header_length = len(("\n".join(response_lines[:6]) + "\n").encode())
        # Obtain the data already received
        data = response[header_length:]
        # Recieve the rest of the data
        remaining_data_length = data_length - (len(raw_response) - header_length)
        while remaining_data_length > 0:
            remaining_data = clientDownloadSocket.recv(remaining_data_length)
            data += remaining_data.decode()
            remaining_data_length -= len(remaining_data)
        clientDownloadSocket.close()
        return data
    else:
        print("There was an error from the peer. This is the error code and message")
        print(response)
        return

def client_upload_rfc(peerSocket, peerAddress):
    raw_request = peerSocket.recv(1024)
    request = raw_request.decode()
    # Get the RFC Number from the request
    request_lines = request.split("\n")
    if re.search(r"P2P\-CI\/1\.0", request_lines[0]):
        if re.search(r"GET", request_lines[0]):
            rfc_number = int(re.search(r"RFC (\d+)", request_lines[0]).group(1))
            try:
                with open("./{}.txt".format(rfc_number), "r") as file:
                    file_data = file.read()
                if file_data:
                    header = "P2P-CI/1.0 "
                    header += "200 OK\n"
                    header += "DATE: " + str(datetime.datetime.today()) + " " + datetime.datetime.now(
                        datetime.timezone.utc).astimezone().tzname() + "\n"
                    header += "OS: " + platform.system() + " " + platform.release() + "\n"
                    header += "LAST-MODIFIED: " + str(
                        os.path.getmtime("./{}.txt".format(str(rfc_number)))) + datetime.datetime.fromtimestamp(
                        os.path.getmtime("./{}.txt".format(str(rfc_number)))).astimezone().tzname() + "\n"
                    header += "CONTENT-LENGTH: " + str(len(file_data.encode())) + "\n"
                    header += "CONTENT-TYPE: text/text\n"
                    data = file_data
                    data_to_send = header+data
                    peerSocket.sendall(data_to_send.encode())
                    peerSocket.close()
                else:
                    header = "P2P-CI/1.0 "
                    header += "404 Not Found\n"
                    header += "DATE: " + str(datetime.datetime.today()) + " " + datetime.datetime.now(
                        datetime.timezone.utc).astimezone().tzname() + "\n"
                    header += "OS: " + platform.system() + " " + platform.release() + "\n"
                    return header
            except FileNotFoundError as e:
                return "Error Caught: FileNotFoundError" 
            
        else:
            header = "P2P-CI/1.0 "
            header += "505 P2P-CI Version Not Supported\n"
            header += "DATE: " + str(datetime.datetime.today()) + " " + datetime.datetime.now(
                datetime.timezone.utc).astimezone().tzname() + "\n"
            header += "OS: " + platform.system() + " " + platform.release() + "\n"
            peerSocket.sendall(header.encode())
            peerSocket.close()
    else:
        header = "P2P-CI/1.0 "
        header += "400 Bad Request\n"
        header += "DATE: " + str(datetime.datetime.today()) + " " + datetime.datetime.now(
            datetime.timezone.utc).astimezone().tzname() + "\n"
        header += "OS: " + platform.system() + " " + platform.release() + "\n"
        peerSocket.sendall(header.encode())
        peerSocket.close()



def client_thread(clientUploadSocket, upload_port):
    clientName = "0.0.0.0"
    clientUploadSocket.bind((clientName, upload_port))
    clientUploadSocket.listen()
    while True:
        peerSocket, peerAddress = clientUploadSocket.accept()
        peer_thread = threading.Thread(target=client_upload_rfc, args=(peerSocket, peerAddress))
        peer_thread.start()


def server_thread(clientServerSocket, upload_port):
    serverPort = 7734
    serverName = "rohit-ubuntu"
    clientName = socket.gethostname()
    clientServerSocket.connect((serverName, serverPort))
    clientPort = clientServerSocket.getsockname()[1]
    while True:
        request_type = input("Please input the request type: " + "\n")
        if request_type == "ADD":
            rfc_number = input("Please input the RFC Number: " + "\n")
            rfc_title = input("Please input the RFC Title " + "\n")
            if os.path.exists(rfc_number + ".txt"):
                header = "ADD RFC " + rfc_number + " P2P-CI/1.0" + "\n" \
                + "HOST: " + clientName + "\n" \
                + "PORT: " + str(upload_port) + "\n" \
                + "TITLE: " + rfc_title
                clientServerSocket.send(header.encode())
                raw_response = clientServerSocket.recv(1024)
                response = raw_response.decode()
                print(response)
            else:
                print("RFC not present")

        elif request_type == "GET":
            rfc_number = input("Please input the RFC number you want to get: " + "\n")
            rfc_title = input("Please input the RFC Title of the RFC Number entered previously: " + "\n")
            header = "LOOKUP RFC " + rfc_number + " P2P-CI/1.0" + "\n" \
              + "HOST: " + clientName + "\n" \
              + "PORT: " + str(upload_port) + "\n" \
              + "TITLE: " + rfc_title
            clientServerSocket.send(header.encode())
            raw_response = clientServerSocket.recv(1024)
            response = raw_response.decode()
            print("The server response to your lookup: ")
            print(response)
            response_lines = response.split("\n")
            if re.search(r"200 OK", response_lines[0]):
                # From line 1 we have all the information we need
                peer_info_line = response_lines[1].split(" ")
                # Last item in the above list is the peer port number, second last item is the peer host
                peer_host = peer_info_line[-2]
                peer_port = int(peer_info_line[-1])
                get_message = "GET RFC " + rfc_number + " P2P-CI/1.0\n" \
              + "HOST: " + peer_host + "\n" \
              + "OS: " + platform.system() + " " + platform.release()
                data = get_rfc(peer_host, peer_port, get_message)
                if data:
                    with open("./{}.txt".format(rfc_number), "w") as file:
                        file.write(data)
                    # Sending ADD request to Server so that the server can keep his things updated
                    message = "ADD RFC " + rfc_number + " P2P-CI/1.0" + "\n" \
                        + "HOST: " + clientName + "\n" \
                        + "PORT: " + str(upload_port) + "\n" \
                        + "TITLE: " + rfc_title
                    clientServerSocket.send(message.encode())
                    raw_response = clientServerSocket.recv(1024)
                    response = raw_response.decode()
            else:
                print("Error Occurred")
                print(response)

        elif request_type == "LIST":
            header = "LIST ALL P2P-CI/1.0\n" \
              + "HOST: " + clientName + "\n" \
              + "PORT: " + str(upload_port)
            clientServerSocket.send(header.encode())
            raw_response = clientServerSocket.recv(1024)
            response = raw_response.decode()
            print(response)

        elif request_type == "LOOKUP":
            rfc_number = input("Please input the RFC Number you want to lookup: " + "\n")
            rfc_title = input("Please input the RFC Title of the RFC Number entered previously: " + "\n")
            header = "LOOKUP RFC " + rfc_number + " P2P-CI/1.0" + "\n" \
              + "HOST: " + clientName + "\n" \
              + "PORT: " + str(upload_port) + "\n" \
              + "TITLE: " + rfc_title
            clientServerSocket.send(header.encode())
            raw_response = clientServerSocket.recv(1024)
            response = raw_response.decode()
            print(response)

        

        elif request_type == "CLOSE":
            clientServerSocket.close()
            break


def main():
    # Manually create a random port number for the upload socket connection
    upload_port = random.randint(10000, 63000)
    clientUploadSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    uploading_thread = threading.Thread(target=client_thread, args=(clientUploadSocket, upload_port))

    clientServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_conn_thread = threading.Thread(target=server_thread, args=(clientServerSocket, upload_port))

    uploading_thread.start()
    server_conn_thread.start()


if __name__ == '__main__':
    main()
