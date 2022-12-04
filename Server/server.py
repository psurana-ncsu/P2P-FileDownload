import pickle
import threading
import socket
import re

#global variable for maintainig a dictionary of peers along with their upload ports connected to the server.
active_peer_list = {}
#global variable for maintainig a dictionary of RFC and the peers having them.
rfc_list = {}
#Dictionary of response codes.
response_code = {1:'200 OK\n',
        2:'400 Bad Request\n',
        3:'404 Not Found\n',
        4:'505 P2P-CI Version Not Supported\n'}
#Setting Buffer Size
buff_size = 4096
serverPort = 7734
serverName = "0.0.0.0"
# print(response_code)


def lookup_rfc(data):
    global rfc_list
    global active_peer_list
    global response_code
    header = "P2P-CI/1.0 "
    lines = data.split("\n")
    # RFC Number is in the zero line
    # RFC Title is in the 3rd line
    rfc_number = int(re.search(r"RFC (\d+)", lines[0]).group(1))
    rfc_title = re.sub(r"TITLE: ", "", lines[3])
    if rfc_number in rfc_list.keys():
        header += response_code[1]
        for peer in rfc_list[rfc_number]:
            data += "RFC {} ".format(rfc_number) + peer["RFC TITLE"] + " " + peer["PEER HOST"] + " " + active_peer_list[
                peer["PEER HOST"]] + "\n"
        return header+data

    else:
        header += response_code[3]
        return header


def add_active_peer(data):
    global active_peer_list
    lines = data.split("\n")
    # Hostname of the client is on line 1
    # Port Number that the client is using for the upload process is on line 2
    peer_host = re.sub(r"HOST: ", "", lines[1])
    peer_upload = re.sub(r"PORT: ", "", lines[2])
    active_peer_list[peer_host] = peer_upload
    return peer_host, peer_upload


def add_rfc(data):
    global rfc_list
    lines = data.split("\n")
    # RFC Number is in the zero line
    # RFC Title is in the 3rd line
    rfc_number = int(re.search(r"RFC (\d+)", lines[0]).group(1))
    rfc_title = re.sub(r"TITLE: ", "", lines[3])
    peer_host = re.sub(r"HOST: ", "", lines[1])
    if rfc_number in rfc_list.keys():
        rfc_list[rfc_number].append({"PEER HOST": peer_host, "RFC TITLE": rfc_title})
    else:
        rfc_list[rfc_number] = [{"PEER HOST": peer_host, "RFC TITLE": rfc_title}]
    print(rfc_list)


def clean_peer_and_rfc(peer_host, peer_upload):
    global active_peer_list
    global rfc_list
    del (active_peer_list[peer_host])
    for key, value in rfc_list.items():
        rfc_list[key] = [x for x in value if x.get("PEER HOST") != peer_host]
    rfc_list = {k: v for k, v in rfc_list.items() if v}
    print(active_peer_list)
    print(rfc_list)


def client_thread(clientSocket, clientAddress, lock):
    global active_peer_list
    global rfc_list
    global response_code
    global buff_size
    peer_host = ""
    peer_upload = 0
    while True:
        raw_data = clientSocket.recv(buff_size)
        data = raw_data.decode()
        first_line = data.split("\n")[0]
        if re.search(r"P2P\-CI\/1\.0", first_line):
            if re.search(r"ADD", first_line):
                lock.acquire()
                print(data)
                peer_host, peer_upload = add_active_peer(data)
                add_rfc(data)
                header = "P2P-CI/1.0"
                lines = data.split("\n")
                peer_host = re.sub(r"HOST: ", "", lines[1])
                peer_upload = re.sub(r"PORT: ", "", lines[2])
                rfc_number = int(re.search(r"RFC (\d+)", lines[0]).group(1))
                rfc_title = re.sub(r"TITLE: ", "", lines[3])
                data_to_send = header + " " + response_code[1] \
                        + "RFC {} ".format(rfc_number) + rfc_title + " " + peer_host + " " + peer_upload
                lock.release()
                clientSocket.send(data_to_send.encode())
            elif re.search(r"LIST", first_line):
                lock.acquire()
                print(data)
                header = "P2P-CI/1.0 " + response_code[1]
                for rfc_number, rfc_info in rfc_list.items():
                    for peer in rfc_info:
                        data_to_send = "RFC {} ".format(rfc_number) + peer["RFC TITLE"] + " " + peer["PEER HOST"] + " " + active_peer_list[
                            peer["PEER HOST"]] + "\n"
                lock.release()
                out_data = header+data_to_send
                clientSocket.send(out_data.encode())
            elif re.search(r"LOOKUP", first_line):
                lock.acquire()
                print(data)
                response = lookup_rfc(data)
                lock.release()
                clientSocket.send(response.encode())
            else:
                message = "P2P-CI/1.0 " + response_code[2]
                print(data)
                clientSocket.send(message.encode())
        elif len(raw_data) == 0:
            # This means the socket is closed and we need to clean up
            if peer_host:
                lock.acquire()
                clean_peer_and_rfc(peer_host, peer_upload)
                lock.release()
            break
        else:
            message = "P2P-CI/1.0 " + response_code[4]
            print(data)
            clientSocket.send(message.encode())
    print("This thread is done")


def main():
    global serverName
    global serverPort
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((serverName, serverPort))
    serverSocket.listen()
    lock = threading.Lock()
    while True:
        clientSocket, clientAddress = serverSocket.accept()
        threading.Thread(target=client_thread, args=(clientSocket, clientAddress, lock)).start()


if __name__ == '__main__':
    main()
