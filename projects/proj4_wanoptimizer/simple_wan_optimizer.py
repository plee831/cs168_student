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
        self.buffers = {}
        self.hash_to_block = {}

    def send_packet(self, packet):
        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            self.send(packet, self.address_to_port[packet.dest])
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            self.send(packet, self.wan_port)

    def send_block(self, list_of_packets, source, destination, is_fin):
        complete_block = ""
        for packet in list_of_packets:
            complete_block += packet.payload
        hashed_data = utils.get_hash(complete_block)
        if hashed_data in self.hash_to_block.keys():
            hashed_packet = Packet(src=source, dest=destination, is_raw_data=False, is_fin=is_fin, payload=hashed_data)
            self.send_packet(hashed_packet)
        else:
            self.hash_to_block[hashed_data] = complete_block
            for packet in list_of_packets:
                self.send_packet(packet)

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
        if packet.is_raw_data:
            if (packet.src, packet.dest) not in self.buffers.keys():
                self.buffers[(packet.src, packet.dest)] = {}
                self.buffers[(packet.src, packet.dest)]["packets"] = []
                self.buffers[(packet.src, packet.dest)]["length"] = 0
            if packet.is_fin or packet.size() + self.buffers[(packet.src, packet.dest)]["length"] > WanOptimizer.BLOCK_SIZE:
                if packet.is_fin:
                    split_payload_1 = packet.payload[
                                      :(WanOptimizer.BLOCK_SIZE - self.buffers[(packet.src, packet.dest)]["length"])]
                    split_payload_2 = packet.payload[
                                      (WanOptimizer.BLOCK_SIZE - self.buffers[(packet.src, packet.dest)]["length"]):]
                    packet_to_send = Packet(src=packet.src, dest=packet.dest, is_raw_data=True, is_fin=False,
                                            payload=split_payload_1)
                    self.buffers[(packet.src, packet.dest)]["packets"].append(packet_to_send)
                    self.buffers[(packet.src, packet.dest)]["length"] += packet_to_send.size()
                    self.send_block(self.buffers[(packet.src, packet.dest)]["packets"], packet.src, packet.dest,
                                    is_fin=False)
                    packet_for_later = Packet(src=packet.src, dest=packet.dest, is_raw_data=True, is_fin=packet.is_fin,
                                              payload=split_payload_2)

                    self.buffers[(packet.src, packet.dest)]["packets"] = [packet_for_later]
                    self.send_block(self.buffers[(packet.src, packet.dest)]["packets"], packet.src, packet.dest,
                                    is_fin=packet.is_fin)
                    self.buffers[(packet.src, packet.dest)]["length"] = 0
                    self.buffers[(packet.src, packet.dest)]["packets"] = []
                else:
                    split_payload_1 = packet.payload[
                                      :(WanOptimizer.BLOCK_SIZE - self.buffers[(packet.src, packet.dest)]["length"])]
                    split_payload_2 = packet.payload[
                                      (WanOptimizer.BLOCK_SIZE - self.buffers[(packet.src, packet.dest)]["length"]):]
                    packet_to_send = Packet(src=packet.src, dest=packet.dest, is_raw_data=True, is_fin=False,
                                            payload=split_payload_1)
                    self.buffers[(packet.src, packet.dest)]["packets"].append(packet_to_send)
                    self.buffers[(packet.src, packet.dest)]["length"] += packet_to_send.size()

                    self.send_block(self.buffers[(packet.src, packet.dest)]["packets"], packet.src, packet.dest,
                                    is_fin=False)
                    packet_for_later = Packet(src=packet.src, dest=packet.dest, is_raw_data=True, is_fin=False,
                                              payload=split_payload_2)
                    self.buffers[(packet.src, packet.dest)]["length"] = packet_for_later.size()
                    self.buffers[(packet.src, packet.dest)]["packets"] = [packet_for_later]
            else:
                self.buffers[(packet.src, packet.dest)]["length"] += packet.size()
                self.buffers[(packet.src, packet.dest)]["packets"].append(packet)
        else:
            if packet.payload in self.hash_to_block.keys():
                raw_data = self.hash_to_block[packet.payload]
                while raw_data is not "":
                    print len(raw_data)
                    if len(raw_data) <= utils.MAX_PACKET_SIZE:
                        print packet.is_fin
                        temp_packet = Packet(src=packet.src, dest=packet.dest, is_raw_data=True, is_fin=packet.is_fin,
                                             payload=raw_data[:utils.MAX_PACKET_SIZE])
                    else:
                        temp_packet = Packet(src=packet.src, dest=packet.dest, is_raw_data=True, is_fin=False,
                                             payload=raw_data[:utils.MAX_PACKET_SIZE])
                    raw_data = raw_data[utils.MAX_PACKET_SIZE:]
                    self.send_packet(temp_packet)
