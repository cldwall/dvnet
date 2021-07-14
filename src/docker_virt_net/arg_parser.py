import argparse, logging

log = logging.getLogger(__name__)

level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

def _log_level_check(level):
    if level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise argparse.ArgumentTypeError

    return level_map[level.upper()]


def parse_args():
    log.debug("Parsing input arguments")
    parser = argparse.ArgumentParser(description = "Docker-based Network Virtualizer")
    parser.add_argument(
        "net_definition",
        help = "JSON file containing the desired network's definition."
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
        "--log", nargs = '?', default = "INFO", type = _log_level_check,
        help = "Log level (DEBUG | INFO | WARNING | ERROR | CRITICAL)."
    )
    parser.add_argument(
        "-d", "--defaults", action = 'store_true',
        help = "Show the default values for optional elements in the JSON config files."
    )

    return parser.parse_args()
