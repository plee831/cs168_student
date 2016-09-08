import socket
import sys
import utils
import client_split_messages
from client_split_messages import ChatClientSplitMessages
import select
import errno

NAME_TAG = '$$$$'

client_sock = socket.socket()
client_name = NAME_TAG + sys.argv[1]
host = sys.argv[2]
port = int(sys.argv[3])
ccsm = ChatClientSplitMessages(host, port)

try:
    client_socket = client_sock.connect((host, port))
except socket.error, exc:
    print(utils.CLIENT_CANNOT_CONNECT.format(host, str(port)))
    pass
ccsm.send_split_message(client_sock, client_name)
while True:
    try:
        ready_to_read, ready_to_write, in_error = select.select([client_sock], [client_sock], [])
        for read_sock in ready_to_read:
            # data = client_sock.recv(1024)
            data = read_sock.recv(200).strip()
            if not data:
                break
            print(data)

        for write_sock in ready_to_write:
            raw_message_to_send = raw_input()
            padded_message = client_split_messages.pad_message(raw_message_to_send)
            ccsm.send_split_message(write_sock, padded_message)
            # print(utils.CLIENT_MESSAGE_PREFIX + raw_message_to_send)
    except select.error, e:
        if e.errno == errno.ECONNRESET:
            print(utils.CLIENT_SERVER_DISCONNECTED.format(host, port))

