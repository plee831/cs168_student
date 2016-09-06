import socket
import sys
import utils

client_sock = socket.socket()
client_name = sys.argv[1]
host = sys.argv[2]
port = int(sys.argv[3])
try:
    client_socket = client_sock.connect((host, port))
except socket.error, exc:
    print(utils.CLIENT_CANNOT_CONNECT.replace('{0}', host).replace('{1}', port))

while True:
    Data = client_socket.recv(1024)
    if len(Data) == 0:
        print(utils.CLIENT_SERVER_DISCONNECTED.replace({'0'}, host).replace({1}, port))

        break
    client_sock.send(client_name)

    client_sock.send(raw_input())

