import sys, logging

from .addr_manager import request_ip

import ip2_api.link as iplink
import ip2_api.addr as ipaddr
import ip2_api.utils as iputils
from ip2_api.exceptions import IP2Error, UtilError

from . import docker_cnx as dx

from .exceptions import DckError, InstError

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
    dx.set_hostname(name)
    existing_instances['containers'].append(name)

def _connect_node(node, bridge):
    x, y = f"{node}-{bridge}", f"{bridge}-{node}"
    iplink.veth.create(x, y)
    iplink.veth.connect(node, x, host = True)
    iplink.veth.activate(x, netns = node)
    iplink.veth.connect(bridge, y, host = False)
    iplink.veth.activate(y)
    return x, y

def _undo_deployment(instances):
    for bridge in instances['bridges']:
        iplink.bridge.remove(bridge)

    for container in instances['containers']:
        dx.remove_container(container)

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
