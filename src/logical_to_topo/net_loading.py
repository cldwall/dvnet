import logging

import networkx as nx
import pandas as pd

from typing import Union

log = logging.getLogger(__name__)

def loadGexf(defPath: str, directed: bool) -> Union[nx.Graph, None]:
    log.info(f"Loading graph at {defPath} (gexf)...")
    try:
        logicalGraph = nx.read_gexf(defPath)
    except FileNotFoundError:
        log.exception("Couldn't load the graph definition")
        return None

    return logicalGraph

def loadEdgeList(defPath: str, directed: bool) -> Union[nx.Graph, None]:
    log.info(f"Loading graph at {defPath} (edge-list) as a{' directed' if directed else 'n undirected'} graph...")
    try:
        df = pd.read_csv(defPath, header = None)
        logicalGraph = nx.parse_edgelist(
            [f"{edge[0]} {edge[1]}" for _, edge in df.iterrows()],
            nodetype = str,
            create_using = nx.Graph if not directed else nx.DiGraph)
    except (FileNotFoundError, IndexError):
        log.exception("Couldn't load the graph definition")
        return None
    return logicalGraph
