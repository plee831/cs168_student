import socket
import sys
import select

READ_SOCKET_LIST = []

server_socket = socket.socket()
port = int(sys.argv[1])
server_socket.bind(('', port))
server_socket.listen(20)
READ_SOCKET_LIST.append(server_socket)
# dictionary of all the names to respective channels
remote_to_name = {}
name_to_channel = {}
name_to_messages = {}
client_name = ''

while True:
    ready_to_read, ready_to_write, in_error = select.select(READ_SOCKET_LIST, [], [], 0)
    for sock in ready_to_read:
        # new connection to server
        if sock == server_socket:
            (new_sock, address) = server_socket.accept()
            READ_SOCKET_LIST.append(new_sock)
        else:
            # STDOUT Server Side
            Data = sock.recv(1024)
            if '$$$$' in Data:
                client_name = Data[4:]
                remote_to_name[str(sock.getpeername())] = client_name
                print(client_name)
            else:
                client_name = remote_to_name[str(sock.getpeername())]
                name_to_messages[client_name] = Data
                # This sends to specific socket's address, not remote
                sock.sendto(Data, sock.getsockname())
                print(Data)


# The first message that the server receives
# from the client should be used as the client's name.


# broadcast chat messages to all connected clients
def broadcast (server_socket, sock, message):
    for socket in READ_SOCKET_LIST:
        # send the message only to peer
        if socket != server_socket and socket != sock :
            try:
                socket.send(message)
            except socket.gaierror: #maybe different exception here
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in READ_SOCKET_LIST:
                    READ_SOCKET_LIST.remove(socket)