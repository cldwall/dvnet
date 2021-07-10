import sys, logging, json

import networkx

from .addr_manager import request_ip, name_2_ip, get_net_addr

import ip2_api.link as iplink
import ip2_api.addr as ipaddr
import ip2_api.route as iproute
import ip2_api.utils as iputils
from ip2_api.exceptions import IP2Error, UtilError

from . import docker_cnx as dx

from .exceptions import DckError, InstError
from docker_virt_net import addr_manager

log = logging.getLogger(__name__)

existing_instances = {
    'bridges': [],
    'containers': []
}

def instantiate_network(conf, net_graph):
    try:
        log.info("Setting up the system")
        _system_setup()
        log.info("Begining subnet creation")
        _instantiate_subnets(conf)
        log.info("Begining router creation")
        _instantiate_routers(conf, net_graph)
        log.info("Beginning network routing")
        _route_net(conf, net_graph)
        log.info("Adding entries to /etc/hosts at each node")
        _update_hosts_files()
    except InstError as err:
        log.critical(f"Error instantiating the net: {err.cause}")
        log.info("Cleaning what we had...")
        try:
            _undo_deployment(existing_instances)
        except (IP2Error, DckError) as err:
            log.critical(f"Error undoing the deployment: {err.cause}.")
            log.critical("Try to manually remove containers and bridges left behind...")
        sys.exit(-1)

def _system_setup():
    try:
        iputils.alter_ipv4_forwarding()
        iputils.alter_brd_iptables_calls()
        iputils.create_netns_dir()
    except UtilError as err:
        raise InstError(err.cause)

def _instantiate_subnets(conf):
    try:
        for subnet, config in conf['subnets'].items():
            log.info(f"Instantiating subnet {subnet}")
            _create_bridge(subnet + "_brd")

            for host in config['hosts']:
                log.info(f"Instantiating host {host}")
                _create_node(host, dx.types.host)
                host_iface, _ = _connect_node(host, subnet + "_brd")
                ipaddr.assign(
                    host_iface,
                    request_ip(config['address'], hname = host),
                    netns = host
                )
    except (IP2Error, DckError) as err:
        raise InstError(err.cause)

def _instantiate_routers(conf, net_graph):
    try:
        for router, config in conf['routers'].items():
            log.info(f"Instantiating router {router}")
            _create_node(router, dx.types.router)
            for subnet in config['subnets']:
                router_iface, _ = _connect_node(router, subnet + "_brd")
                ipaddr.assign(
                    router_iface,
                    request_ip(conf['subnets'][subnet]['address'], hname = router),
                    netns = router
                )
            dx.apply_fw_rules(router, config['fw_rules'])

        if conf.get("internet_access", False):
            log.info("Enabling internet access for the network")
            first_router = list(conf['routers'].keys())[0]
            iplink.bridge.activate('docker0')
            r_iface, _ = _connect_node(first_router, 'docker0')
            ipaddr.assign(r_iface, "172.17.0.2/16", first_router)
            iproute.assign('default', '172.17.0.1', first_router)
            for range in addr_manager.private_ranges:
                dx.add_nat_rule(first_router, "ACCEPT", range)
            dx.add_nat_rule(first_router, "MASQUERADE")

    except (IP2Error, DckError) as err:
        raise InstError(err.cause)

def _create_bridge(name):
    iplink.bridge.create(name)
    iplink.bridge.activate(name)
    existing_instances['bridges'].append(name)

def _create_node(name, type, img = None, caps = None):
    dx.run_container(
        name, type
    )
    dx.link_netns(name)
    existing_instances['containers'].append(name)

def _connect_node(node, bridge):
    x, y = f"{node}-{bridge}", f"{bridge}-{node}"
    iplink.veth.create(x, y)
    iplink.veth.connect(node, x, host = True)
    iplink.veth.activate(x, netns = node)
    iplink.veth.connect(bridge, y, host = False)
    iplink.veth.activate(y)
    return x, y

def _route_net(net_conf, net_graph):
    paths_to_subnets = {}
    for subnet, config in net_conf['subnets'].items():
        paths_to_subnets[config['address']] = networkx.shortest_path(
            net_graph, target = subnet + "_brd",
            method = "dijkstra"
        )

    if net_conf.get("internet_access", False):
        paths_to_subnets['default'] = networkx.shortest_path(
            net_graph, target = list(net_conf['routers'].keys())[0],
            method = "dijkstra"
        )

    log.debug(f"Discovered routes --\n{json.dumps(paths_to_subnets, indent = 2)}\n--")

    for subnet, paths_to_it in paths_to_subnets.items():
        for source, path_to_subnet in paths_to_it.items():
            # No need to route bridges
            if source in existing_instances['bridges']:
                continue
            # We belong to the same subnet
            if len(path_to_subnet) == 2:
                continue
            # Source and destination are included in the path
            for hop in path_to_subnet[1:]:
                if hop in net_conf['routers'].keys():
                    gw_ip = _find_reachable_ip(source, hop)
                    try:
                        iproute.assign(subnet, gw_ip, netns = source)
                    except IP2Error as err:
                        raise InstError(err.cause)

def _find_reachable_ip(source, gw):
    gw_addresses = name_2_ip(gw, index = -1)
    gw_subnets = [get_net_addr(addr) for addr in gw_addresses]
    for subnet in [get_net_addr(addr) for addr in name_2_ip(source, index = -1)]:
        if subnet in gw_subnets:
            return gw_addresses[gw_subnets.index(subnet)].split('/')[0]

def _undo_deployment(instances):
    for bridge in instances['bridges']:
        iplink.bridge.remove(bridge)

    for container in instances['containers']:
        dx.remove_container(container)

def _update_hosts_files():
    for node in existing_instances['containers']:
        log.debug(f"Updating /etc/hosts @ {node}")
        for container in existing_instances['containers']:
            if container != node:
                dx.append_to_file(
                    node,
                    f"{name_2_ip(container)} {container}",
                    "/etc/hosts"
                )

def delete_net(net_conf):
    log.info(f"Deleting the '{net_conf['name']}' network")
    tmp = {'bridges': [], 'containers': []}
    for subnet, config in net_conf['subnets'].items():
        tmp['bridges'].append(subnet + "_brd")
        for host in config['hosts']:
            tmp['containers'].append(host)
    for router in net_conf['routers'].keys():
        tmp['containers'].append(router)

    try:
        _undo_deployment(tmp)
    except (IP2Error, DckError) as err:
        log.critical(f"Error undoing the deployment: {err.cause}.")
        log.critical("Try to manually remove containers and bridges left behind...")
        sys.exit(-1)
