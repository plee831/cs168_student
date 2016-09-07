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
    ready_to_read, ready_to_write, in_error = select.select([], [client_sock], [], 0)
    # for read_sock in ready_to_read:
    #     print('READING')
    #     (new_sock, address) = read_sock.accept()
    #     Data = new_sock.recv(1024)
    #     # TODO something with the data
    #     print(Data)
    for write_sock in ready_to_write:
        raw_message_to_send = raw_input()
        if len(raw_message_to_send) != 200:
            padded_message_to_send = raw_message_to_send.ljust(200, ' ')
        write_sock.send(padded_message_to_send)
        print(utils.CLIENT_MESSAGE_PREFIX + raw_message_to_send)

    data = client_sock.recv(1024)
    if not data:
        break
    else:
        print(data)
