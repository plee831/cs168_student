import socket
import sys
import utils
import select

NAME_TAG = '$$'
READ_SOCKET_LIST = []
client_sock = socket.socket()
client_name = NAME_TAG + sys.argv[1]
host = sys.argv[2]
port = int(sys.argv[3])
READ_SOCKET_LIST.append(client_sock)


def pad_message(message):
    while len(message) < utils.MESSAGE_LENGTH:
        message += " "
    return message[:utils.MESSAGE_LENGTH]


try:
    client_socket = client_sock.connect((host, port))
except socket.error, exc:
    print(utils.CLIENT_CANNOT_CONNECT.format(host, str(port)))
    pass
client_sock.send(pad_message(client_name))
leftover_chars = 0
current_data = ''
a = True
sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX)
sys.stdout.flush()
while True:
    ready_to_read, ready_to_write, in_error = select.select(READ_SOCKET_LIST, READ_SOCKET_LIST, [])
    for read_sock in ready_to_read:
        Data = read_sock.recv(200)
        if len(Data) == 0:
            sys.exit(utils.CLIENT_WIPE_ME[0] + utils.CLIENT_SERVER_DISCONNECTED.format(host, port))
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
        x = len(Data.strip().split("\n")[0])
        print(utils.CLIENT_WIPE_ME[0]
              + (Data.strip()
                 if len(utils.CLIENT_WIPE_ME) - 1 <= x
                 else Data[:x] + utils.CLIENT_WIPE_ME[1:] + Data.strip()[x:]))
        sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX)
        sys.stdout.flush()

    for write_sock in ready_to_write:
        if bool(select.select([sys.stdin], [], [], 0.0)[0]):
            raw_message_to_send = sys.stdin.readline()
            padded_message = pad_message(raw_message_to_send)
            write_sock.send(padded_message)
            sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX)
            sys.stdout.flush()

