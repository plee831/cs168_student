import socket
import sys
import select

SOCKET_LIST = []

server_socket = socket.socket()
port = int(sys.argv[1])
server_socket.bind(('', port))
server_socket.listen(5)
SOCKET_LIST.append(server_socket)

# dictionary of all the names to respective channels
name_to_remote = {}
name_to_channel = {}

while True:
    ready_to_read, ready_to_write, in_error = select.select(SOCKET_LIST, [], [], 0)
    for read_sock in ready_to_read:
        # new connection to server
        if read_sock == server_socket:
            (new_sock, address) = server_socket.accept()
            SOCKET_LIST.append(new_sock)
        else:
            Data = new_sock.recv(1024)
            if '$$$$' in Data:
                client_name = Data[4:]
                name_to_remote[client_name] = str(new_sock.getpeername())

# The first message that the server receives
# from the client should be used as the client's name.


# broadcast chat messages to all connected clients
def broadcast (server_socket, sock, message):
    for socket in SOCKET_LIST:
        # send the message only to peer
        if socket != server_socket and socket != sock :
            try:
                socket.send(message)
            except socket.gaierror: #maybe different exception here
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)