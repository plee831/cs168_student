import socket
import sys
import select
import utils

READ_SOCKET_LIST = []

server_socket = socket.socket()
port = int(sys.argv[1])
server_socket.bind(('', port))
server_socket.listen(5)
READ_SOCKET_LIST.append(server_socket)

# remote address of socket to name
remote_to_name = {}
# name to socket address of socket
# name_to_address = {}
name_to_channel = {}
channels = set()
name_to_messages = {}
client_name = ''


def pad_message(message):
    while len(message) < utils.MESSAGE_LENGTH:
        message += " "
    return message[:utils.MESSAGE_LENGTH]


# broadcast chat messages to all connected clients
def broadcast(server_socket, sock, message):
    for socket in READ_SOCKET_LIST:
        # send the message only to peer
        if socket != server_socket and socket != sock:
            try:
                socket.send(pad_message(message))
            except socket.gaierror: # maybe different exception here
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in READ_SOCKET_LIST:
                    READ_SOCKET_LIST.remove(socket)


def create(c_message, c_name):
    msg_to_send = ''
    if len(c_message) == 1:
        msg_to_send = utils.SERVER_CREATE_REQUIRES_ARGUMENT
    else:
        chl = c_message[1]
        if chl in channels:
            msg_to_send = utils.SERVER_CHANNEL_EXISTS.format(chl)
        else:
            channels.add(chl)
            name_to_channel[c_name] = chl
    return pad_message(msg_to_send)


def list_channels(socket):
    msg_to_send = ''
    for c in channels:
        msg_to_send = msg_to_send + c + '\n'
    if msg_to_send != '':
        socket.send(pad_message(msg_to_send))


def join_channel(socket, channel, c_name):
    if channel in channels:
        for name in name_to_channel.keys():
            for inner_sock in READ_SOCKET_LIST:
                if name_to_channel[name] == channel:
                    if remote_to_name[str(inner_sock.getpeername())] == name:
                        if c_name != name:
                            inner_sock.send(pad_message(
                                utils.SERVER_CLIENT_JOINED_CHANNEL.format(name)))
        if c_name in name_to_channel.keys():
            old_channel = name_to_channel[c_name]
            for name in name_to_channel.keys():
                for inner_sock in READ_SOCKET_LIST:
                    if name_to_channel[name] == old_channel:
                        if remote_to_name[str(inner_sock.getpeername())] == name:
                            if c_name != name:
                                inner_sock.send(pad_message(utils.SERVER_CLIENT_LEFT_CHANNEL.format(name)))
            name_to_channel[c_name] = channel
    else:
        socket.send(pad_message(utils.SERVER_NO_CHANNEL_EXISTS.format(channel)))


current_data = ''
leftover_chars = 0
while True:
    ready_to_read, ready_to_write, in_error = select.select(READ_SOCKET_LIST, [], [], 0)
    for sock in ready_to_read:
        # new connection to server
        if sock == server_socket:
            (new_sock, address) = server_socket.accept()
            READ_SOCKET_LIST.append(new_sock)
        else:
            Data = sock.recv(200)
            if not Data:
                continue
            chars_recv = len(Data)
            if leftover_chars + chars_recv < 200:
                leftover_chars += chars_recv
                current_data = current_data + Data
                continue
            elif leftover_chars + chars_recv == 200:
                Data = current_data + Data[:chars_recv]
                leftover_chars = 0
                current_data = ''
            else:
                new_data = current_data + Data[:(200-leftover_chars)]
                leftover_chars = leftover_chars+chars_recv-200
                current_data = Data[-leftover_chars:]
                Data = new_data
            # STDOUT Server Side
            if '$$' in Data:
                client_name = Data[4:]
                remote_to_name[str(sock.getpeername())] = client_name
                # name_to_address[client_name] = sock.getsockname()
            else:
                remote_to_name[str(sock.getpeername())] = client_name
                name_to_messages[client_name] = Data
                if Data[0] == '/':
                    control_message = Data[1:].strip().split(" ")
                    if control_message[0] == 'create' and len(control_message) == 2:
                        sock.send(create(pad_message(control_message), client_name))
                    elif control_message[0] == 'list' and len(control_message) == 1:
                        list_channels(socket)
                    elif control_message[0] == 'join':
                        if len(control_message) == 1:
                            sock.send(pad_message(utils.SERVER_JOIN_REQUIRES_ARGUMENT))
                        else:
                            join_channel(sock, control_message[1], client_name)
                    else:
                        sock.sendall(pad_message(utils.SERVER_INVALID_CONTROL_MESSAGE.format(control_message)))
                else:
                    # This sends to specific socket's address, not remote
                    name = remote_to_name[str(sock.getpeername())]
                    if name not in name_to_channel.keys():
                        sock.send(pad_message(utils.SERVER_CLIENT_NOT_IN_CHANNEL))

                    else:
                        # broadcast(server_socket, sock, '[' + name + '] ' + Data)
                        sock.send(pad_message(Data))

# The first message that the server receives
# from the client should be used as the client's name.


