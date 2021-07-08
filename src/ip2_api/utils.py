import subprocess
from .exceptions import UtilError

def alter_ipv4_forwarding(disable = False):
    try:
        subprocess.run(
            [
                'sysctl', '-w',
                f'net.ipv4.ip_forward={0 if disable else 1}'
            ],
            check = True
        )
    except subprocess.CalledProcessError:
        raise UtilError(f"Error writing to net.ipv4.ip_forward")

def alter_brd_iptables_calls(disable = True):
    try:
        subprocess.run(
            [
                'sysctl', '-w',
                f'net.bridge.bridge-nf-call-iptables={0 if disable else 1}'
            ],
            check = True
        )
    except subprocess.CalledProcessError:
        raise UtilError(f"Error writing to net.bridge.bridge-nf-call-iptables")

def create_netns_dir():
    try:
        subprocess.run(
            ['mkdir', '-p', '/var/run/netns'],
            check = True
        )
    except subprocess.CalledProcessError:
        raise UtilError(f"Error writing creating the /var/run/netns directory")
