import wan_optimizer
import utils


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
        self.CURRENT_BLOCK = ""
        self.hash_to_data = {}
        self.waiting_to_fill_block = False

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
            if len(self.CURRENT_BLOCK + packet.payload) <= WanOptimizer.BLOCK_SIZE:
                if len(self.CURRENT_BLOCK + packet.payload) == WanOptimizer.BLOCK_SIZE:
                    self.waiting_to_fill_block = False
                    temp_payload = self.CURRENT_BLOCK + packet.payload
                    self.CURRENT_BLOCK = ""
                    hashed_data = utils.get_hash(temp_payload)
                    if hashed_data in self.hash_to_data.keys():
                        packet.payload = self.hash_to_data[hashed_data]
                        packet.is_raw_data = False
                    else:
                        packet.payload = temp_payload
                else:
                    self.waiting_to_fill_block = True
                    self.CURRENT_BLOCK += packet.payload
            else:
                self.CURRENT_BLOCK += packet.payload[:(WanOptimizer.BLOCK_SIZE - len(self.CURRENT_BLOCK))]
                block_to_send = self.CURRENT_BLOCK
                hashed_data = utils.get_hash(block_to_send)
                # Check if the data in the dict. If yes, send HASH
                if hashed_data in self.hash_to_data.keys():
                    packet.payload = self.hash_to_data[hashed_data]
                    packet.is_raw_data = False
                # Store the data into the dict. Send data
                else:
                    self.hash_to_data[hashed_data] = block_to_send
                    self.CURRENT_BLOCK = packet.payload[(WanOptimizer.BLOCK_SIZE - len(self.CURRENT_BLOCK)):]
                    packet.payload = block_to_send
        # Received a Hash from WAN optimizer and not raw data.
        else:
            received_hash = packet.payload
            # Check if its in the dict. If it isn't, INVALID HASH
            if received_hash in self.hash_to_data.keys():
                raw_data = self.hash_to_data[received_hash]
                packet.payload = raw_data
            else:
                return
        if self.waiting_to_fill_block:
            if not packet.is_fin and len(self.CURRENT_BLOCK) == WanOptimizer.BLOCK_SIZE:
                return
            else:
                hashed_data = utils.get_hash(self.CURRENT_BLOCK)
                if hashed_data in self.hash_to_data.keys():
                    packet.payload = hashed_data
                    packet.is_raw_data = False
                else:
                    self.hash_to_data[hashed_data] = self.CURRENT_BLOCK
                    packet.payload = self.CURRENT_BLOCK
                self.CURRENT_BLOCK = ""
                self.waiting_to_fill_block = False
        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            self.send(packet, self.address_to_port[packet.dest])
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            self.send(packet, self.wan_port)

    # # Return the modified packet if seen. Else, return None
    # def block_seen_before(self, packet, non_hashed_data):
    #     hashed_data = utils.get_hash(non_hashed_data)
    #     # Check if the data in the dict. If yes, send HASH
    #     if hashed_data in self.hash_to_data.keys():
    #         packet.payload = self.hash_to_data[hashed_data]
    #         packet.is_raw_data = False
    #         return packet
    #     else:
    #         return None
