import socket
import sys
import utils
import select

NAME_TAG = '$$$$'

client_sock = socket.socket()
client_name = NAME_TAG + sys.argv[1]
host = sys.argv[2]
port = int(sys.argv[3])

try:
    client_socket = client_sock.connect((host, port))
except socket.error, exc:
    print(utils.CLIENT_CANNOT_CONNECT.format(host, str(port)))
    pass
client_sock.send(client_name)
while True:
    print("begin")
    ready_to_read, ready_to_write, in_error = select.select([client_sock], [client_sock], [], 0)
    for write_sock in ready_to_write:
        raw_message_to_send = raw_input()
        print('writing ' + raw_message_to_send)
        if len(raw_message_to_send) != 200:
            padded_message_to_send = raw_message_to_send.ljust(200, ' ')
        write_sock.send(padded_message_to_send)
        print(utils.CLIENT_MESSAGE_PREFIX + raw_message_to_send)
    for read_sock in ready_to_read:
        # data = client_sock.recv(1024)
        data = read_sock.recv(1024)
        if not data:
            print('please')
            break
        else:
            print(data.strip())
