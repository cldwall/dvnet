import docker, subprocess, logging

# Supress urrlib3's log output below the WARNING level
logging.getLogger("urllib3").setLevel(logging.WARNING)

from .addr_manager import name_2_ip
from .exceptions import DckError

log = logging.getLogger(__name__)

class types:
    host = 0
    router = 1

image_map = [
    "d_host",
    "d_router"
]

caps_map = [
    ["SYS_ADMIN"],
    ["SYS_ADMIN", "NET_ADMIN"]
]

sysctls_map = [
    {},
    {'net.ipv4.ip_forward': 1}
]

d_client = docker.from_env()

def run_container(name, type, img = None, caps = None, sysctls = None):
    if not img:
        img = image_map[type]

    if not caps:
        caps = caps_map[type]

    if not sysctls:
        sysctls = sysctls_map[type]

    log.debug(f"Running container {name}: img = {img}; caps = {caps}; sysctls = {sysctls}")

    try:
        d_client.containers.run(
            img,
            name = name,
            hostname = name,
            network_mode = "none",
            cap_add = caps,
            sysctls = sysctls,
            detach = True
        )
    except docker.errors.ImageNotFound:
        raise DckError(f"Image for L3 device {name} not found")
    except docker.errors.APIError as err:
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
                'iptables', '-I', chain,
                '-j', target, '-p', 'all',
                '-s', source,
                '-d', dest
            ]
        )
    except DckError:
        raise DckError(f"Error on rule {source}/{dest}/{target}; chain {chain}")

def append_to_file(name, content, file):
    try:
        log.debug(f"Running 'bash -c 'echo {content} >> {file}'' on {name}")
        d_client.containers.get(name).exec_run(
            f"bash -c 'echo {content} >> {file}'"
        )
    except DckError:
        raise DckError(f"Error appending {content} to {file} on {name}")

def _exec(cont, args):
    rc, _ = cont.exec_run(args)
    if rc != 0:
        raise DckError("Foo")
