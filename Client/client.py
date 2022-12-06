import socket
import threading
import os
import re
import random
import platform
import datetime
import traceback
import sys

running = True

def get_rfc(client_host, client_port, get_data):
    rfc_get_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rfc_get_socket.connect((client_host, client_port))
    rfc_get_socket.sendall(get_data.encode())
    encoded_response = rfc_get_socket.recv(1024)
    plain_text_response = encoded_response.decode()
    response_lines = plain_text_response.split("\n")
    if "200 OK" in  response_lines[0]: 
        data_len = int(re.sub(r"CONTENT-LENGTH: ", "", response_lines[4]))
        header_length = len(("\n".join(response_lines[:6]) + "\n").encode())
        text = plain_text_response[header_length:]
        rfc_data_length = data_len - (len(encoded_response) - header_length)
        while rfc_data_length > 0:
            remaining_data = rfc_get_socket.recv(rfc_data_length)
            text += remaining_data.decode()
            rfc_data_length -= len(remaining_data)
        rfc_get_socket.close()
        return text
    else:
        print("Error Occurred while downloading!")
        print(plain_text_response)
        return

def upload_rfc(peerSocket, peerAddress):
    raw_request = peerSocket.recv(1024)
    request = raw_request.decode()
    request_lines = request.split("\n")
    if "P2P-CI/1.0" in request_lines[0]:
        if "GET" in request_lines[0]:
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
        peer_thread = threading.Thread(target=upload_rfc, args=(peerSocket, peerAddress))
        peer_thread.start()


def server_thread(clientServerSocket, upload_port):
    
    global running
    serverPort = 7734 ##Connecting to a well know port number.
    serverName = "rohit-ubuntu" ##Change according to your server's hostname.
    clientName = socket.gethostname()

    clientServerSocket.connect((serverName, serverPort))
    clientPort = clientServerSocket.getsockname()[1]
    while running:
        
        print("Please input the request type: " + "\n")
        request_type = input("1: Add RFC\n2: Get RFC\n3: List RFC(s)\n4: Lookup RFC\n5: Close the Client\n")
        if request_type == "1" or request_type ==  1:
            print("kjdfhsjfhskjdf")
            rfc_number = input("Please input the RFC Number: " + "\n")
            rfc_title = input("Please input the RFC Title " + "\n")
            # print (os.path+ "/" +rfc_number + ".txt")
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

        elif request_type == "2" or request_type ==  2:
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
            if "200 OK" in response_lines[0]:
                peer_info_line = response_lines[-2].split(" ")
                print(peer_info_line)
                peer_host = peer_info_line[-2]
                peer_port = int(peer_info_line[-1])
                get_message = "GET RFC " + rfc_number + " P2P-CI/1.0\n" \
              + "HOST: " + peer_host + "\n" \
              + "OS: " + platform.system() + " " + platform.release()
                data = get_rfc(peer_host, peer_port, get_message)
                if data:
                    with open("./{}.txt".format(rfc_number), "w") as file:
                        file.write(data)
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

        elif request_type == "3" or request_type ==  3:
            header = "LIST ALL P2P-CI/1.0\n" \
              + "HOST: " + clientName + "\n" \
              + "PORT: " + str(upload_port)
            clientServerSocket.send(header.encode())
            raw_response = clientServerSocket.recv(1024)
            response = raw_response.decode()
            print(response)

        elif request_type == "4" or request_type ==  4:
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

        

        elif request_type == "5" or request_type == 5:
            clientServerSocket.close()
            running = False
            os._exit(0)
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