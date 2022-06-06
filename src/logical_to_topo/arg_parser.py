import argparse, logging

log = logging.getLogger(__name__)

level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
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
        "-s", "--show", nargs = '?', default = "NOSHOW", const = "NOSTORE",
        help = "Show a visual representation of the network defined on <net_definition> (PATH to save file)."
    )
    parser.add_argument(
        "--log", nargs = '?', default = "INFO",
        choices = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help = "Log level."
    )
    parser.add_argument(
        "-d", "--defaults", action = 'store_true',
        help = "Show the default values for optional elements in the JSON config files."
    )

    return parser.parse_args()
