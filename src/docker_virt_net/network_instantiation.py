import sys, logging, json, tarfile, io

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
        log.info("Creating subnets...")
        _instantiate_subnets(conf)
        log.info("Creating routers...")
        _instantiate_routers(conf, net_graph)
        if conf['private_routing']:
            log.info("Routing the private network...")
            _private_routing(conf, net_graph)
        if conf['internet_access']:
            log.info("Routing the network towrds the Internet...")
            _public_routing(conf, net_graph)
        if conf['update_hosts']:
            log.info("Adding entries to /etc/hosts at each node...")
            _update_hosts_files()
        log.info(f"Network '{conf['name']}' is ready to go!")
    except (InstError, DckError, IP2Error) as err:
        log.critical(f"Error instantiating the net: {err.cause}")
        log.debug("Cleaning what we had...")
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
            log.debug(f"Instantiating subnet {subnet}")
            _create_bridge(subnet + "_brd")

            for host in config['hosts']:
                log.debug(f"Instantiating host {host}")
                _create_node(host, dx.types.host, conf['host_image'])
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
            log.debug(f"Instantiating router {router}")
            _create_node(router, dx.types.router, conf['router_image'])
            for subnet in config['subnets']:
                router_iface, _ = _connect_node(router, subnet + "_brd")
                ipaddr.assign(
                    router_iface,
                    request_ip(conf['subnets'][subnet]['address'], hname = router),
                    netns = router
                )
            dx.apply_fw_rules(router, config['fw_rules'])

        if conf['internet_access']:
            try:
                d_brd, d_gw, d_subnet = dx.get_default_net_data()
            except DckError as err:
                log.warning(f"Couldn't configure outward internet access: {err.cause}")

            log.info("Enabling internet access for each network node...")

            first_router = list(conf['routers'].keys())[0]
            iplink.bridge.activate(d_brd)
            r_iface, _ = _connect_node(first_router, d_brd)
            addr_manager.request_ip(d_subnet)
            r_ip = addr_manager.request_ip(d_subnet, first_router)
            ipaddr.assign(r_iface, r_ip, first_router)
            iproute.assign('default', d_gw, first_router)
            for range in addr_manager.private_ranges:
                dx.add_nat_rule(first_router, "ACCEPT", range)
            dx.add_nat_rule(first_router, "MASQUERADE")

    except (IP2Error, DckError) as err:
        raise InstError(err.cause)

def _create_bridge(name):
    iplink.bridge.create(name)
    iplink.bridge.activate(name)
    existing_instances['bridges'].append(name)

def _create_node(name, type, img):
    dx.run_container(
        name, type, img
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

def _public_routing(net_conf, net_graph):
    routes = {
        'default': networkx.shortest_path(
            net_graph, target = list(net_conf['routers'].keys())[0],
            method = "dijkstra"
        )
    }

    log.debug(f"Discovered PUBLIC routes --\n{json.dumps(routes, indent = 2)}\n--")

    _apply_routes(routes, net_conf)

def _private_routing(net_conf, net_graph):
    routes = {}
    for subnet, config in net_conf['subnets'].items():
        routes[config['address']] = networkx.shortest_path(
            net_graph, target = subnet + "_brd",
            method = "dijkstra"
        )

    log.debug(f"Discovered PRIVATE routes --\n{json.dumps(routes, indent = 2)}\n--")

    _apply_routes(routes, net_conf)

def _apply_routes(routes, net_conf):
    for subnet, paths_to_it in routes.items():
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
                    break

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
    hosts_file = '\n'.join(
        [f"{addrs[0].split('/')[0]} {host}" for host, addrs in addr_manager.assigned_addreses.items()]
    ) + '\n'
    log.debug(f"Extra hosts:\n{hosts_file}")

    # TAR file generation:
        # data_buff -> Binary buffer containing the extra hosts to be added to /etc/hosts.
        # tar_buff  -> Binary buffer where the generated TAR file will be written.
        # tinfo     -> TarInfo instance containing the name and size of the TAR file.
    data_buff, tar_buff = io.BytesIO(hosts_file.encode()), io.BytesIO()
    t_file = tarfile.open(mode = 'w', fileobj = tar_buff)
    tinfo = tarfile.TarInfo()
    tinfo.name = "extra_hosts"
    tinfo.size = data_buff.seek(0, io.SEEK_END)
    data_buff.seek(0, io.SEEK_SET)
    t_file.addfile(tinfo, data_buff)
    t_file.close()
    tar_buff.seek(0, io.SEEK_SET)
    tar_data = tar_buff.read()

    # Once the TAR file has been generated, upload it to containers
        # and append it to /etc/hosts
    for node in existing_instances['containers']:
        log.debug(f"Updating /etc/hosts @ node {node}")

        # We CANNOT overwrite /etc/hosts as it is bind-mounted
            # by the docker engine from the host's disk...
        dx.upload_file(node, "/etc", tar_data)
        dx.append_file_to_file(node, f"/etc/{tinfo.name}", "/etc/hosts")

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
        log.info(f"Deleted the '{net_conf['name']}' network correctly!")
    except (IP2Error, DckError) as err:
        log.critical(f"Error undoing the deployment: {err.cause}.")
        log.critical("Try to manually remove containers and bridges left behind...")
        sys.exit(-1)
