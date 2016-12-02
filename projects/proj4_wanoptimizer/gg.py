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

        # Some kind of dictionary for seen blocks
        # {hash : block}
        self.hash_to_data = {}

        # Buffer for each client "dest"
        # {[packet.src, packet.dest] : {'packets' : [], 'length' : Int}}
        self.buffers = {}

        # Need different result_packets for WAN-to-WAN and WAN-to-CLIENT
        # How come?

        # Also when creating packets to send, must differentiate between if youre sending
        # to another client or if you are sending to another WAN

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
        if not packet.is_raw_data:
            if packet.dest in self.address_to_port:
                # Can't we assume that we have the hash?
                block = self.hash_to_data[packet.payload]
                packets = []
                while len(block) > utils.MAX_PACKET_SIZE:
                    packets.append(Packet(packet.src, packet.dest, True, False, block[:utils.MAX_PACKET_SIZE]))
                    block = block[utils.MAX_PACKET_SIZE:]
                packets.append(Packet(packet.src, packet.dest, True, packet.is_fin, block))
                for pack in packets:
                    self.send(pack, self.address_to_port[packet.dest])
        else:
            packet_to_send = packet
            packet_for_later = None
            if (packet.src, packet.dest) not in self.buffers.keys():
                self.buffers[(packet.src, packet.dest)] = {}
                self.buffers[(packet.src, packet.dest)]["packets"] = []
                self.buffers[(packet.src, packet.dest)]["length"] = 0

            # Checking if packet needs to be split
            if packet.size() + self.buffers[(packet.src, packet.dest)]["length"] > WanOptimizer.BLOCK_SIZE:
                diff = WanOptimizer.BLOCK_SIZE - self.buffers[(packet.src, packet.dest)]["length"]
                # Result should not be True ever
                packet_to_send = Packet(packet.src, packet.dest, packet.is_raw_data, False, packet.payload[:diff])
                packet_for_later = Packet(packet.src, packet.dest, packet.is_raw_data, packet.is_fin, packet.payload[diff:])

            # Checking if source, destination has been seen before:
            self.buffers[(packet.src, packet.dest)]['packets'].append(packet_to_send)
            self.buffers[(packet.src, packet.dest)]['length'] += packet.size()

            # Checking if we have met block size limit and must therefore send
            if packet.is_fin or self.buffers[(packet.src, packet.dest)]['length'] >= WanOptimizer.BLOCK_SIZE:
                packets = self.buffers[(packet.src, packet.dest)]['packets']

                # Create block
                block = ""
                for pack in packets:
                    block += pack.payload

                # If block is in our self.hash_to_data
                if block in self.hash_to_data.values():
                    if packet.dest in self.address_to_port:
                        for pack in packets:
                            self.send(pack, self.address_to_port[pack.dest])
                    else:
                        for hash_key, block_val in self.hash_to_data.iteritems():
                            if block == block_val:
                                hash_packet = Packet(packet.src, packet.dest, False, packet.is_fin, hash_key)
                                break
                        self.send(hash_packet, self.wan_port)

                # If seeing packets for the first time
                else:
                    # Store hash and block to self.hash_to_data
                    self.hash_to_data[utils.get_hash(block)] = block

                    # Send the packets
                    for pack in packets:
                        if packet.dest in self.address_to_port:
                            self.send(pack, self.address_to_port[pack.dest])
                        else:
                            self.send(pack, self.wan_port)

                # Reset after sending out buffer
                self.buffers[(packet.src, packet.dest)]['packets'] = []
                self.buffers[(packet.src, packet.dest)]['length'] = 0
                if packet_for_later:
                    self.buffers[(packet.src, packet.dest)]['packets'] = [packet_for_later]
                    self.buffers[(packet.src, packet.dest)]['length'] = packet_for_later.size()
