import socket
import sys
import select
import utils

READ_SOCKET_LIST = []

server_socket = socket.socket()
port = int(sys.argv[1])
server_socket.bind(('', port))
server_socket.listen(20)
READ_SOCKET_LIST.append(server_socket)

# remote address of socket to name
remote_to_name = {}
# name to socket address of socket
name_to_address = {}
name_to_channel = {}
channels = set()
name_to_messages = {}
client_name = ''


def create(c_message):
    msg_to_send = ''
    if len(c_message) == 1:
        msg_to_send = utils.SERVER_CREATE_REQUIRES_ARGUMENT
    else:
        chl = c_message[1]
        if chl in channels:
            msg_to_send = utils.SERVER_CHANNEL_EXISTS.format(chl)
        else:
            channels.add(chl)
            name_to_channel[client_name] = chl
    return msg_to_send


def list_channels():
    msg_to_send = ''
    for c in channels:
        msg_to_send = msg_to_send + c + '\n'
    return msg_to_send


def join_channel(c_message, c_name):
    msg_to_send = ''
    if len(c_message) == 1:
        msg_to_send = utils.SERVER_JOIN_REQUIRES_ARGUMENT
    else:
        channel = c_message[1]
        if channel in channels:
            for name in name_to_channel.keys():
                for inner_sock in READ_SOCKET_LIST:
                    if name_to_channel[name] == channel and remote_to_name[str(inner_sock.getpeername())] == name:
                        inner_sock.sendall(utils.SERVER_CLIENT_JOINED_CHANNEL.format(name))
            if c_name in name_to_channel.keys():
                old_channel = name_to_channel[c_name]
                for name in name_to_channel.keys():
                    for inner_sock in READ_SOCKET_LIST:
                        if name_to_channel[name] == old_channel and \
                                        remote_to_name[str(inner_sock.getpeername())] == name:
                            inner_sock.sendall(utils.SERVER_CLIENT_LEFT_CHANNEL.format(name))
                name_to_channel[client_name] = channel
        else:
            msg_to_send = utils.SERVER_NO_CHANNEL_EXISTS.format(channel)
    return msg_to_send

while True:
    ready_to_read, ready_to_write, in_error = select.select(READ_SOCKET_LIST, [], [], 0)
    for sock in ready_to_read:
        # new connection to server
        if sock == server_socket:
            (new_sock, address) = server_socket.accept()
            READ_SOCKET_LIST.append(new_sock)
        else:
            # STDOUT Server Side
            Data = sock.recv(8000)

            # removing broken socket
            if not Data:
                if sock in READ_SOCKET_LIST:
                    READ_SOCKET_LIST.remove(sock)
                continue

            # Client is sending its name over
            if '$$$$' in Data:
                client_name = Data[4:]
                remote_to_name[str(sock.getpeername())] = client_name
                name_to_address[client_name] = sock.getsockname()
            # Client sending over message
            else:
                client_name = remote_to_name[str(sock.getpeername())]
                name_to_messages[client_name] = Data

                # Control Command
                message = Data.strip()
                if not message == '':
                    if message[0] == '/':
                        control_message = message[1:].split(" ")
                        if control_message[0] == 'create':
                            sock.sendall(create(control_message))
                        elif control_message[0] == 'list':
                            sock.sendall(list_channels())
                        elif control_message[0] == 'join':
                            sock.sendall(join_channel(control_message, client_name))
                        else:
                            sock.sendall(utils.SERVER_INVALID_CONTROL_MESSAGE.format(control_message))
                # Not a control Command. Regular message
                else:
                    # This sends to specific socket's address, not remote
                    name = remote_to_name[str(sock.getpeername())]
                    if name not in name_to_channel.keys():
                        sock.sendall(utils.SERVER_CLIENT_NOT_IN_CHANNEL)
                    else:
                        sock.sendall(Data)

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