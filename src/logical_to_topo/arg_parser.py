import argparse, logging

log = logging.getLogger(__name__)

level_map = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

def parse_args():
    log.debug("Parsing input arguments")
    parser = argparse.ArgumentParser(description = "Logical to Physical topology mapper")
    parser.add_argument(
        "logical_definition",
        help = "File containing the desired network's definition."
    )
    parser.add_argument(
        "-f", "--format", default = "gexf",
        choices = ["gexf", "edge-list"],
        help = "The format of the provided network definition."
    )
    parser.add_argument(
        "-a", "--algorithm", default = "naive-multi-router",
        choices = ["multi-router", "mono-router", "vlans"],
        help = "The algorithm to use for instantiating the network."
    )
    parser.add_argument(
        "--node_image", default = "pcollado/d_host",
        help = "The Docker image to run on hosts."
    )
    parser.add_argument(
        "--router_image", default = "pcollado/d_router",
        help = "The Docker image to run on routers."
    )
    parser.add_argument(
        "-e", "--experiment", action = 'store_true',
        help = "Instantiate additional infrastructure for running experiments."
    )
    parser.add_argument(
        "-r", "--remove", action = 'store_true',
        help = "Remove the instances of elements found on <net_definition>."
    )
    parser.add_argument(
        "-d", "--dump", action = 'store_true',
        help = "Dump visualisation and GEXF files for the logical and physical topologies."
    )
    parser.add_argument(
        "-c", "--cliques", action = 'store_true',
        help = "Dump discovered cliques. This is only applicable for the `vlans` algorithm."
    )
    parser.add_argument(
        "--log", nargs = '?', default = "info",
        choices = ["debug", "info", "warning", "error", "critical"],
        help = "Log level."
    )
    parser.add_argument(
        "--disable-colours", action = 'store_true',
        help = "Disable the use of escape sequences adding colours to logging."
    )

    return parser.parse_args()
