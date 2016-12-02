import wan_optimizer
import utils
import tcp_packet


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
        self.blocks = {}
        self.hash_to_data = {}

    def src_dest_data_read(self, packet):
        if not (packet.src, packet.dest) in self.blocks.keys():
            self.blocks[(packet.src, packet.dest)] = ["", "", 0, []]

        src_dest_data = self.blocks[(packet.src, packet.dest)]
        text_buffer = src_dest_data[0]
        text_buffer_overflow = src_dest_data[1]
        text_buffer_len = src_dest_data[2]
        block = src_dest_data[3]
        return text_buffer, text_buffer_overflow, text_buffer_len, block

    def src_dest_data_write(self, packet, src_dest_data):
        self.blocks[(packet.src, packet.dest)] = src_dest_data

    def fill_buffer(self, packet):
        text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)

        if (text_buffer_len + packet.size()) <= WanOptimizer.BLOCK_SIZE:
            text_buffer = text_buffer + packet.payload
        else:
            remaining_space = WanOptimizer.BLOCK_SIZE - text_buffer_len
            text_buffer = text_buffer + packet.payload[:remaining_space]
            text_buffer_overflow = packet.payload[remaining_space:]

        text_buffer_len = len(text_buffer)

        src_dest_data = [text_buffer, text_buffer_overflow, text_buffer_len, block]
        self.src_dest_data_write(packet, src_dest_data)

    def hash_block(self, packet):
        text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)

        hashcode = utils.get_hash(text_buffer)
        self.hash_to_data[hashcode] = text_buffer

        src_dest_data = [text_buffer, text_buffer_overflow, text_buffer_len, block]
        self.src_dest_data_write(packet, src_dest_data)

    def reset_buffers(self, packet):
        text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)

        text_buffer = text_buffer_overflow
        text_buffer_len = len(text_buffer)
        text_buffer_overflow = ""
        block = []

        src_dest_data = [text_buffer, text_buffer_overflow, text_buffer_len, block]
        self.src_dest_data_write(packet, src_dest_data)

    def flush_buffer(self, packet):
        text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)
        self.split_and_send_data(packet, text_buffer)

    def split_and_send_data(self, packet, data):
        text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)
        data_len = len(data)

        num_of_full_packets = data_len / utils.MAX_PACKET_SIZE
        size_of_last_packet = data_len - num_of_full_packets * utils.MAX_PACKET_SIZE
        for i in range(0, num_of_full_packets):
            start = i * utils.MAX_PACKET_SIZE
            end = start + utils.MAX_PACKET_SIZE
            payload = data[start:end]
            curr_packet = tcp_packet.Packet(src=packet.src,
                                            dest=packet.dest,
                                            is_raw_data=True,
                                            is_fin=False,
                                            payload=payload)
            self.staff_send(curr_packet)
        last_payload_start = num_of_full_packets * utils.MAX_PACKET_SIZE
        last_payload_end = last_payload_start + size_of_last_packet
        last_payload = data[last_payload_start:last_payload_end]
        last_packet = tcp_packet.Packet(src=packet.src,
                                        dest=packet.dest,
                                        is_raw_data=True,
                                        is_fin=packet.is_fin,
                                        payload=last_payload)
        self.staff_send(last_packet)

    def staff_send(self, packet):
        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox
            # send the packet there.
            self.send(packet, self.address_to_port[packet.dest])
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            self.send(packet, self.wan_port)

    def receive(self, packet):
        """ Handles receiving a packet.

        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 1.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of 
        the WAN this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        if packet.is_raw_data:
            text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)

            block.append(packet)

            self.fill_buffer(packet)
            text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)

            buffer_flushed = False
            if text_buffer_len == WanOptimizer.BLOCK_SIZE:
                hashcode = utils.get_hash(text_buffer)

                # ERIC: Set curr_is_fin for the packet_with_hash
                curr_is_fin = packet.is_fin

                if len(text_buffer_overflow) > 0:
                    curr_is_fin = False

                if hashcode in self.hash_to_data.keys():
                    packet_with_hash = tcp_packet.Packet(src=packet.src,
                                                         dest=packet.dest,
                                                         is_raw_data=False,
                                                         is_fin=curr_is_fin,
                                                         payload=hashcode)
                    self.staff_send(packet_with_hash)
                else:
                    # self.send_raw_data_block(packet)
                    self.flush_buffer(packet)
                    self.hash_block(packet)
                buffer_flushed = True

            # ERIC: Reset the buffers here but also check if packet.is_fin.
            # If the packet.is_fin, then we check to see if there's unsent data.
            # If there is unsent data, then we hash the remaining data and send it out.
            if packet.is_fin:
                if buffer_flushed:
                    self.reset_buffers(packet)
                    text_buffer, text_buffer_overflow, text_buffer_len, block = self.src_dest_data_read(packet)

                hashcode = self.hash_block

                if hashcode in self.hash_to_data.keys():
                    packet.payload = hashcode
                    self.staff_send(packet)
                else:
                    self.flush_buffer(packet)
                self.reset_buffers(packet)
            else:
                if buffer_flushed:
                    self.reset_buffers(packet)
        else:
            received_hash = packet.payload
            # Check if its in the dict. If it isn't, INVALID HASH
            if received_hash in self.hash_to_data.keys():
                if packet.dest in self.address_to_port:  # ERIC: If we are sending to a client, then we don't send the hash
                    # The packet is destined to one of the clients connected to this middlebox
                    # send the packet there.
                    raw_data = self.hash_to_data[received_hash]
                    self.split_and_send_data(packet, raw_data)
                else:
                    # The packet must be destined to a host connected to the other middlebox
                    # so send it across the WAN.
                    self.staff_send(packet)
