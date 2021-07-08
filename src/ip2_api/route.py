from .call_factory import _call_factory

def assign(dest, gw, netns = None):
    if netns:
        args = ['ip', '-n', netns, 'route', 'replace', dest, 'via', gw]
    else:
        args = ['ip', 'route', 'replace', dest, 'via', gw]

    _call_factory(
        args,
        f"Error adding route to {dest} via {gw} on host {netns if netns else 'root'}"
    )

def remove(dest, gw, netns = None):
    if netns:
        args = ['ip', '-n', netns, 'route', 'del', dest, 'via', gw]
    else:
        args = ['ip', 'route', 'del', dest, 'via', gw]

    _call_factory(
        args,
        f"Error deleting route to {dest} via {gw} on host {netns if netns else 'root'}"
    )
