import logging, json, sys

import networkx as nx

from docker_virt_net import addr_manager
from docker_virt_net import network_instantiation as ni
from docker_virt_net import docker_cnx as dx
from docker_virt_net import ip_utils
from docker_virt_net import net_visualization

import ip2_api.addr as ipaddr
import ip2_api.route as iproute

log = logging.getLogger(__name__)

def instantiate_net(logicalGraph):
    ni._system_setup()

    currentSubnet = "10.0.0.0/30"

    topology, n = nx.Graph(name = "Topology"), len(logicalGraph)

    log.info(f"Adding bridge brdCore to the topology graph")
    topology.add_node("brdCore", type = "bridge", subnet = "")
    ni._create_bridge("brdCore")

    for i, node in enumerate(list(logicalGraph.nodes())):
        brdName, hostName, routerName = f"brd{i}", f"h{i}", f"r{i}"

        log.info(f"Adding bridge {brdName} to the topology graph")
        topology.add_node(brdName, type = "bridge", subnet = "")

        ni._create_bridge(brdName)

        log.info(f"Adding host {hostName} to the topology graph")
        topology.add_node(hostName, type = "host")

        log.info(f"Instantiating host {hostName}")
        ni._create_node(hostName, dx.types.host, "pcollado/d_host")

        log.info(f"Adding the {brdName} <--> {hostName} edge")
        topology.add_edge(brdName, hostName)

        nIface, _ = ni._connect_node(hostName, brdName)

        hIP = addr_manager.request_ip(currentSubnet, hname = hostName)
        ipaddr.assign(nIface, hIP, netns = hostName)

        log.info(f"Adding router {routerName} to the topology graph")
        topology.add_node(routerName, type = "router",
            fw_rules = {"POLICY": "DROP", "ACCEPT": [], "DROP": []}, internet_gw = False)

        ni._create_node(routerName, dx.types.router, "pcollado/d_router")
        log.info(f"Adding the {brdName} <--> {routerName} edge")
        topology.add_edge(brdName, routerName)
        rIfaceSubnet, _ = ni._connect_node(routerName, brdName)
        log.info(f"Adding the brdCore <--> {routerName} edge")
        topology.add_edge("brdCore", routerName)
        rIfaceCore, _ = ni._connect_node(routerName, "brdCore")

        rIPSubnet = addr_manager.request_ip(currentSubnet, hname = routerName)
        rIPCore = addr_manager.request_ip("172.16.0.0/12", hname = routerName)
        ipaddr.assign(rIfaceSubnet, rIPSubnet, netns = routerName)
        ipaddr.assign(rIfaceCore, rIPCore, netns = routerName)

        iproute.assign("default", rIPSubnet.split("/")[0], netns = hostName)

        currentSubnet = "{}/30".format(
            addr_manager.binary_to_addr(ip_utils.addr_to_binary(currentSubnet.split("/")[0]) + 4)
        )

    rNames = [f"r{i}" for i in range(n)]
    for tRouter in rNames:
        rawSubnet = addr_manager.name_2_ip(tRouter, -1)
        tSubnet = "{}/{}".format(
            addr_manager.binary_to_addr(addr_manager.get_net_addr(rawSubnet[0])),
            rawSubnet[0].split('/')[1]
        )
        tIP = rawSubnet[-1].split('/')[0]
        for sRouter in rNames:
            if sRouter == tRouter:
                continue
            iproute.assign(tSubnet, tIP, netns = sRouter)

def remove_net(logicalGraph):
    tmp = {"bridges": ["brdCore"], "containers": []}
    for i in range(len(logicalGraph)):
        tmp["bridges"].append(f"brd{i}")
        tmp["containers"].append(f"h{i}")
        tmp["containers"].append(f"r{i}")

    log.info(f"Deleting the following instances:\n{json.dumps(tmp)}")
    ni._undo_deployment(tmp)
    sys.exit(0)
