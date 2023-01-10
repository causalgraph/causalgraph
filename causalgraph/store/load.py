#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Load Class, to import formats like NetworkX MultiDiGraph,
tigramite, graphml or gml into causalgraph Graph format."""

# general imports
from typing import Tuple
from logging import Logger
import numpy as np
import networkx as nx
# causalgraph and owlready imports
import causalgraph.graph as cg
import owlready2
from causalgraph.utils.logging_utils import init_logger


class Load():
    """ Contains all methods to to import formats like NetworkX MultiDiGraph,
    tigramite, graphml or gml into causalgraph Graph format.
    """
    def __init__(self, graph, logger: Logger = None) -> None:
        self.graph = graph
        if logger is not None:
            self.logger = logger
        else:
            self.logger = init_logger("Load")


    def nx(self, nx_graph: nx.MultiDiGraph, sql_db_filename: str, external_ontos: list=[]):
        """Loads a NetworkX MultiDiGraph and converts it to a causalgraph Graph() object.
        Will return a Graph() object.

        :param nx_graph: The NetworkX MultiDiGraph.
        :type nx_graph: nx.MultiDiGraph
        :param sql_db_filename: path and filename of new sqlite-file
        :type sql_db_filename: str
        :param external_ontos: List of paths or urls to external ontologies, default to []
        :type external_ontos: list
        :return: A causalgraph Graph() object.
        :rtype: Graph
        """
        # graph_dict from nx graph
        graph_dict = self.graph.map.graph_dict_from_nx(nx_graph)
        # Graph() object from graph_dict
        G_new = cg.Graph(sql_db_filename=sql_db_filename, external_ontos=external_ontos)
        G_new.map.fill_empty_graph_from_dict(graph_dict)
        return G_new
       

    def tigra(self, node_names: list, edge_names: dict, link_matrix: np.ndarray, q_matrix: np.ndarray, timestep_len_s: int, sql_db_filename: str):
        """Loads a Tigramite Graph representation and converts it to a causalgraph Graph() object.
        Will return a Graph() object.

        :param node_names: List of all nodes in the tigramite graph.
        :type node_names: list
        :param edge_names: Dict of all edges with their cause/ effect pairs.
        :type edge_names: dict
        :param link_matrix: The tigramite link matrix. Contains edges and their timelag.
        :type link_matrix: np.ndarray
        :param q_matrix: A tigramite PCMCI q_matrix
        :type q_matrix: np.ndarray
        :param timestep_len_s: Tigramite timestep length.
        :type timestep_len_s: int
        :param sql_db_filename: path and filename of new sqlite-file
        :type sql_db_filename: str
        :return: A causalgraph Graph() object.
        :rtype: Graph
        """
        # graph_dict from tigra representation
        graph_dict = self.graph.map.graph_dict_from_tigra(node_names, edge_names, link_matrix, q_matrix, timestep_len_s)
        # Graph() object from graph_dict
        G_new = cg.Graph(sql_db_filename=sql_db_filename)
        G_new.map.fill_empty_graph_from_dict(graph_dict)
        return G_new
        