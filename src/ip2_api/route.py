import logging

from .cmds import _execute

log = logging.getLogger(__name__)

def assign(dest, gw, netns = None):
    log.debug(f"Assigning route to {dest} via {gw} on netns {netns if netns else 'root'}")
    if netns:
        args = ['ip', '-n', netns, 'route', 'replace', dest, 'via', gw]
    else:
        args = ['ip', 'route', 'replace', dest, 'via', gw]

    _execute(
        args,
        f"Error adding route to {dest} via {gw} on host {netns if netns else 'root'}"
    )

def remove(dest, gw, netns = None):
    log.debug(f"Removing route to {dest} via {gw} on netns {netns if netns else 'root'}")
    if netns:
        args = ['ip', '-n', netns, 'route', 'del', dest, 'via', gw]
    else:
        args = ['ip', 'route', 'del', dest, 'via', gw]

    _execute(
        args,
        f"Error deleting route to {dest} via {gw} on host {netns if netns else 'root'}"
    )
