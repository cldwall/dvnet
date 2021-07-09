import docker, subprocess

from .exceptions import DckError

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

d_client = docker.from_env()

def run_container(name, type, img = None, caps = None):
    if not img:
        img = image_map[type]

    if not caps:
        caps = caps_map[type]

    try:
        d_client.containers.run(
            img,
            name = name,
            network_mode = "none",
            cap_add = caps,
            detach = True
        )
    except docker.errors.ImageNotFound:
        raise DckError(f"Image for L3 device {name} not found")
    except docker.errors.APIError:
        raise DckError("Docker engine error...")

def link_netns(name):
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

def set_hostname(name):
    try:
        _exec(d_client.get(name), ['hostname', name])
    except DckError:
        raise DckError(f"Error setting up hostname for {name}")

def apply_fw_rules(name, fw_rules, chain = "FORWARD"):
    if len(fw_rules) <= 0:
        return

    try:
        r_cont = d_client.get(name)

        try:
            _exec(
                r_cont,
                ['iptables', '-P', chain, fw_rules['POLICY'].uppper()]
            )
        except DckError:
            raise DckError(f"Error setting policy {fw_rules['POLICY']}")

        for target in ["ACCEPT", "DROP"]:
            for rule in fw_rules[target]:
                _add_fw_rule(r_cont, chain, target, rule[0], rule[1])
                if rule[2]:
                    _add_fw_rule(r_cont, chain, target, rule[1], rule[0])
    except DckError as err:
        raise DckError(f"FW conf error @ {name}: {err.cause}")
    except docker.errors.APIError:
        raise DckError(f"FW conf error @ {name}: Couldn't get container")

def _add_fw_rule(cont, chain, target, source, dest):
    try:
        _exec(
            cont,
            [
                'ipatbles', '-I', chain,
                '-j', target, '-p', 'all',
                '-s', source, '-d', dest
            ]
        )
    except DckError:
        raise DckError(f"Error on rule {source}/{dest}/{target}; chain {chain}")

def _exec(cont, args):
    rc, _ = cont.exec_run(args)
    if rc != 0:
        raise DckError
