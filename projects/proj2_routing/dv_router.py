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
        self.port_to_latency = {}
        self.hosts_to_route = {}
        self.poison_state = {}

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.
        The port attached to the link and the link latency are passed in.
        """
        self.port_to_latency[port] = latency
        for host in self.hosts_to_route.keys():
            self.send(basics.RoutePacket(host, self.hosts_to_route[host][0]), port)

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.
        The port number used by the link is passed in.
        """
        if not self.POISON_MODE:
            for host in self.hosts_to_route.keys():
                if self.hosts_to_route[host][1] == port:
                    del self.hosts_to_route[host]
        else:
            for host in self.hosts_to_route.keys():
                if self.hosts_to_route[host][1] == port:
                    self.poison_state[host] = self.hosts_to_route[host]
                    self.send(basics.RoutePacket(host, INFINITY), flood=True)
                    del self.hosts_to_route[host]
        del self.port_to_latency[port]

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.
        packet is a Packet (or subclass).
        port is the port number it arrived on.
        You definitely want to fill this in.
        """
        if isinstance(packet, basics.RoutePacket):
            if packet.latency + self.port_to_latency[port] < INFINITY:
                if packet.destination in self.poison_state and self.POISON_MODE:
                    del self.poison_state[packet.destination]
                if self.POISON_MODE:
                    self.send(basics.RoutePacket(packet.destination, INFINITY), port)
                if packet.destination not in self.hosts_to_route.keys() \
                        or self.hosts_to_route[packet.destination][0] > packet.latency + self.port_to_latency[port]:
                    temp_packet = basics.RoutePacket(packet.destination, self.port_to_latency[port] + packet.latency)
                    self.hosts_to_route[packet.destination] = [temp_packet.latency, port, api.current_time()]
                    self.send(temp_packet, port, flood=True)
                else:
                    if self.hosts_to_route[packet.destination][1] == port:
                        self.hosts_to_route[packet.destination][2] = api.current_time()
                        if packet.latency + self.port_to_latency[port] > self.hosts_to_route[packet.destination][0]:
                            self.hosts_to_route[packet.destination][0] = packet.latency + self.port_to_latency[port]
                            self.send(basics.RoutePacket(
                                packet.destination, self.port_to_latency[port] + packet.latency), port, flood=True)
            elif packet.latency >= INFINITY and self.POISON_MODE:
                for host in self.hosts_to_route.keys():
                    if host == packet.destination:
                        if self.hosts_to_route[host][1] == port:
                            poison = basics.RoutePacket(packet.destination, INFINITY)
                            self.send(poison, port, flood=True)
                            self.poison_state[host] = self.hosts_to_route[host]
                            del self.hosts_to_route[host]

        elif isinstance(packet, basics.HostDiscoveryPacket):
            self.hosts_to_route[packet.src] = [self.port_to_latency[port], port, -1]
            route = basics.RoutePacket(packet.src, self.port_to_latency[port])
            self.send(route, port, flood=True)
        else:
            if packet.dst in self.hosts_to_route:
                if self.hosts_to_route[packet.dst][1] != port:
                    if self.hosts_to_route[packet.dst][0] <= INFINITY:
                        self.send(packet, self.hosts_to_route[packet.dst][1], flood=False)

    def handle_timer(self):
        """
        Called periodically.
        When called, your router should send tables to neighbors.  It also might
        not be a bad place to check for whether any entries have expired.
        """
        if self.POISON_MODE:
            for p in self.poison_state.keys():
                self.send(basics.RoutePacket(p, INFINITY), flood=True)
        for host in self.hosts_to_route.keys():
            route_still_valid = api.current_time() - self.hosts_to_route[host][2] <= self.ROUTE_TIMEOUT
            host_route = self.hosts_to_route[host][2] == -1
            if route_still_valid or host_route:
                if self.POISON_MODE:
                    self.send(basics.RoutePacket(host, INFINITY), self.hosts_to_route[host][1])
                self.send(basics.RoutePacket(host, self.hosts_to_route[host][0]),
                          self.hosts_to_route[host][1], flood=True)
            else:
                if self.POISON_MODE:
                    self.send(basics.RoutePacket(host, INFINITY), self.hosts_to_route[host][1])
                    self.poison_state[host] = self.hosts_to_route[host]
                del self.hosts_to_route[host]

