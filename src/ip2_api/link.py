from .call_factory import _call_factory

class veth:
    @staticmethod
    def create(x, y):
        _call_factory(
            [
                'ip', 'link', 'add', x,
                'type', 'veth', 'peer',
                'name', y
            ],
            f"Error creating veth {x}--{y}"
        )

    @staticmethod
    def activate(veth):
        _call_factory(
            ['ip', 'link', 'set', veth, 'up'],
            f"Error activating veth {veth}"
        )

    @staticmethod
    def connect(node, veth, host = True):
        _call_factory(
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

        _call_factory(
            args,
            f"Error removing veth {veth} on netns {netns if netns else 'root'}"
        )

class bridge:
    @staticmethod
    def create(name):
        _call_factory(
            [
                'ip', 'link', 'add', 'name',
                name, 'type', 'bridge'
            ],
            f"Error creating bridge {name}"
        )

    @staticmethod
    def activate(name):
        _call_factory(
            ['ip', 'link', 'set', name, 'up'],
            f"Error activating bridge {name}"
        )

    @staticmethod
    def remove(name):
        _call_factory(
            ['ip', 'link', 'del', name],
            f"Error deleting bridge {name}"
        )
