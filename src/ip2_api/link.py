import logging
from .cmds import _execute

log = logging.getLogger(__name__)

class veth:
    @staticmethod
    def create(x, y):
        log.debug(f"Creating veth {x}--{y}")
        _execute(
            [
                'ip', 'link', 'add', x,
                'type', 'veth', 'peer',
                'name', y
            ],
            f"Error creating veth {x}--{y}. Check it doesn't exist already!"
        )

    @staticmethod
    def activate(veth, netns = None):
        log.debug(f"Activating {veth} on netns {netns if netns else 'root'}")
        if netns:
            args = ['ip', '-n', netns, 'link', 'set', veth, 'up']
        else:
            args = ['ip', 'link', 'set', veth, 'up']

        _execute(
            args,
            f"Error activating veth {veth}"
        )

    @staticmethod
    def connect(node, veth, host = True):
        log.debug(f"Connecting {veth} to {node}")
        _execute(
            [
                'ip', 'link', 'set', veth,
                'netns' if host else 'master',
                node
            ],
            f"Error connectig {veth} to {node}"
        )

    @staticmethod
    def remove(veth, netns = None):
        log.debug(f"Remvoving veth {veth} from netns {netns if netns else 'root'}")
        if netns:
            args = ['ip', '-n', netns, 'link', 'del', veth, 'type', 'veth']
        else:
            args = ['ip', 'link', 'del', veth, 'type', 'veth']

        _execute(
            args,
            f"Error removing veth {veth} on netns {netns if netns else 'root'}"
        )

class bridge:
    @staticmethod
    def create(name):
        log.debug(f"Activating bridge {name}")
        _execute(
            [
                'ip', 'link', 'add', 'name',
                name, 'type', 'bridge'
            ],
            f"Error creating bridge {name}. Check it doesn't exist already!"
        )

    @staticmethod
    def activate(name):
        log.debug(f"Activating bridge {name}")
        _execute(
            ['ip', 'link', 'set', name, 'up'],
            f"Error activating bridge {name}"
        )

    @staticmethod
    def remove(name):
        log.debug(f"Removing bridge {name}")
        _execute(
            ['ip', 'link', 'del', name],
            f"Error deleting bridge {name}"
        )
