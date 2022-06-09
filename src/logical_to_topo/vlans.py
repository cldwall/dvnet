import logging, json, math, pathlib

import networkx as nx

from docker_virt_net import addr_manager
from docker_virt_net import network_instantiation as ni
from docker_virt_net import docker_cnx as dx
from docker_virt_net import net_visualization
from networkx.drawing.nx_agraph import write_dot

from typing import Union

import ip2_api.link as iplink
import ip2_api.addr as ipaddr
import ip2_api.vlan as ipvlan

log = logging.getLogger(__name__)

def instantiate_net(logicalGraph, storeCliques):
    ni._system_setup()

    topology = nx.Graph(name = "Topology")
    topology.add_node("brdC", type = "bridge", subnet = "")
    ni._create_bridge("brdC")

    trunkVLAN = ipvlan.vlan(0)

    topology.add_node("brdE0", type = "bridge", subnet = "")
    topology.add_edge("brdC", "brdE0")
    ni._create_bridge("brdE0")
    iplink.bridge.enableVLAN("brdE0")
    _, edgeIface = ni._connect_node("brdC", "brdE0", brdToBrd = True)
    trunkVLAN.addIface(edgeIface)

    nextFreeIP, currVLANID, instantiatedHosts, currEdgeBridge = "10.0.0.0", 2, 0, "brdE0"

    for clique in nx.find_cliques(logicalGraph):

        log.info(f"Taking clique {clique} into account")

        cliqueSubnetIPsExp = math.ceil(math.log(len(clique) + 2, 2))

        binNextFreeIP = addr_manager.addr_to_binary(nextFreeIP)
        if binNextFreeIP % (2 ** cliqueSubnetIPsExp) != 0:
            binNextFreeIP += (2 ** cliqueSubnetIPsExp) - (binNextFreeIP % (2 ** cliqueSubnetIPsExp))
            nextFreeIP = addr_manager.binary_to_addr(binNextFreeIP)

        cliqueSubnet = f"{nextFreeIP}/{32 - cliqueSubnetIPsExp}"

        nextFreeIP = addr_manager.binary_to_addr(addr_manager.addr_to_binary(nextFreeIP) + 2 ** cliqueSubnetIPsExp)

        cliqueVLAN = ipvlan.vlan(currVLANID)
        currVLANID += 1

        log.debug(f"Assigning addresses from subnet --> {cliqueSubnet}")

        for host in clique:
            addHost(topology, currEdgeBridge, host, cliqueSubnet, cliqueVLAN)
            instantiatedHosts += 1

            # Linux bridges can tolerate a maximum of 1024 ports: we can use 1023 for hosts and
                # we need a remaining one for a trunk port. We can use the following to effectively
                # check that's the imposed limit: `echo $((( $(bridge -c vlan show | wc -l) - 1) / 2))`
            if instantiatedHosts % 1023 == 0:
                currEdgeBridge = f"brdE{int(instantiatedHosts / 1023)}"
                topology.add_node(currEdgeBridge, type = "bridge", subnet = "")
                topology.add_edge("brdC", currEdgeBridge)
                ni._create_bridge(currEdgeBridge)
                iplink.bridge.enableVLAN(currEdgeBridge)
                _, edgeIface = ni._connect_node("brdC", currEdgeBridge, brdToBrd = True)
                trunkVLAN.addIface(edgeIface)

        log.debug(f"Assigned addresses -> {addr_manager.assigned_addreses}")

def remove_net(logicalGraph):
    tmp = {"bridges": ["brdC", *[f"brdE{i}" for i in range(len(logicalGraph) / 1023)]], "containers": []}
    for node in logicalGraph:
        tmp["containers"].append(node)

    log.info(f"Deleting the following instances:\n{json.dumps(tmp)}")
    ni._undo_deployment(tmp, fail = False)

def dump_graph_figure(logicalGraph, name: str):
    topology = nx.MultiGraph(name = f"{name.capitalize().replace('_', ' ')} Topology")

    topology.add_node("brdC", type = "bridge", subnet = "")

    for clique in nx.find_cliques(logicalGraph):
        log.warn(f"Taking clique {clique} into account")

        for host in clique:
            if host not in topology:
                topology.add_node(host, type = "host")
            topology.add_edge(host, "brdC")

    nx.write_gexf(topology, f"{name}_topology.gexf")
    write_dot(topology, f"{name}_topology.dot")

    net_visualization.show_net(topology, f"{name}_topology")

def addHost(graph, brdName, hostName, subnet, vlan):
    if hostName not in graph:
        graph.add_node(hostName, type = "host")
        ni._create_node(hostName, dx.types.host, "pcollado/d_host")
    graph.add_edge(hostName, brdName)
    hIface = addNetworkInfrastructure(brdName, hostName, vlan)
    addNetworkAddresses(subnet, hostName, hIface)

def addNetworkInfrastructure(brdName, host, vlan: ipvlan.vlan):
    hIface, brdIface = ni._connect_node(host, brdName, vID = vlan.vID)
    vlan.addIface(brdIface)
    return hIface

def addNetworkAddresses(subnet, hostName, hIface):
    ipaddr.assign(hIface, addr_manager.request_ip(subnet, hname = hostName), netns = hostName)
