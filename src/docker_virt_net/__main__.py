import logging, argparse
from . import coloured_log_formatter
from . import config_parser

def main():
    # Parsing input arguments
    parser = argparse.ArgumentParser(description = "Docker-based Network Virtualizer")
    parser.add_argument("net_definition", help = "JSON file containing the desired network's definition.")
    args = parser.parse_args()

    # Logger initialization
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(coloured_log_formatter.coloured_formatter())

    logger.addHandler(ch)

    config_parser.parse_config(args.net_definition)

if __name__ == "__main__":
    main()
