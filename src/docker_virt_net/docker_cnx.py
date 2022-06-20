import docker, subprocess, logging, time

# Supress urrlib3's log output below the WARNING level
logging.getLogger("urllib3").setLevel(logging.WARNING)

from .addr_manager import name_2_ip
from .exceptions import DckError

log = logging.getLogger(__name__)

class types:
    host = 0
    router = 1

caps_map = [
    ["SYS_ADMIN", "NET_ADMIN"],
    ["SYS_ADMIN", "NET_ADMIN"]
]

sysctls_map = [
    {
        'net.ipv6.conf.all.disable_ipv6': 0
    },
    {
        'net.ipv6.conf.all.disable_ipv6': 0,
        'net.ipv4.ip_forward': 1
    }
]

dns_resolvers = [
    "1.1.1.1", "8.8.8.8"
]

d_client = docker.from_env()

def get_default_net_data():
    for net in d_client.networks.list():
        if net.name == "bridge":
            try:
                brd = net.attrs['Options']['com.docker.network.bridge.name']
                gw = net.attrs['IPAM']['Config'][0]['Gateway']
                subn = net.attrs['IPAM']['Config'][0]['Subnet']
            except (KeyError, docker.errors.APIError):
                raise DckError("Couldn't retrieve default docker network configuration")
            return brd, gw, subn

# TODO: Use the extra_hosts (https://docker-py.readthedocs.io/en/stable/containers.html) parameter
    # to update /etc/hosts within new containers!

def run_container(name, type, img):
    log.debug(f"Running container {name}: img = {img}; caps = {caps_map[type]}; sysctls = {sysctls_map[type]}")

    try:
        d_client.containers.run(
            img,
            name = name,
            hostname = name,
            dns = dns_resolvers,
            network_mode = "none",
            cap_add = caps_map[type],
            sysctls = sysctls_map[type],
            detach = True
        )
    except docker.errors.ImageNotFound:
        raise DckError(f"Image '{img}' for L3 device {name} couldn't be found")
    except docker.errors.APIError as err:
        # We might've hit a timeout!
        time.Sleep(5)
        d_client.containers.get(name).start()
        raise DckError(f"Docker engine error - {err.explanation}")

def remove_container(name):
    log.debug(f"Removing container {name} and unlinking its netns")
    try:
        c_inst = d_client.containers.get(name)
        c_inst.stop()
        c_inst.remove()
        subprocess.run(['rm', '-f', f'/var/run/netns/{name}'])
    except docker.errors.APIError as err:
        raise DckError(f"Docker engine error - {err.explanation}")

def link_netns(name):
    log.debug(f"Linking {name}'s network namespace")
    try:
        subprocess.run(
                [
                    'ln', '-sf',
                    f"/proc/{d_client.api.inspect_container(name)['State']['Pid']}/ns/net",
                    f'/var/run/netns/{name}'
                ],
                check = True,
                stdout = subprocess.DEVNULL,
                stderr = subprocess.DEVNULL
            )
    except subprocess.CalledProcessError:
        raise DckError(f"Error linking the netns of container {name}")

def apply_fw_rules(name, fw_rules, chain = "FORWARD"):
    if len(fw_rules) <= 0:
        return

    try:
        r_cont = d_client.containers.get(name)

        log.debug(f"Setting {name}'s default FW policy to {fw_rules['POLICY'].upper()}")

        try:
            _exec(
                r_cont,
                ['iptables', '-P', chain, fw_rules['POLICY'].upper()]
            )
        except DckError:
            raise DckError(f"Error setting policy {fw_rules['POLICY']}")

        for target in ["ACCEPT", "DROP"]:
            for rule in fw_rules[target]:
                log.debug(f"Adding FW rule {rule} to {name}")
                _add_fw_rule(r_cont, chain, target, rule[0], rule[1])
                if rule[2]:
                    _add_fw_rule(r_cont, chain, target, rule[1], rule[0])
    except DckError as err:
        raise DckError(f"FW conf error @ {name}: {err.cause}")
    except docker.errors.APIError:
        raise DckError(f"FW conf error @ {name}: Couldn't get container")

def _add_fw_rule(cont, chain, target, source, dest):
    source, dest = name_2_ip(source), name_2_ip(dest)

    if source == -1:
        raise DckError(f"Couldn't retrieve {source}'s IP")

    if dest == -1:
        raise DckError(f"Couldn't retrieve {dest}'s IP")

    try:
        _exec(
            cont,
            [
                'iptables', '-A', chain, '-j', target,
                '-s', source, '-d', dest
            ]
        )
    except DckError as err:
        raise DckError(f"{err.cause} @ rule {source}-{dest}-{target}; {chain} chain; filter table")

def _allow_traffic_to_ip(cont, dest):
    try:
        _exec(d_client.containers.get(cont), ['iptables', '-A', "FORWARD", '-j', "ACCEPT", '-d', dest])
    except DckError as err:
        raise DckError(f"{err.cause} @ rule anywhere-{dest}-ACCEPT; FORWARD chain; filter table")

def _allow_traffic_from_ip(cont, src):
    try:
        _exec(d_client.containers.get(cont), ['iptables', '-A', "FORWARD", '-j', "ACCEPT", '-s', src])
    except DckError as err:
        raise DckError(f"{err.cause} @ rule {src}-anywhere-ACCEPT; FORWARD chain; filter table")

def add_nat_rule(cont, target, dest = None):
    cont = d_client.containers.get(cont)
    args = [
        'iptables', '-t', 'nat', '-A', 'POSTROUTING',
        '-j', target, '-d', dest
    ]

    if dest == None:
        args = args[:-2]

    try:
        _exec(cont, args)
    except DckError as err:
        raise DckError(f"{err.cause} @ rule any-{dest if dest else 'any'}-{target}; POSTROUTING chain; nat table")

def append_file_to_file(name, src, dst):
    try:
        d_client.containers.get(name).exec_run(
            f"bash -c 'cat {src} >> {dst}'"
        )
    except docker.errors.APIError as err:
        raise DckError(err.explanation)

def upload_file(name, path, data):
    try:
        d_client.containers.get(name).put_archive(path, data)
    except docker.errors.APIError as err:
        raise DckError(err.explanation)

def _exec(cont, args):
    try:
        rc, _ = cont.exec_run(args)
        if rc != 0:
            raise DckError("Non-zero return code")
    except docker.errors.APIError as err:
        raise DckError(err.explanation)
