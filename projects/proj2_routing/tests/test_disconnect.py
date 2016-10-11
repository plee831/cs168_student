"""

@658 on Piazza
https://piazza.com/class/iq6sgotn6pp37f?cid=658


"""

import sim
import sim.api as api
import sim.basics as basics
import sys

from tests.test_simple import GetPacketHost, NoPacketHost


class SwitchableCountingHub(api.Entity):
    pings = 0
    enabled = True

    def handle_rx(self, packet, in_port):
        if self.enabled:
            self.send(packet, in_port, flood=True)
            # if not isinstance(packet, basics.Ping):
            # api.userlog.debug('%s saw a packet: %s' % (self.name, packet))
        if isinstance(packet, basics.Ping):
            api.userlog.debug('%s saw a ping' % (self.name,))
            self.pings += 1


def launch():
    h1 = NoPacketHost.create('h1')
    h2 = GetPacketHost.create('h2')

    s1 = sim.config.default_switch_type.create('s1')
    s2 = sim.config.default_switch_type.create('s2')

    c1 = SwitchableCountingHub.create('c1')

    s1.linkTo(h1, latency=1)
    s1.linkTo(h2, latency=5)
    s1.linkTo(c1, latency=1)
    s2.linkTo(c1, latency=1)
    s2.linkTo(h2, latency=1)

    def test_tasklet():
        yield 15  # wait for path convergence

        api.userlog.debug('Sending ping from h1 to h2')
        h1.ping(h2)

        yield 10  # wait for ping to go through

        if c1.pings != 1:
            api.userlog.error("Ping should have gone through c1")
            sys.exit(1)

        # unlink s2
        s2.unlinkTo(c1)
        s2.unlinkTo(h2)
        s1.unlinkTo(c1)

        api.userlog.debug("bye bye s2")

        yield 25  # wait for new route convergence
        api.userlog.debug('Sending ping from h1 to h2')
        h1.ping(h2)

        yield 10  # wait for ping to reach h2 again

        if c1.pings != 1:
            api.userlog.error("c1 shouldn't have seen another ping")
            sys.exit(1)

        if h2.pings != 2:
            api.userlog.error("h2 should have seen the ping by now")
            sys.exit(1)

        sys.exit(0)

    api.run_tasklet(test_tasklet)