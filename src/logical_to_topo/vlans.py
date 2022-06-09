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
    topology.add_node("brdCore", type = "bridge", subnet = "")
    ni._create_bridge("brdCore")
    iplink.bridge.enableVLAN("brdCore")

    log.debug("Beginning clique discovery...")
    cliques = discoverCliques(logicalGraph, storeCliques)
    log.debug(f"Discovered cliques: {cliques}")

    nextFreeIP, currVLANID = "10.0.0.0", 2

    for cLen, cliqueL in cliques.items():
        if cLen == 0:
            continue
        for clique in cliqueL:
            if discardClique(clique, cLen, cliques):
                continue

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
                addHost(topology, host, cliqueSubnet, cliqueVLAN)

        log.debug(f"Assigned addresses -> {addr_manager.assigned_addreses}")

def discoverCliques(logicalGraph: nx.Graph, storeCliques: bool = False) -> dict[int, Union[int, list[set]]]:
    cliques = {}
    for clique in list(nx.enumerate_all_cliques(logicalGraph)):
        cLen = len(clique)
        if cLen <= 1:
            continue
        if cLen not in cliques:
            cliques[cLen] = [set(clique)]
        else:
            cliques[cLen].append(set(clique))
        cliques[0] = max(cliques.keys())
    if storeCliques:
        pathlib.Path("cliques.json").write_text(json.dumps(cliques))
    return cliques

def remove_net(logicalGraph):
    tmp = {"bridges": ["brdCore"], "containers": []}
    for node in logicalGraph:
        tmp["containers"].append(node)

    log.info(f"Deleting the following instances:\n{json.dumps(tmp)}")
    ni._undo_deployment(tmp, fail = False)

def dump_graph_figure(logicalGraph, name: str):
    topology = nx.MultiGraph(name = f"{name.capitalize().replace('_', ' ')} Topology")

    topology.add_node("brdCore", type = "bridge", subnet = "")

    cliques = discoverCliques(logicalGraph)

    for cLen, cliqueL in cliques.items():
        if cLen == 0:
            continue
        for clique in cliqueL:
            if discardClique(clique, cLen, cliques):
                continue

            log.warn(f"Taking clique {clique} into account")

            for host in clique:
                if host not in topology:
                    topology.add_node(host, type = "host")
                topology.add_edge(host, "brdCore")

    nx.write_gexf(topology, f"{name}_topology.gexf")
    write_dot(topology, f"{name}_topology.dot")

    net_visualization.show_net(topology, f"{name}_topology")

def discardClique(clique, cLen, cliques):
    for l in range(cLen + 1, cliques[0] + 1):
        for bClique in cliques[l]:
            if bClique >= clique:
                log.debug(f"Clique {clique} is a subset of {bClique}! Discarding it...")
                return True
    return False

def addHost(graph, hostName, subnet, vlan):
    if hostName not in graph:
        graph.add_node(hostName, type = "host")
        ni._create_node(hostName, dx.types.host, "pcollado/d_host")
    graph.add_edge(hostName, "brdCore")
    hIface = addNetworkInfrastructure(hostName, vlan)
    addNetworkAddresses(subnet, hostName, hIface)

def addNetworkInfrastructure(host, vlan: ipvlan.vlan):
    hIface, brdIface = ni._connect_node(host, "brdCore", vID = vlan.vID)
    vlan.addIface(brdIface)
    return hIface

def addNetworkAddresses(subnet, hostName, hIface):
    ipaddr.assign(hIface, addr_manager.request_ip(subnet, hname = hostName), netns = hostName)
