import matplotlib, logging
import matplotlib.pyplot as plt
import networkx

try:
    matplotlib.use("TkAgg")
except ImportError:
    matplotlib.use("agg")

log = logging.getLogger(__name__)

colour_map = {
    "host": "#00CC66",
    "router": "#0066CC",
    "bridge": "#CCCC00",
    "internetgw": "#B300B3",
    "notype": "#CC2200"
}

def show_net(net_graph, fig_path, k = 0.5, n_size = 400, e_size = 1, f_size = 10):
    log.debug("Showing a network visualization")
    pos = networkx.spring_layout(net_graph, k = k)
    fig = plt.figure(f"{net_graph.graph.get('name', 'Unnamed Graph').capitalize()} Network Visualization")

    node_colours = [colour_map[node[1].get("type", "notype")] for node in net_graph.nodes.data()]

    node_colours = []
    for node in net_graph.nodes.data():
        node_colours.append(colour_map[node[1].get("type", "notype")])
        if node[1].get("internet_gw", False):
            node_colours[-1] = colour_map['internetgw']

    networkx.draw_networkx_nodes(net_graph, pos, node_color = node_colours, node_size = n_size)
    networkx.draw_networkx_edges(net_graph, pos, width = e_size)
    networkx.draw_networkx_labels(net_graph, pos, font_family = "sans-serif", font_weight = "bold", font_size = f_size)
    plt.axis("off")
    plt.title(net_graph.graph.get("name", "Unnamed Graph"))
    plt.plot()

    if fig_path != "NOSTORE":
        plt.savefig(
            "{}.png".format(
                '_'.join(net_graph.graph.get("name", "Unnamed Graph").split(' '))
            ),
            dpi = 200
        )
    else:
        plt.show()
