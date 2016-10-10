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
        self.routing_table = {} # destination: latency, port, current time
        self.dst_to_destination = {} # dst to destination
        self.ports = {} # port to latency
        self.ports_to_dst = {} # ports to dst
        self.hosts = {} # port to source

        # Another thought : destination: latency, next_hop, for the routing table, do we need port?

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.
        The port attached to the link and the link latency are passed
        in.
        """
        # could be host or router that comes up
        # TODO add in logic of sending update of routing table
        for port in self.hosts.keys():
            print ("#######")
            self.send(basics.RoutePacket(destination=destination, latency=self.routing_table[destination][0]), port=port)
        # for p in self.ports:
            # self.send(basics.RoutePacket(destination=destination, latency=latency), port=p)
        self.ports[port] = latency

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.
        The port number used by the link is passed in.
        """
        if port in self.ports:
           del self.ports[port]
        if port in self.hosts:
            del self.hosts[port]
        
        for key in self.routing_table:
            if self.routing_table[key][1] == port:
                del self.routing_table[key]
        # TODO add in logic of sending update of routing table
        # This is a big one
        # TODO letting routers know that the link went down (whether host or router)

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.
        packet is a Packet (or subclass).
        port is the port number it arrived on.
        You definitely want to fill this in.
        """
        self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):  # .dst = none
            
            # Add all the ports to a destination list
            destinations = []
            for dst in self.routing_table.keys():
                destinations.append(self.routing_table[dst][1])

            self.routing_table[packet.destination] = (packet.latency, port, api.current_time())

            if packet.destination not in self.routing_table:
                self.routing_table[packet.destination] = (packet.latency, port, api.current_time())
            else:
                old_latency = self.routing_table[packet.destination][0]
                # We are missing another latency value here
                # routing[packet]
                new_latency = self.routing_table[packet.src][0] + packet.latency
                if old_latency > new_latency:
                    self.routing_table[packet.destination] = (new_latency, port, api.current_time())
                    self.send(basics.RoutePacket(packet.destination, self.routing_table[packet.destination][0]), destinations, flood=False)
            self.send(basics.RoutePacket(packet.destination, self.routing_table[packet.destination][0]), destinations, flood=False)
            self.dst_to_destination[packet.dst] = packet.destination
            self.ports_to_dst[port] = packet.dst

        elif isinstance(packet, basics.HostDiscoveryPacket):
            # https://piazza.com/class/iq6sgotn6pp37f?cid=463
            print "Host Discovery Packet $$$$"
            
            self.hosts[port] = packet.src
            
            print packet.src
            print self.hosts
            if packet.src not in self.hosts.values():
                print "IN HEEHEHEH"
                print "Packet.src: " + str(packet.src)
                print "Packet.dst: " + str(packet.dst)
                self.hosts[packet.src] = {port, packet.dst}
                self.send(basics.RoutePacket(destination=packet.src, latency=0),
                          port=port, flood=True)
            else:
                print("AAAAA")
        else:
            # packet.src & packet.dst
            print ("-----")
            print ("Regular Packet")
            found_host = False
            # print packet.src, 'Hwyeywey'
            # print packet.dst, "Hwllo"
            for port in self.hosts.keys():
                if packet.src != packet.dst:
                #if port in self.ports_to_dst.keys():
                    if self.hosts[port] == packet.dst:
                        found_host = True
                        self.send(packet, port=port)
            print "ALEX"
            for key in self.routing_table:
                print key
            print "NOOBUEN"
            if not found_host:
                if packet.dst in self.routing_table.keys():
                    self.send(packet, self.routing_table[packet.dst][1])
            #if not found_host:
                # if port in self.ports_to_dst.keys():
                #     # never goes into this
                #     dst = self.ports_to_dst[port]
                #     self.send(packet, port=self.routing_table[dst][1])

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
