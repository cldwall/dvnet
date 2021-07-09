import logging
from .cmds import _execute, _get_value

log = logging.getLogger(__name__)

prev_bridge_nf_call = None
prev_ipv4_forward = None

def alter_ipv4_forwarding(disable = False):
    global prev_ipv4_forward
    log.debug(f"Setting net.ipv4.ip_forward to {0 if disable else 1}")
    if not prev_ipv4_forward:
        prev_ipv4_forward = int(
            _get_value(
                ['sysctl', '-n', 'net.ipv4.ip_forward'],
                "Error retrieving ipv4.ip_forward's value"
            )
        )

    _execute(
        [
            'sysctl', '-w',
            f'net.ipv4.ip_forward={0 if disable else 1}'
        ],
        "Error writing to net.ipv4.ip_forward"
    )

def restore_ipv4_forwarding():
    log.debug(f"Restoring net.ipv4.ip_forward to {prev_ipv4_forward}")
    _execute(
        [
            'sysctl', '-w',
            f'net.ipv4.ip_forward={prev_ipv4_forward}'
        ],
        "Error restoring ipv4.ip_forward's value"
    )

def alter_brd_iptables_calls(disable = True):
    global prev_bridge_nf_call
    log.debug(f"Setting net.bridge.bridge-nf-call-iptables to {0 if disable else 1}")
    if not prev_bridge_nf_call:
        prev_bridge_nf_call = int(
            _get_value(
                ['sysctl', '-n', 'net.bridge.bridge-nf-call-iptables'],
                "Error retrieving bridge-nf-call-iptables' value. The br_netfilter module might not be loaded!"
            )
        )

    _execute(
        [
            'sysctl', '-w',
            f'net.bridge.bridge-nf-call-iptables={0 if disable else 1}'
        ],
        "Error writing to net.bridge.bridge-nf-call-iptables. The br_netfilter module might not be loaded!"
    )

def restore_brd_iptables_calls():
    log.debug(f"Restoring net.bridge.bridge-nf-call-iptables to {prev_bridge_nf_call}")
    _execute(
        [
            'sysctl', '-w',
            f'net.bridge.bridge-nf-call-iptables={prev_bridge_nf_call}'
        ],
        "Error restoring net.bridge.bridge-nf-call-iptables's value. The br_netfilter module might not be loaded!"
    )

def create_netns_dir():
    log.debug("Creating the /var/run/netns directory")
    _execute(
        ['mkdir', '-p', '/var/run/netns'],
        "Error creating the /var/run/netns directory"
    )
