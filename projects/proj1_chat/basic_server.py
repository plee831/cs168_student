import socket
import sys

server_socket = socket.socket()
server_socket.bind(('', int(sys.argv[1])))
server_socket.listen(5)
while 1:
    (new_sock, address) = server_socket.accept()
    Data = new_sock.recv(1024)
    print(Data)
