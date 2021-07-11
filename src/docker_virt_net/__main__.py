import logging
from . import arg_parser
from . import coloured_log_formatter
from . import config_parser
from . import network_instantiation
from . import net_visualization

def main():
    args = arg_parser.parse_args()

    # Logger initialization
    logger = logging.getLogger()
    logger.setLevel(args.log)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(coloured_log_formatter.coloured_formatter())

    logger.addHandler(ch)

    net_conf, net_graph = config_parser.parse_config(args.net_definition)

    if args.show != "NOSHOW":
        net_visualization.show_net(net_graph, args.show)
        return 0

    if args.remove:
        network_instantiation.delete_net(net_conf)
        return 0

    network_instantiation.instantiate_network(net_conf, net_graph)

if __name__ == "__main__":
    main()
