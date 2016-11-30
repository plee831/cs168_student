import wan_optimizer
import utils
from tcp_packet import Packet


class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into fixed-size blocks.

    This WAN optimizer should implement part 1 of project 4.
    """

    # Size of blocks to store, and send only the hash when the block has been
    # sent previously
    BLOCK_SIZE = 8000

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).
        # self.CURRENT_BLOCK = ""
        self.CURRENT_PAYLOAD = ""
        self.CURRENT_BLOCK = []
        self.CURRENT_BLOCK_BYTE_SIZE = 0
        self.hash_to_data = {}

    def send_block(self, list_of_packets, source, destination, is_fin=False):
        complete_block = ""
        for packet in list_of_packets:
            complete_block += packet.payload
        hashed_data = utils.get_hash(complete_block)
        # Check if the data in the dict. If yes, send only the HASH
        if hashed_data in self.hash_to_data.keys():
            hashed_data_packet = Packet(src=source,
                                        dest=destination,
                                        is_raw_data=False,
                                        is_fin=is_fin,
                                        payload=hashed_data)
            if hashed_data_packet.dest in self.address_to_port:
                # The packet is destined to one of the clients connected to this middlebox;
                # send the packet there.
                self.send(hashed_data_packet, self.address_to_port[hashed_data_packet.dest])
            else:
                # The packet must be destined to a host connected to the other middlebox
                # so send it across the WAN.
                self.send(hashed_data_packet, self.wan_port)
        # Store the data into the dict. Send the original data (by the packets)
        else:
            self.hash_to_data[hashed_data] = complete_block
            for packet in list_of_packets:
                if packet.dest in self.address_to_port:
                    # The packet is destined to one of the clients connected to this middlebox;
                    # send the packet there.
                    self.send(packet, self.address_to_port[packet.dest])
                else:
                    # The packet must be destined to a host connected to the other middlebox
                    # so send it across the WAN.
                    self.send(packet, self.wan_port)

    # The receiving WAN optimizer, when it gets raw data, will similarly compute the hash,
    # and store the mapping between the hash and the raw data.
    def receive(self, packet):
        """ Handles receiving a packet.

        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 1.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of 
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        # Data from CLIENT
        # collect enough data for a block. Then hash the block (storing mapping of hash->raw data)
        if packet.is_raw_data:
            old_payload = self.CURRENT_PAYLOAD
            self.CURRENT_PAYLOAD += packet.payload[:(utils.MAX_PACKET_SIZE - len(old_payload))]
            next_payload = packet.payload[(utils.MAX_PACKET_SIZE - len(old_payload)):]
            print "PACKET.PAYLOAD LENGTH: " + str(len(packet.payload))
            print "CURRENT PAYLOAD LENGHT: " + str(len(self.CURRENT_PAYLOAD))
            print "NEXT PAYLOAD LENGTH: " + str(len(next_payload))

            if len(self.CURRENT_PAYLOAD) + self.CURRENT_BLOCK_BYTE_SIZE < WanOptimizer.BLOCK_SIZE:

                # In the case that the packet has reached max size or its the final packet, send
                if len(self.CURRENT_PAYLOAD) == utils.MAX_PACKET_SIZE:
                    self.CURRENT_BLOCK.append(
                        Packet(packet.src, packet.dest, is_raw_data=True, is_fin=False, payload=self.CURRENT_PAYLOAD))

                    self.CURRENT_BLOCK_BYTE_SIZE += len(self.CURRENT_PAYLOAD)
                    self.CURRENT_PAYLOAD = next_payload

            elif len(self.CURRENT_PAYLOAD) + self.CURRENT_BLOCK_BYTE_SIZE == WanOptimizer.BLOCK_SIZE:
                self.CURRENT_BLOCK.append(
                    Packet(packet.src, packet.dest, is_raw_data=True, is_fin=False, payload=self.CURRENT_PAYLOAD))
                self.send_block(self.CURRENT_BLOCK, packet.src, packet.dest)

                self.CURRENT_BLOCK = []
                self.CURRENT_BLOCK_BYTE_SIZE = 0
                self.CURRENT_PAYLOAD = next_payload

            # len(self.CURRENT_PAYLOAD) + self.CURRENT_BLOCK_BYTE_SIZE > WanOptimizer.BLOCK_SIZE
            else:
                old_payload = self.CURRENT_PAYLOAD
                print "@@@@"
                print "SIZE LEFT in BLOCK: " + str(WanOptimizer.BLOCK_SIZE - self.CURRENT_BLOCK_BYTE_SIZE)
                print "PACKET PAYLOAD: " + str(len(packet.payload))
                payload_to_send = self.CURRENT_PAYLOAD[:(
                    WanOptimizer.BLOCK_SIZE - self.CURRENT_BLOCK_BYTE_SIZE)]
                payload_to_send = payload_to_send[:utils.MAX_PACKET_SIZE]
                print "PAYLOAD TO SEND: " + str(len(payload_to_send))
                self.CURRENT_PAYLOAD = old_payload[(
                    WanOptimizer.BLOCK_SIZE - self.CURRENT_BLOCK_BYTE_SIZE):] + next_payload
                self.CURRENT_BLOCK.append(
                    Packet(packet.src, packet.dest, is_raw_data=True, is_fin=False, payload=payload_to_send))
                self.send_block(self.CURRENT_BLOCK, packet.src, packet.dest)

                print "NEXT PAYLOAD: " + str(len(next_payload))
                print "CURRENT PAYLOAD: " + str(len(self.CURRENT_PAYLOAD))
                self.CURRENT_BLOCK = []
                self.CURRENT_BLOCK_BYTE_SIZE = 0
            if packet.is_fin:
                print "FIN"
                if next_payload == "":
                    self.CURRENT_BLOCK.append(
                        Packet(packet.src, packet.dest, is_raw_data=True, is_fin=True, payload=self.CURRENT_PAYLOAD))
                    for packet in self.CURRENT_BLOCK:
                        print packet
                    self.send_block(self.CURRENT_BLOCK, packet.src, packet.dest, is_fin=True)
                    self.CURRENT_PAYLOAD = ""
                    self.CURRENT_BLOCK = []
                    self.CURRENT_BLOCK_BYTE_SIZE = 0
                else:
                    self.CURRENT_BLOCK.append(
                        Packet(packet.src, packet.dest, is_raw_data=True, is_fin=False, payload=self.CURRENT_PAYLOAD))
                    self.send_block(self.CURRENT_BLOCK, packet.src, packet.dest)
                    # Send a block of the remaining bytes
                    self.CURRENT_BLOCK_BYTE_SIZE = len(next_payload)
                    self.CURRENT_BLOCK = [
                        Packet(packet.src, packet.dest, is_raw_data=True, is_fin=True, payload=next_payload)
                    ]
                    self.send_block(self.CURRENT_BLOCK, packet.src, packet.dest)
                    self.CURRENT_PAYLOAD = ""
                    self.CURRENT_BLOCK = []
                    self.CURRENT_BLOCK_BYTE_SIZE = 0
        # Received a Hash from WAN optimizer and not raw data.
        else:
            received_hash = packet.payload
            # Check if its in the dict. If it isn't, INVALID HASH
            if received_hash in self.hash_to_data.keys():
                raw_data = self.hash_to_data[received_hash]
                packet.payload = raw_data
                if packet.dest in self.address_to_port:
                    # The packet is destined to one of the clients connected to this middlebox;
                    # send the packet there.
                    self.send(packet, self.address_to_port[packet.dest])
                else:
                    # The packet must be destined to a host connected to the other middlebox
                    # so send it across the WAN.
                    self.send(packet, self.wan_port)
