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

remote_to_name = {}
name_to_sock = {}
name_to_channel = {}
channels = set()
name_to_messages = {}
client_name = ''


def pad_message(message):
    while len(message) < utils.MESSAGE_LENGTH:
        message += " "
    return message[:utils.MESSAGE_LENGTH]


def broadcast(client_name, channel, message):
    if client_name in name_to_channel.keys():
        if channel in channels:
            for name in name_to_channel.keys():
                if name_to_channel[name] == channel:
                    if client_name != name:
                        name_to_sock[name].send(pad_message(message))


def create(channel, c_name, sock):
    if channel in channels:
        sock.send(pad_message(utils.SERVER_CHANNEL_EXISTS.format(channel)))
    else:
        channels.add(channel)
        name_to_channel[c_name] = channel


def list_channels(socket):
    msg_to_send = ''
    for c in channels:
        msg_to_send = msg_to_send + c + '\n'
    if msg_to_send != '':
        socket.send(pad_message(msg_to_send))


def join_channel(socket, channel, client_name):
    old_channel = ''
    if channel in channels:
        if client_name in name_to_channel.keys():
            old_channel = name_to_channel[client_name]
        name_to_channel[client_name] = channel
        broadcast(client_name, channel, utils.SERVER_CLIENT_JOINED_CHANNEL.format(client_name))
        if old_channel != '':
            broadcast(client_name, old_channel, utils.SERVER_CLIENT_LEFT_CHANNEL.format(client_name))
    else:
        socket.send(pad_message(utils.SERVER_NO_CHANNEL_EXISTS.format(channel)))


current_data = ''
leftover_chars = 0
while True:
    ready_to_read, ready_to_write, in_error = select.select(READ_SOCKET_LIST, [], [], 0)
    for sock in ready_to_read:
        if sock == server_socket:
            (new_sock, address) = server_socket.accept()
            READ_SOCKET_LIST.append(new_sock)
        else:  
            Data = sock.recv(200)
            if len(Data) == 0:
                disconnected_name = remote_to_name[str(sock.getpeername())]
                sock = name_to_sock[disconnected_name]
                channel = name_to_channel[disconnected_name]
                READ_SOCKET_LIST.remove(sock)
                broadcast(disconnected_name, channel, utils.SERVER_CLIENT_LEFT_CHANNEL.format(disconnected_name))
                name_to_channel.pop(disconnected_name)
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
            if '$$' in Data:
                client_name = Data[2:].strip()
                remote_to_name[str(sock.getpeername())] = client_name
                name_to_sock[client_name] = sock
            else:
                print(client_name, len(client_name))
                client_name = remote_to_name[str(sock.getpeername())]
                name_to_messages[client_name] = Data
                if Data[0] == '/':
                    control_message = Data[1:].strip().split(" ")
                    if control_message[0] == 'create':
                        if len(control_message) == 1:
                            sock.send(pad_message(utils.SERVER_CREATE_REQUIRES_ARGUMENT))
                        else:
                            create(control_message[1], client_name, sock)
                    elif control_message[0] == 'list' and len(control_message) == 1:
                        list_channels(sock)
                    elif control_message[0] == 'join':
                        if len(control_message) == 1:
                            sock.send(pad_message(utils.SERVER_JOIN_REQUIRES_ARGUMENT))
                        else:
                            join_channel(sock, control_message[1], client_name)
                    else:
                        sock.sendall(pad_message(utils.SERVER_INVALID_CONTROL_MESSAGE.format(control_message)))
                else:
                    name = remote_to_name[str(sock.getpeername())]
                    if name not in name_to_channel.keys():
                        sock.send(pad_message(utils.SERVER_CLIENT_NOT_IN_CHANNEL))

                    else:
                        broadcast(client_name, name_to_channel[client_name], '[' + name + '] ' + Data)



