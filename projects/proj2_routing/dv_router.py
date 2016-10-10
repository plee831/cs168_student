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
        self.port_to_latency = {}  # port to latency
        self.hosts_to_route = {}  # host to (destination, port)
        self.host_to_port = {}  # host to port
        # Another thought : destination: latency, next_hop, for the routing table, do we need port?

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.
        The port attached to the link and the link latency are passed
        in.
        """
        print "handling this port: " + str(port)
        self.port_to_latency[port] = latency

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.
        The port number used by the link is passed in.
        """
        # deleted_destination = None
        # for host in self.host_to_port.keys():
        #     if self.host_to_port[host] == port:
        #         deleted_destination = host
        #         del self.host_to_port[host]
        # for host in self.host_to_port.keys():
        #     if deleted_destination is not None:
        #         self.send(basics.RoutePacket(deleted_destination, -1), self.host_to_port[host], flood=False)
        if port in self.port_to_latency: 
            del self.port_to_latency[port]

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.
        packet is a Packet (or subclass).
        port is the port number it arrived on.
        You definitely want to fill this in.
        """
        self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):  # .dst = none
            # if packet.latency == -1:
            #     for host in self.host_to_port.keys():
            #         del self.hosts_to_route[host]
            #         self.send(basics.RoutePacket(packet.destination, -1), self.host_to_port[host])
            destinations = []
            for host in self.hosts_to_route.keys():
                destinations.append(self.hosts_to_route[host][1])
            if packet.src not in self.hosts_to_route.keys():
                self.hosts_to_route[packet.src] = (packet.destination, port, api.current_time())
            else:
                old_latency = self.port_to_latency[self.hosts_to_route[packet.src][1]]
                new_latency = self.port_to_latency[self.hosts_to_route[packet.src][1]] + packet.latency
                if old_latency > new_latency:
                    self.hosts_to_route[packet.src] = (packet.destination, port, api.current_time())
                    self.port_to_latency[port] = new_latency
            self.send(basics.RoutePacket(packet.destination,
                                         self.port_to_latency[self.hosts_to_route[packet.src][1]]),
                      destinations,
                      flood=False)

        elif isinstance(packet, basics.HostDiscoveryPacket):
            # https://piazza.com/class/iq6sgotn6pp37f?cid=463
            print "Host Discovery Packet $$$$"
            print str(port) + " HP"
            if packet.src not in self.host_to_port:
                self.host_to_port[packet.src] = port
            for host in self.host_to_port.keys():
                self.send(basics.RoutePacket(
                    destination=host,
                    latency=self.port_to_latency[self.host_to_port[host]]),
                    port=self.host_to_port[host]
                )

            # if port not in self.neighbors.keys():
            #     self.neighbors[port] = (packet.src, packet.dst)
            #     for neighbor in self.neighbors.keys():
            #         self.send(basics.RoutePacket(destination=packet.src,
            #                                      latency=self.port_to_latency[neighbor]
            #                                      ), port=neighbor)
        else:
            found_host = False
            for host in self.host_to_port.keys():
                if packet.src != packet.dst:
                    if host == packet.dst:
                        found_host = True
                        self.send(packet, port=port)
            if not found_host:
                print self.hosts_to_route
                if packet.dst in self.hosts_to_route.keys():
                    print (" $!$!$!: " + self.hosts_to_route[packet.dst])
                    self.send(packet, self.hosts_to_route[packet.dst][1])

    def handle_timer(self):
        """
        Called periodically.
        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.
        """
        for host in self.hosts_to_route.keys():
            received_time = self.hosts_to_route[host][2]
            if api.current_time() - received_time > self.ROUTE_TIMEOUT:
                del self.hosts_to_route[host]
