import json, jsonschema, pathlib, logging, sys, networkx

log = logging.getLogger(__name__)

def _addr_to_binary(addr):
    """Returns an integer equivalent for an IPv4 address.

        Args:
            addr (str): An IPv4 address in A.B.C.D format.

        Returns:
            int: The equivalent representation of `addr`.
    """
    bin_ip, loop_count = 0, 0
    for x in reversed(addr.split('/')[0].split('.')):
        bin_ip |= int(x) << loop_count * 8
        loop_count += 1
    return bin_ip

def _get_net_addr(subn):
    """Returns the network address for an IPv4 CIDR block.

        Args:
            subn (str): An IPv4 CIDR block in A.B.C.D/X format.

        Returns:
            int: The CIDR's block network address.
    """
    mask = 0
    for i in range(int(subn.split('/')[1])):
        mask |= 0x1 << (31 - i)
    return _addr_to_binary(subn) & mask

def _get_brd_addr(subn):
    """Returns the broadcast address for an IPv4 CIDR block.

        Args:
            subn (str): An IPv4 CIDR block in A.B.C.D/X format.

        Returns:
            int: The CIDR's block broadcast address.
    """
    mask = 0
    for i in range(int(subn.split('/')[1])):
        mask |= 0x1 << (31 - i)
    return _get_net_addr(subn) | ~mask

private_ranges = {subn: (_get_net_addr(subn), _get_brd_addr(subn)) for subn in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]}

class ConfError(Exception):
    """Exception representing an error in the network configuration's contents."""
    def __init__(self, cause):
        self.cause = cause

    def __str__(self):
        return self.cause

def parse_config(conf, schema = "net.schema"):
    """Loads the desired network configuration and performs initial validation.

        Args:
            conf (str): The user-specified path to the desired network configuration file.
            schema (str, optional): The JSON schema to validate the configuration against.

        Returns:
            networkx.Graph: A graph representing the desired virtual network.
    """
    try:
        net_conf = load_conf(conf, schema)
        log.info(f"Correctly loaded {conf}")
        validate_subnet_addresses(net_conf)
        log.debug(f"IPv4 addresses specified on {conf} seem good to go")
        net = build_graph(net_conf)
        log.info(f"Built a graph representing the network defined in {conf}")
        return net
    except ConfError as err:
        log.critical(err.cause)
        sys.exit(-1)

def load_conf(conf_path, schema = "net.schema"):
    """Loads the desired network configuration and performs initial validation.

        Args:
            conf (str): The user-specified path to the desired network configuration file.
            schema (str, optional): The JSON schema to validate the configuration against.

        Returns:
            dictionary: The contents of the file specified by `conf`.
    """
    try:
        net_conf = json.loads(pathlib.Path(conf_path).read_text())
        jsonschema.validate(
            net_conf,
            schema = json.loads((pathlib.Path(__file__).parent / schema).read_text())
        )
    except FileNotFoundError as err:
        raise ConfError(f"Couldn't find file {err.filename}")
    except json.JSONDecodeError as err:
        raise ConfError(f"Could not decode {conf_path}: {err.msg} @ line {err.lineno}")
    except jsonschema.ValidationError as err:
        raise ConfError(f"Network configuration {conf_path} is NOT VALID: {err.message}")

    return net_conf

def validate_subnet_addresses(conf):
    """Validates the CIDR addresses for every subnet.

    Args:
        conf (dictionary): The network configuration whose addresses are to
            be validated.
    """
    previous_subnets = []
    for subnet in conf['subnets'].values():
        try:
            subnet_addr = subnet['address']
            ip, mask = subnet_addr.split('/')
            if len(ip.split('.')) != 4:
                raise ValueError
            for oct in ip.split('.'):
                ioct = int(oct)
                if not 0 <= ioct <= 255:
                    raise ValueError
            if not 1 <= int(mask) <= 32:
                raise ValueError
            check_private_ip(subnet_addr)
            if subnet_addr in previous_subnets:
                raise ConfError(f"CIDR block {subnet_addr} has been assigned more than once")
            previous_subnets.append(subnet_addr)
        except ValueError:
            raise ConfError(f"IPv4 subnet range in CIDR notation {subnet_addr} is not valid.")

def check_private_ip(subnet):
    """Checks whether a subnet block is contained within a private address range as per RFC 1918.

        Args:
            subnet (string): The CIDR block to check.

        Returns:
            bool: True if the subnet block belongs to a private range. False otherwise.
    """
    brd = _get_brd_addr(subnet)
    net = _get_net_addr(subnet)

    for range, limits in private_ranges.items():
        if net >= limits[0] and brd <= limits[1]:
            log.debug(f"CIDR block {subnet} belongs to private IPv4 range {range}")
            return True

    log.debug(f"CIDR block {subnet} does not belong to a private block. This could interfere with outbound connectivity...")
    return False

def build_graph(conf):
    """Builds a NetworkX graph representing the network specified in the configuration file.

        Args:
            conf (dictionary): The network configuration loaded from a user-specified file.

        Returns:
            networkx.Graph: A graph representing the entire network.
    """
    net = networkx.Graph()
    for subnet, content in conf['subnets'].items():
        if net.has_node(subnet + "_brd"):
            raise ConfError(f"Subnet {subnet} has been defined more than once")
        net.add_node(subnet + "_brd", type = "bridge", subnet = content['address'])
        for host in content['hosts']:
            if net.has_node(host):
                raise ConfError(f"Host {host} has been added more than once")
            net.add_node(host, type = "node")
            net.add_edge(host, subnet + "_brd")

    for router, router_conf in conf['routers'].items():
        if net.has_node(router):
            raise ConfError(f"Router {router} has been added more than once")
        net.add_node(router, type = "router", fw_rules = router_conf['fw_rules'])
        for subnet in router_conf['subnets']:
            if not net.has_node(subnet + "_brd"):
                raise ConfError(f"Subnet {subnet} has not been defined and router {router} connects to it")
            net.add_edge(router, subnet + "_brd")

    return net