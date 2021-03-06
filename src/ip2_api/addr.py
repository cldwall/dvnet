import logging

from .cmds import _execute

log = logging.getLogger(__name__)

def assign(iface, cidr_block, netns = None):
    log.debug(f"Assigning address {cidr_block} to interface {iface} on netns {netns if netns else 'root'}")
    if netns:
        args = [
            'ip', '-n', netns, 'addr', 'replace',
            cidr_block, 'brd', '+', 'dev', iface
        ]
    else:
        args = [
            'ip', 'addr', 'replace', cidr_block,
            'brd', '+', 'dev', iface
        ]

    _execute(
        args,
        f"Error assigning {cidr_block} to {iface} on netns {netns if netns else 'root'}"
    )

def reset(iface, netns = None):
    log.debug(f"Resetting interface {iface} on netns {netns if netns else 'root'}")
    if netns:
        args = ['ip', '-n', netns, 'addr', 'flush', 'dev', iface, 'scope', 'global']
    else:
        args = ['ip', 'addr', 'flush', 'dev', iface, 'scope', 'global']

    _execute(
        args,
        f"Error flushing interface {iface} on netns {netns if netns else 'root'}"
    )
