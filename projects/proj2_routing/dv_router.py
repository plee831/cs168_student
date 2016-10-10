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
        self.routing_table = {}  # destination: latency, port, current time
        self.ports = {}  # port to latency
        self.neighbors = {}  # port to source

        # Another thought : destination: latency, next_hop, for the routing table, do we need port?

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.
        The port attached to the link and the link latency are passed
        in.
        """
        print "handling this port: " + str(port)
        self.ports[port] = latency

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.
        The port number used by the link is passed in.
        """
        print self
        print ("FAILURE " + str(port))
        print self.neighbors
        deleted_destination = None
        for neighbor_port in self.neighbors.keys():
            if neighbor_port == port:
                print "GGGGG"
                deleted_destination = self.neighbors[neighbor_port][0]
                del self.neighbors[neighbor_port]
        for neighbor in self.neighbors.keys():
            print deleted_destination
            if deleted_destination is not None:
                self.send(basics.RoutePacket(deleted_destination, -1), neighbor, flood=False)
        if port in self.ports: 
            del self.ports[port]

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.
        packet is a Packet (or subclass).
        port is the port number it arrived on.
        You definitely want to fill this in.
        """
        self.log("RX %s on %s (%s)", packet, port, api.current_time())
        print str(port) + " YO YO Y OY OYO YO YO YOY OY O"
        if isinstance(packet, basics.RoutePacket):  # .dst = none
            self.neighbors[port] = (packet.src, packet.dst)
            if packet.latency == -1:
                print "@@@@@@@@@@@@@"
                for neighbor in self.neighbors.keys():
                    del self.routing_table[packet.destination]
                    self.send(basics.RoutePacket(packet.destination, -1), self.neighbors(neighbor)[1])
            destinations = []
            for dst in self.routing_table.keys():
                destinations.append(self.routing_table[dst][1])

            self.routing_table[packet.destination] = (packet.latency, port, api.current_time())

            if packet.destination not in self.routing_table:
                self.routing_table[packet.destination] = (packet.latency, port, api.current_time())
            else:
                old_latency = self.routing_table[packet.destination][0]

                new_latency = self.routing_table[packet.destination][0] + packet.latency
                if old_latency > new_latency:
                    self.routing_table[packet.destination] = (new_latency, port, api.current_time())
            self.send(basics.RoutePacket(packet.destination, self.routing_table[packet.destination][0]), destinations,
                      flood=False)

        elif isinstance(packet, basics.HostDiscoveryPacket):
            # https://piazza.com/class/iq6sgotn6pp37f?cid=463
            print "Host Discovery Packet $$$$"
            print str(port) + " HP"
            if port not in self.neighbors.keys():
                self.neighbors[port] = (packet.src, packet.dst)
                print str(self.neighbors[port]) + " " + str(port)
                print ("@@@@")
                print self.routing_table.keys()
                print self.neighbors.keys()
                for neighbor in self.neighbors.keys():
                    self.send(basics.RoutePacket(destination=packet.src,
                                                 latency=self.ports[neighbor]
                                                 ), port=port, flood=True)
        else:
            found_host = False
            for port in self.neighbors.keys():
                if packet.src != packet.dst:
                    if self.neighbors[port][0] == packet.dst:
                        found_host = True
                        self.send(packet, port=port)
            if not found_host:
                if packet.dst in self.routing_table.keys():
                    self.send(packet, self.routing_table[packet.dst][1])

    def handle_timer(self):
        """
        Called periodically.
        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.
        """
        for dst in self.routing_table.keys():
            received_time = self.routing_table[dst][2]
            if api.current_time() - received_time > self.ROUTE_TIMEOUT:
                del self.routing_table[dst]
