import logging, json, sys

import networkx as nx

from docker_virt_net import addr_manager
from docker_virt_net import network_instantiation as ni
from docker_virt_net import docker_cnx as dx
from docker_virt_net import ip_utils

import ip2_api.addr as ipaddr
import ip2_api.route as iproute

log = logging.getLogger(__name__)

def instantiate_net(logicalGraph):
    ni._system_setup()

    currentSubnet = "10.0.0.0/30"

    log.info(f"Instantiating the core bridge")
    ni._create_bridge("brdCore")

    topology, n = nx.Graph(name = "Topology"), len(logicalGraph)

    for i, node in enumerate(list(logicalGraph.nodes())):
        brdName, hostName, routerName = f"brd{i}", f"h{i}", f"r{i}"

        log.info(f"Adding bridge {brdName} to the topology graph")
        topology.add_node(brdName, type = "bridge", subnet = "")

        log.info(f"Instantiating bridge {brdName}")
        ni._create_bridge(brdName)

        log.info(f"Adding host {hostName} to the topology graph")
        topology.add_node(hostName, type = "host")

        log.info(f"Instantiating host {hostName}")
        ni._create_node(hostName, dx.types.host, "pcollado/d_host")

        log.info(f"Adding the {brdName} <--> {hostName} edge")
        topology.add_edge(brdName, hostName)

        log.info(f"Adding the {brdName} <--> {hostName} veth")
        nIface, _ = ni._connect_node(hostName, brdName)

        hIP = addr_manager.request_ip(currentSubnet, hname = hostName)
        log.info(f"Assigning IPv4 {hIP} to host {hostName}")
        ipaddr.assign(nIface, hIP, netns = hostName)

        log.info(f"Adding router {routerName} to the topology graph")
        topology.add_node(routerName, type = "router", fw_rules = {}, internet_gw = False)

        ni._create_node(routerName, dx.types.router, "pcollado/d_router")
        log.info(f"Adding the {brdName} <--> {routerName} veth")
        rIfaceSubnet, _ = ni._connect_node(routerName, brdName)
        log.info(f"Adding the {hostName} <--> {routerName} veth")
        rIfaceCore, _ = ni._connect_node(routerName, "brdCore")

        rIPSubnet = addr_manager.request_ip(currentSubnet, hname = routerName)
        rIPCore = addr_manager.request_ip("172.16.0.0/12", hname = hostName)
        log.info(f"Assigning subnet IPv4 {rIPSubnet} to router {routerName}")
        ipaddr.assign(rIfaceSubnet, rIPSubnet, netns = routerName)
        log.info(f"Assigning core IPv4 {rIPCore} to router {routerName}")
        ipaddr.assign(rIfaceCore, rIPCore, netns = routerName)

        iproute.assign("default", rIPSubnet.split("/")[0], netns = hostName)

        currentSubnet = "{}/30".format(
            addr_manager.binary_to_addr(ip_utils.addr_to_binary(currentSubnet.split("/")[0]) + 4)
        )

    # nx.add_cycle(topology, [f"r{i}" for i in range(n)], type = "router", fw_rules = {}, internet_gw = False)

    # net_visualization.show_net(topology, "NOSTORE", k = 0.01)

def remove_net(logicalGraph):
    tmp = {"bridges": ["brdCore"], "containers": []}
    for i in range(len(logicalGraph)):
        tmp["bridges"].append(f"brd{i}")
        tmp["containers"].append(f"h{i}")
        tmp["containers"].append(f"r{i}")

    log.info(f"Deleting the following instances:\n{json.dumps(tmp)}")
    ni._undo_deployment(tmp)
    sys.exit(0)
