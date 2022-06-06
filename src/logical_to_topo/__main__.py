import logging, sys

import networkx as nx

from . import arg_parser
from . import naive_multi_router
from . import naive_mono_router

from docker_virt_net import coloured_log_formatter

niMap = {
    "naive-multi-router": (
        naive_multi_router.instantiate_net, naive_multi_router.remove_net, naive_multi_router.dump_graph_figure
    ),
    "naive-mono-router": (
        naive_mono_router.instantiate_net, naive_mono_router.remove_net, naive_mono_router.dump_graph_figure
    )
}

def main():
    args = arg_parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(arg_parser.level_map[args.log])

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(coloured_log_formatter.coloured_formatter())

    logger.addHandler(ch)

    log = logging.getLogger(__name__)

    try:
        logicalGraph = nx.read_gexf(args.logical_definition)
    except FileNotFoundError as err:
        log.critical(f"Couldn't load the graph definition: {err.cause}")
        sys.exit(-1)

    if args.remove:
        niMap[args.algorithm][1](logicalGraph)
        return

    if args.dump:
        niMap[args.algorithm][2](logicalGraph, args.logical_definition.split('/')[-1].split('.')[0])
        return

    niMap[args.algorithm][0](logicalGraph)
    return

if __name__ == "__main__":
    main()
