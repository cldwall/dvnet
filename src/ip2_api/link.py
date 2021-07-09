from .cmds import _execute

class veth:
    @staticmethod
    def create(x, y):
        _execute(
            [
                'ip', 'link', 'add', x,
                'type', 'veth', 'peer',
                'name', y
            ],
            f"Error creating veth {x}--{y}"
        )

    @staticmethod
    def activate(veth):
        _execute(
            ['ip', 'link', 'set', veth, 'up'],
            f"Error activating veth {veth}"
        )

    @staticmethod
    def connect(node, veth, host = True):
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
        _execute(
            [
                'ip', 'link', 'add', 'name',
                name, 'type', 'bridge'
            ],
            f"Error creating bridge {name}"
        )

    @staticmethod
    def activate(name):
        _execute(
            ['ip', 'link', 'set', name, 'up'],
            f"Error activating bridge {name}"
        )

    @staticmethod
    def remove(name):
        _execute(
            ['ip', 'link', 'del', name],
            f"Error deleting bridge {name}"
        )