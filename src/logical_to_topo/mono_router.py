from ctypes import util
import logging, json, subprocess, io, tarfile

import networkx as nx

from docker_virt_net import addr_manager
from docker_virt_net import network_instantiation as ni
from docker_virt_net import docker_cnx as dx
from docker_virt_net import ip_utils
from docker_virt_net import net_visualization
from docker_virt_net.exceptions import DckError

import ip2_api.addr as ipaddr
from ip2_api.exceptions import IP2Error
import ip2_api.route as iproute

from . import utils

log = logging.getLogger(__name__)

def instantiate_net(logicalGraph: nx.Graph, _, nImage, rImage, experiment = False, skipInstantiation = False):
    ni._system_setup()
    currentSubnet = "10.0.0.0/30"
    topology = nx.Graph(name = "Topology")

    topology.add_node("rCore", type = "router", internet_gw = False)
    ni._create_node("rCore", dx.types.router, rImage)

    # Pad all node names to at least 3-digit numbers
    logicalGraph = nx.relabel_nodes(logicalGraph, {f"{i}": "0" * (3 - len(f"{i}")) + f"{i}" for i in range(100)})

    for i, hostName in enumerate(logicalGraph):
        brdName = f"brd{hostName}"
        addGraphNode(topology, brdName, hostName)
        if not skipInstantiation:
            hIface, rIfaceSubnet = addNetworkInfrastructure(brdName, hostName, nImage, i * 4, skipInstantiation)
            if hIface != None and rIfaceSubnet != None:
                routerSubnetIP = addNetworkAddresses(
                    [(currentSubnet, hostName, hIface), (currentSubnet, "rCore", rIfaceSubnet)], skipInstantiation
                )
                addHostNetworkRoutes(hostName, routerSubnetIP, skipInstantiation)
        else:
            # Force address allocation
            addr_manager.request_ip(currentSubnet, hname = hostName)
            addr_manager.request_ip(currentSubnet, hname = "rCore")

        currentSubnet = "{}/30".format(
            addr_manager.binary_to_addr(ip_utils.addr_to_binary(currentSubnet.split("/")[0]) + 4)
        )

    configureFirewalls(logicalGraph)

    for node in logicalGraph:
        if isinstance(logicalGraph, nx.DiGraph):
            addNeighbourMap(node, [e[1] for e in logicalGraph.out_edges(node)])
        else:
            addNeighbourMap(node, logicalGraph.neighbors(node))

    if experiment:
        log.debug("Setting up additional experiment infrastructure")
        dx.link_netns("influxdb")
        ni._create_bridge("brdIDB")
        hIface, _ = ni._connect_node("influxdb", "brdIDB")
        rIface, _ = ni._connect_node("rCore", "brdIDB")
        ipaddr.assign(hIface, "192.168.0.2/30", netns = "influxdb")
        ipaddr.assign(rIface, "192.168.0.1/30", netns = "rCore")
        iproute.assign("default", "192.168.0.1", netns = "influxdb")
        dx._allow_traffic_to_ip("rCore", "192.168.0.2")
        dx._allow_traffic_from_ip("rCore", "192.168.0.2")

def remove_net(logicalGraph):
    logicalGraph = nx.relabel_nodes(logicalGraph, {f"{i}": "0" * (3 - len(f"{i}")) + f"{i}" for i in range(100)})
    tmp = {"bridges": ["brdIDB", "brdIDB-influxdb"], "containers": ["rCore"]}
    subprocess.run(['rm', '-f', '/var/run/netns/influxdb'])
    for node in logicalGraph:
        tmp["bridges"].append(f"brd{node}")
        tmp["containers"].append(node)

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

def addGraphNode(graph, bridge, host):
    graph.add_node(bridge, type = "bridge", subnet = "")
    graph.add_node(host, type = "host")
    graph.add_edge(bridge, host)
    graph.add_edge(bridge, "rCore")

def addNetworkInfrastructure(bridge, host, nImage, index):
    try:
        ni._create_bridge(bridge)
        ni._create_node(host, dx.types.host, nImage)
        hIface, _ = ni._connect_node(host, bridge,
            nIfaceName   = utils.intToString(index, alphabet = "z0123456789abcdefghijklmnopqrstuvwxy", padding = 4),
            brdIfaceName = utils.intToString(index + 1, alphabet = "z0123456789abcdefghijklmnopqrstuvwxy", padding = 4)
        )
        rIfaceSubnet, _ = ni._connect_node("rCore", bridge,
            nIfaceName   = utils.intToString(index + 2, alphabet = "z0123456789abcdefghijklmnopqrstuvwxy", padding = 4),
            brdIfaceName = utils.intToString(index + 3, alphabet = "z0123456789abcdefghijklmnopqrstuvwxy", padding = 4)
        )
    except DckError as err:
        log.warn(f"Error creating host {host}: {err.cause}")
        return None, None
    except IP2Error as err:
        log.warn(f"Error creating network infrastructure: {err.cause}")
        return None, None
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
    dx.apply_fw_rules("rCore", {"POLICY": "DROP", "DROP": [], "ACCEPT": [
            (node, neigh, True) for node in logicalGraph for neigh in logicalGraph.neighbors(node)
        ]})

def addNeighbourMap(node, neighbours):
    log.debug(f"Adding neighbour map to {node}")
    data_buff, tar_buff = io.BytesIO(json.dumps(
        {"ourIP": addr_manager.name_2_ip(node), "neighIPs": [addr_manager.name_2_ip(neigh) for neigh in neighbours]}
    ).encode()), io.BytesIO()

    t_file = tarfile.open(mode = 'w', fileobj = tar_buff)
    tinfo = tarfile.TarInfo()
    tinfo.name = "neighIPs.json"
    tinfo.size = data_buff.seek(0, io.SEEK_END)
    data_buff.seek(0, io.SEEK_SET)
    t_file.addfile(tinfo, data_buff)
    t_file.close()
    tar_buff.seek(0, io.SEEK_SET)
    tar_data = tar_buff.read()

    dx.upload_file(node, "/root", tar_data)
