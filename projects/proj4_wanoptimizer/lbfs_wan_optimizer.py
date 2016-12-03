import wan_optimizer

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into variable-sized
    blocks based on the contents of the file.

    This WAN optimizer should implement part 2 of project 4.
    """

    # The string of bits to compare the lower order 13 bits of hash to
    GLOBAL_MATCH_BITSTRING = '0111011001010'

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).
        return

    def receive(self, packet):
        """ Handles receiving a packet.

        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 2.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of 
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        """
        dictionary: key = (source, destination), value = [complete_data, block_start_index, block_end_index]
        for each source, destination pair:
            build complete_data until final packet arrives      !this might take too much space

            while (block_end_index < len(complete_data)):
                1.  block = complete_data[block_start_index:block_end_index]
                2.  block_hash = utils.get_hash(block) 
                3.  block_key = last(lower) 13 bits of block_hash
                4.  while (block_key != delimiter AND block_end_index < len(complete_data)):
                        block_hash = block.hash()
                        i++;
                5.  if block_hash in dictionary:
                        send block_hash
                    else: 
                        add block to dictionary
                        send out the whole block
                    increment block_start_index
                    increment block_end_index 

        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            self.send(packet, self.address_to_port[packet.dest])
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            self.send(packet, self.wan_port)
