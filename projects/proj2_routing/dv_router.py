"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter(basics.DVRouterBase):
    NO_LOG = True  # Set to True on an instance to disable its logging
    POISON_MODE = False  # Can override POISON_MODE here
    DEFAULT_TIMER_INTERVAL = 5  # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.

        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
        self.routing_table = {}
        self.ports = {}

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        self.ports[port] = latency
        # TODO add in logic of sending update of routing table

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        del self.ports[port]
        for key in self.routing_table:
            if self.routing_table[key] == port:
                del self.routing_table[key]
        # TODO add in logic of sending update of routing table

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            if packet.src not in self.routing_table:
                self.routing_table[packet.src] = port
            if packet.dst in self.routing_table:
                self.send(packet, self.routing_table[packet.dst], flood=False)
        elif isinstance(packet, basics.HostDiscoveryPacket):
            pass
        else:
            # Totally wrong behavior for the sake of demonstration only: send
            # the packet back to where it came from!
            if packet.dst in self.routing_table:
                self.send(packet, port=self.routing_table[packet.dst])

    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        pass
