import socket
import sys
import select

READ_SOCKET_LIST = []
WRITE_SOCKET_LIST = []

server_socket = socket.socket()
port = int(sys.argv[1])
server_socket.bind(('', port))
server_socket.listen(5)
READ_SOCKET_LIST.append(server_socket)
# dictionary of all the names to respective channels
name_to_remote = {}
name_to_channel = {}
messages_to_name = {}
client_name = ''

while True:
    ready_to_read, ready_to_write, in_error = select.select(READ_SOCKET_LIST, WRITE_SOCKET_LIST, [], 0)
    for read_sock in ready_to_read:
        # new connection to server
        if read_sock == server_socket:
            (new_sock, address) = server_socket.accept()
            READ_SOCKET_LIST.append(new_sock)
            write_sock = socket.socket()
            print(new_sock.getpeername())
            t_host = new_sock.getpeername()[0]
            t_port = new_sock.getpeername()[1]
            print(address)
            w_sock = write_sock.connect((address[0], t_port+1))
            WRITE_SOCKET_LIST.append(write_sock)
        else:
            # STDOUT Server Side
            Data = new_sock.recv(1024)
            if '$$$$' in Data:
                client_name = Data[4:]
                name_to_remote[client_name] = str(new_sock.getpeername())
            messages_to_name[client_name] = Data
    #output to CLIENTS
    for wr_sock in ready_to_write:
        if str(wr_sock.getpeername()) == client_name:
            # TODO logic with message (parse)
            wr_sock.send(Data)


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