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
        help = "GEXF file containing the desired network's definition."
    )
    parser.add_argument(
        "-a", "--algorithm", default = "naive-multi-router",
        choices = ["naive-multi-router"],
        help = "The algorithm to use for instantiating the network."
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
        "--log", nargs = '?', default = "info",
        choices = ["debug", "info", "warning", "error", "critical"],
        help = "Log level."
    )

    return parser.parse_args()
