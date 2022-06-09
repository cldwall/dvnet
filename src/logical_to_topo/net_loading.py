import logging

import networkx as nx
import pandas as pd

from typing import Union

log = logging.getLogger(__name__)

def loadGexf(defPath: str) -> Union[nx.Graph, None]:
    try:
        logicalGraph = nx.read_gexf(defPath)
    except FileNotFoundError:
        log.exception("Couldn't load the graph definition")
        return None

    return logicalGraph

def loadEdgeList(defPath: str) -> Union[nx.Graph, None]:
    try:
        df = pd.read_csv(defPath, header = None)
        logicalGraph = nx.parse_edgelist([f"{edge[0]} {edge[1]}" for _, edge in df.iterrows()], nodetype = str)
    except (FileNotFoundError, IndexError):
        log.exception("Couldn't load the graph definition")
        return None
    return logicalGraph
