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
    topology, nNodes = nx.Graph(name = "Topology"), len(logicalGraph)
    topology.add_node("brdCore", type = "bridge", subnet = "")
    ni._create_bridge("brdCore")

    for i in range(nNodes):
        addHost(topology, i, currentSubnet)

        currentSubnet = "{}/30".format(
            addr_manager.binary_to_addr(ip_utils.addr_to_binary(currentSubnet.split("/")[0]) + 4)
        )
    routeNetwork(nNodes)
    configureFirewalls(logicalGraph)

def remove_net(logicalGraph):
    tmp = {"bridges": ["brdCore"], "containers": []}
    for i in range(len(logicalGraph)):
        tmp["bridges"].append(f"brd{i}")
        tmp["containers"].append(f"h{i}")
        tmp["containers"].append(f"r{i}")

    log.info(f"Deleting the following instances:\n{json.dumps(tmp)}")
    ni._undo_deployment(tmp, fail = False)

def dump_graph_figure(logicalGraph, name: str):
    topology, n = nx.Graph(name = f"{name.capitalize().replace('_', ' ')} Topology"), len(logicalGraph)

    topology.add_node("brdCore", type = "bridge", subnet = "")

    for i in range(n):
        addGraphNode(f"brd{i}", f"h{i}", f"r{i}")

    relabeledLogicalGraph = nx.relabel_nodes(logicalGraph,
        {node: f"h{i}" for i, node in enumerate(logicalGraph.nodes())})
    relabeledLogicalGraph.graph['name'] = name.capitalize().replace('_', ' ')

    nx.write_gexf(topology, f"{name}_topology.gexf")
    net_visualization.show_net(topology, f"{name}_topology")

    nx.write_gexf(relabeledLogicalGraph, f"{name}_relabeled.gexf")
    net_visualization.show_net(relabeledLogicalGraph, f"{name}_relabeled")

def addHost(graph, id, subnet):
    brdName, hostName, routerName = f"brd{id}", f"h{id}", f"r{id}"
    addGraphNode(graph, brdName, hostName, routerName)
    hIface, rIfaceSubnet, rIfaceCore = addNetworkInfrastructure(brdName, hostName, routerName)
    routerSubnetIP = addNetworkAddresses(
        [(subnet, hostName, hIface), (subnet, routerName, rIfaceSubnet), ("172.16.0.0/12", routerName, rIfaceCore)]
    )
    addHostNetworkRoutes(hostName, routerSubnetIP)

def addGraphNode(graph, bridge, host, router):
    graph.add_node(bridge, type = "bridge", subnet = "")
    graph.add_node(host, type = "host")
    graph.add_edge(bridge, host)
    graph.add_node(router, type = "router", internet_gw = False)
    graph.add_edge(bridge, router)
    graph.add_edge("brdCore", router)

def addNetworkInfrastructure(bridge, host, router):
    ni._create_bridge(bridge)
    ni._create_node(host, dx.types.host, "pcollado/d_host")
    hIface, _ = ni._connect_node(host, bridge)
    ni._create_node(router, dx.types.router, "pcollado/d_router")
    rIfaceSubnet, _ = ni._connect_node(router, bridge)
    rIfaceCore, _ = ni._connect_node(router, "brdCore")

    return hIface, rIfaceSubnet, rIfaceCore

def addNetworkAddresses(addressingInfo):
    for subnet, nodeName, iface in addressingInfo:
        reqIP = addr_manager.request_ip(subnet, hname = nodeName)
        if nodeName.startswith('r') and not subnet.startswith("172"):
            routerSubnetIP = reqIP
        ipaddr.assign(iface, reqIP, netns = nodeName)
    return routerSubnetIP

def addHostNetworkRoutes(host, routerSubnetIP):
    iproute.assign("default", routerSubnetIP.split("/")[0], netns = host)

def routeNetwork(nNodes):
    rNames = [f"r{i}" for i in range(nNodes)]
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

def configureFirewalls(logicalGraph):
    relabeledLogicalGraph = nx.relabel_nodes(logicalGraph,
        {node: f"h{i}" for i, node in enumerate(logicalGraph.nodes())})

    for i, node in enumerate(relabeledLogicalGraph):
        dx.apply_fw_rules(f"r{i}", {"POLICY": "DROP", "DROP": [], "ACCEPT": [
            (node, neigh, True) for neigh in relabeledLogicalGraph.neighbors(node)
        ]})
