import logging, json

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

    topology.add_node("rCore", type = "router", internet_gw = False)
    ni._create_node("rCore", dx.types.router, "pcollado/d_router")

    for i in range(nNodes):
        addHost(topology, i, currentSubnet)

        currentSubnet = "{}/30".format(
            addr_manager.binary_to_addr(ip_utils.addr_to_binary(currentSubnet.split("/")[0]) + 4)
        )

    configureFirewalls(logicalGraph)

def remove_net(logicalGraph):
    tmp = {"bridges": [], "containers": ["rCore"]}
    for i in range(len(logicalGraph)):
        tmp["bridges"].append(f"brd{i}")
        tmp["containers"].append(f"h{i}")
        tmp["containers"].append(f"r{i}")

    log.info(f"Deleting the following instances:\n{json.dumps(tmp)}")
    ni._undo_deployment(tmp, fail = False)

def dump_graph_figure(logicalGraph, name: str):
    topology, n = nx.Graph(name = f"{name.capitalize().replace('_', ' ')} Topology"), len(logicalGraph)

    topology.add_node("rCore", type = "router", internet_gw = False)

    for i in range(n):
        addGraphNode(topology, f"brd{i}", f"h{i}")

    relabeledLogicalGraph = nx.relabel_nodes(logicalGraph,
        {node: f"h{i}" for i, node in enumerate(logicalGraph.nodes())})
    relabeledLogicalGraph.graph['name'] = name.capitalize().replace('_', ' ')

    nx.write_gexf(topology, f"{name}_topology.gexf")
    net_visualization.show_net(topology, f"{name}_topology")

    nx.write_gexf(relabeledLogicalGraph, f"{name}_relabeled.gexf")
    net_visualization.show_net(relabeledLogicalGraph, f"{name}_relabeled")

def addHost(graph, id, subnet):
    brdName, hostName = f"brd{id}", f"h{id}"
    addGraphNode(graph, brdName, hostName)
    hIface, rIfaceSubnet = addNetworkInfrastructure(brdName, hostName)
    routerSubnetIP = addNetworkAddresses(
        [(subnet, hostName, hIface), (subnet, "rCore", rIfaceSubnet)]
    )
    addHostNetworkRoutes(hostName, routerSubnetIP)

def addGraphNode(graph, bridge, host):
    graph.add_node(bridge, type = "bridge", subnet = "")
    graph.add_node(host, type = "host")
    graph.add_edge(bridge, host)
    graph.add_edge(bridge, "rCore")

def addNetworkInfrastructure(bridge, host):
    ni._create_bridge(bridge)
    ni._create_node(host, dx.types.host, "pcollado/d_host")
    hIface, _ = ni._connect_node(host, bridge)
    rIfaceSubnet, _ = ni._connect_node("rCore", bridge)

    return hIface, rIfaceSubnet

def addNetworkAddresses(addressingInfo):
    for subnet, nodeName, iface in addressingInfo:
        reqIP = addr_manager.request_ip(subnet, hname = nodeName)
        if nodeName.startswith('r'):
            routerSubnetIP = reqIP
        ipaddr.assign(iface, reqIP, netns = nodeName)
    return routerSubnetIP

def addHostNetworkRoutes(host, routerSubnetIP):
    iproute.assign("default", routerSubnetIP.split("/")[0], netns = host)

def configureFirewalls(logicalGraph):
    relabeledLogicalGraph = nx.relabel_nodes(logicalGraph,
        {node: f"h{i}" for i, node in enumerate(logicalGraph.nodes())})

    dx.apply_fw_rules("rCore", {"POLICY": "DROP", "DROP": [], "ACCEPT": [
            (node, neigh, True) for node in relabeledLogicalGraph for neigh in relabeledLogicalGraph.neighbors(node)
        ]})
