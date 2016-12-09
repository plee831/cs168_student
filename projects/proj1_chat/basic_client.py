import socket
import sys

#
client_sock = socket.socket()
client_socket = client_sock.connect((sys.argv[1], int(sys.argv[2])))
# "52.53.187.155", 12388
client_sock.send(raw_input())
