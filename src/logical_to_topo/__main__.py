import logging

from . import arg_parser
from . import net_loading
from . import multi_router
from . import mono_router
from . import vlans

from docker_virt_net import coloured_log_formatter

niMap = {
    "multi-router": (
        multi_router.instantiate_net, multi_router.remove_net, multi_router.dump_graph_figure
    ),
    "mono-router": (
        mono_router.instantiate_net, mono_router.remove_net, mono_router.dump_graph_figure
    ),
    "vlans": (
        vlans.instantiate_net, vlans.remove_net, vlans.dump_graph_figure
    )
}

nlMap = {
    "gexf": net_loading.loadGexf,
    "edge-list": net_loading.loadEdgeList
}

def main():
    args = arg_parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(arg_parser.level_map[args.log])

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    if not args.disable_colours:
        ch.setFormatter(coloured_log_formatter.coloured_formatter())

    logger.addHandler(ch)

    logicalGraph = nlMap[args.format](args.logical_definition)

    if not logicalGraph:
        return -1

    if args.remove:
        niMap[args.algorithm][1](logicalGraph)
        return

    if args.dump:
        niMap[args.algorithm][2](logicalGraph, args.logical_definition.split('/')[-1].split('.')[0])
        return

    niMap[args.algorithm][0](logicalGraph, args.cliques, args.node_image, args.router_image, args.experiment)
    return

if __name__ == "__main__":
    main()
