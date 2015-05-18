"""
Topology tests

logger reference to topology logger.

"""

from nose.tools import *
from nose.plugins.skip import Skip, SkipTest

from mininet.topo import LinearTopo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI

from minicps import constants as c
from minicps.topology import EthStar, Minicps, DLR, L3EthStar

from time import sleep

import os

import logging
logger = logging.getLogger('minicps.topology')
setLogLevel(c.TEST_LOG_LEVEL)


def setup_func(test_name):
    logger.info('Inside %s' % test_name)

def teardown_func(test_name):
    logger.info('Leaving %s' % test_name)

def with_named_setup(setup=None, teardown=None):
    def wrap(f):
        return with_setup(
            lambda: setup(f.__name__) if (setup is not None) else None, 
            lambda: teardown(f.__name__) if (teardown is not None) else None)(f)
    return wrap


def mininet_functests(net):
    """Common mininet functional tests can be called inside
    each unittest. The function will be ignored by nose
    during automatic test collection because its name is
    not part of nose convention.
    Remember to manually stop the network after this call.

    :net: Mininet object
    """

    logging.info("Dumping host connections")
    dumpNodeConnections(net.hosts)
    logging.info("Testing network connectivity")
    net.pingAll()
    logging.info("Testing TCP bandwidth btw first and last host")
    net.iperf()
    

@with_named_setup(setup_func, teardown_func)
def test_EthStar():
    """Show mininet testing capabilites on an eth star topologies"""
    raise SkipTest

    topo = EthStar(n=6)
    net = Mininet(topo)  # TODO: subclass Mininet with Minicps and replace it
    net.start()

    plc1, plc2 = net.get('plc1', 'plc2')  # get host obj reference by name
    # net.iperf((plc1, plc2))  # passed as a tuple
    # output = plc1.cmd('ifconfig')
    # print output

    # while ... do ... done bash syntax
    cmd = """
    while true
    do date
    sleep 1
    done > %s/date.out &
    """ % (c.TEMP_DIR)

    plc1.cmd(cmd)
    sleep(4)  # sec
    plc1.cmd('kill %while')

    with open(c.TEMP_DIR+'/date.out', 'r') as f:
        for line in f.readlines():
            logger.debug(line.strip())  # remove leading and trailing whitespaces
    # file closed automatically by python context manager API

    net.stop()


@with_named_setup(setup_func, teardown_func)
def test_L3EthStarBuild():
    """Test L3EthStar build process with custom L3_LINKOPTS"""
    raise SkipTest

    topo = L3EthStar()
    net = Mininet(topo=topo, link=TCLink)
    net.start()

    CLI(net)
    # mininet_functests(net)

    net.stop()


@with_named_setup(setup_func, teardown_func)
def test_L3EthStarEnip():
    """Test L3EthStar ENIP client/server communications
    plc1 is used as a cpppo simulated controller listening
    to from all interfaces at port 44818
    workstn is used as a cpppo client sending couples of
    write/read requests every second.
    """
    raise SkipTest

    # TODO: integrate everything into log folder
    open(c.TEMP_DIR+'/l3/cppposerver.err', 'w').close()
    open(c.TEMP_DIR+'/l3/cpppoclient.out', 'w').close()
    open(c.TEMP_DIR+'/l3/cpppoclient.err', 'w').close()

    topo = L3EthStar()
    net = Mininet(topo=topo, link=TCLink)
    net.start()

    plc1, workstn = net.get('plc1', 'workstn')

    server_cmd = './scripts/l3/cpppo_plc1server.sh'
    plc1.cmd(server_cmd)

    client_cmd = './scripts/l3/cpppo_client4plc1.sh'
    out = workstn.cmd(client_cmd)
    logger.debug(out)

    net.stop()


@with_named_setup(setup_func, teardown_func)
def test_L3EthStarArpMitm():
    """plc1 ARP poisoning MITM attack using ettercap,
    You can pass IP target to the dedicated script.
    """
    # raise SkipTest

    # TODO: capute packets with ettercap and log it
    open(c.TEMP_DIR+'/l3/plc1arppoisoning.out', 'w').close()

    topo = L3EthStar()
    net = Mininet(topo=topo, link=TCLink)
    net.start()

    plc1, plc2, plc3 = net.get('plc1', 'plc2', 'plc3')

    target_ip1 = plc2.IP()
    target_ip2 = plc3.IP()
    attacker_interface = 'plc1-eth0'

    plc1_cmd = 'scripts/attacks/arp-mitm.sh %s %s %s' % ( target_ip1,
            target_ip2, attacker_interface)
    plc1.cmd(plc1_cmd)

    plc2_cmd = 'ping -c5 %s' % plc3.IP()
    plc2_out = plc2.cmd(plc2_cmd)
    logger.debug(plc2_out)

    plc1_out = plc1.cmd('tcpdump &')
    logger.debug(plc1_out)

    # CLI(net)

    net.stop()
