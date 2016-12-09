"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter(basics.DVRouterBase):
<<<<<<< HEAD
    NO_LOG = True  # Set to True on an instance to disable its logging
    POISON_MODE = False  # Can override POISON_MODE here
    DEFAULT_TIMER_INTERVAL = 5  # Can override this yourself for testing
=======
    # NO_LOG = True # Set to True on an instance to disable its logging
    # POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing
>>>>>>> develop

    def __init__(self):
        """
        Called when the instance is initialized.
<<<<<<< HEAD
        You probably want to do some additional initialization here.
        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
        self.port_to_latency = {}
        self.hosts_to_route = {}
        self.poison_state = {}
=======

        You probably want to do some additional initialization here.

        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
>>>>>>> develop

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.
<<<<<<< HEAD
        The port attached to the link and the link latency are passed in.
        """
        self.port_to_latency[port] = latency
        for host in self.hosts_to_route.keys():
            self.send(basics.RoutePacket(host, self.hosts_to_route[host][0]), port)
=======

        The port attached to the link and the link latency are passed
        in.

        """
        pass
>>>>>>> develop

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.
<<<<<<< HEAD
        The port number used by the link is passed in.
        """
        if not self.POISON_MODE:
            for host in self.hosts_to_route.keys():
                if self.hosts_to_route[host] is not None:
                    if self.hosts_to_route[host][1] == port:
                        self.hosts_to_route[host] = None
        else:
            for host in self.hosts_to_route.keys():
                if self.hosts_to_route[host] is not None:
                    if self.hosts_to_route[host][1] == port:
                        self.poison_state[host] = self.hosts_to_route[host]
                        self.send(basics.RoutePacket(host, INFINITY), flood=True)
                        self.hosts_to_route[host] = None
        del self.port_to_latency[port]
=======

        The port number used by the link is passed in.

        """
        pass
>>>>>>> develop

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.
<<<<<<< HEAD
        packet is a Packet (or subclass).
        port is the port number it arrived on.
        You definitely want to fill this in.
        """
        if isinstance(packet, basics.RoutePacket):
            if packet.latency + self.port_to_latency[port] < INFINITY:
                if self.POISON_MODE:
                    if packet.destination in self.poison_state:
                        del self.poison_state[packet.destination]
                    self.send(basics.RoutePacket(packet.destination, INFINITY), port)
                if packet.destination not in self.hosts_to_route.keys() \
                        or self.hosts_to_route[packet.destination] is None \
                        or self.hosts_to_route[packet.destination][0] > packet.latency + self.port_to_latency[port]:
                    self.hosts_to_route[packet.destination] = \
                        [self.port_to_latency[port] + packet.latency, port, api.current_time()]
                    self.send(basics.RoutePacket(packet.destination, self.port_to_latency[port] + packet.latency), port,
                              flood=True)
                else:
                    if packet.latency + self.port_to_latency[port] == self.hosts_to_route[packet.destination][0]:
                        if self.hosts_to_route[packet.destination][2] < api.current_time():
                            self.hosts_to_route[packet.destination] = \
                                [packet.latency + self.port_to_latency[port], port, api.current_time()]
                            self.send(basics.RoutePacket(
                                packet.destination, self.port_to_latency[port] + packet.latency), port, flood=True)
                    if self.hosts_to_route[packet.destination][1] == port:
                        if packet.latency + self.port_to_latency[port] > self.hosts_to_route[packet.destination][0]:
                            self.hosts_to_route[packet.destination][0] = packet.latency + self.port_to_latency[port]
                            self.send(basics.RoutePacket(
                                packet.destination, self.port_to_latency[port] + packet.latency), port, flood=True)
                        self.hosts_to_route[packet.destination][2] = api.current_time()
            elif packet.latency >= INFINITY and self.POISON_MODE:
                for host in self.hosts_to_route.keys():
                    if host == packet.destination:
                        if self.hosts_to_route[host] is not None:
                            if self.hosts_to_route[host][1] == port:
                                poison = basics.RoutePacket(packet.destination, INFINITY)
                                self.send(poison, port, flood=True)
                                self.poison_state[host] = self.hosts_to_route[host]
                                self.hosts_to_route[host] = None
        elif isinstance(packet, basics.HostDiscoveryPacket):
            self.hosts_to_route[packet.src] = [self.port_to_latency[port], port, -1]
            route = basics.RoutePacket(packet.src, self.port_to_latency[port])
            self.send(route, port, flood=True)
        else:
            if packet.dst in self.hosts_to_route.keys():
                if self.hosts_to_route[packet.dst] is not None:
                    if self.hosts_to_route[packet.dst][1] != port:
                        if self.hosts_to_route[packet.dst][0] <= INFINITY:
                            self.send(packet, self.hosts_to_route[packet.dst][1], flood=False)
=======

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            pass
        elif isinstance(packet, basics.HostDiscoveryPacket):
            pass
        else:
            # Totally wrong behavior for the sake of demonstration only: send
            # the packet back to where it came from!
            self.send(packet, port=port)
>>>>>>> develop

    def handle_timer(self):
        """
        Called periodically.
<<<<<<< HEAD
        When called, your router should send tables to neighbors.  It also might
        not be a bad place to check for whether any entries have expired.
        """
        if self.POISON_MODE:
            for p in self.poison_state.keys():
                self.send(basics.RoutePacket(p, INFINITY), flood=True)
                self.poison_state[p] = self.hosts_to_route[p]

        for host in self.hosts_to_route.keys():
            if self.hosts_to_route[host] is not None:
                # if self.POISON_MODE:
                #     self.send(basics.RoutePacket(host, INFINITY), self.hosts_to_route[host][1])
                route_still_valid = api.current_time() - self.hosts_to_route[host][2] <= self.ROUTE_TIMEOUT
                host_route = self.hosts_to_route[host][2] == -1
                if route_still_valid or host_route:
                    self.send(basics.RoutePacket(host, self.hosts_to_route[host][0]),
                              self.hosts_to_route[host][1], flood=True)
                else:
                    self.hosts_to_route[host] = None
=======

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        pass
>>>>>>> develop
