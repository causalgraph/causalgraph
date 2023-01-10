#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Export Class, to export a cg graph to other
formats like nx, tigramite, graphml, gml."""

# general imports
from typing import Tuple
from logging import Logger
import numpy as np
from networkx import MultiDiGraph, write_graphml, write_gml
# causalgraph and owlready imports
import owlready2
from causalgraph.utils.logging_utils import init_logger


class Export():
    """ Contains all methods to export cg graphs to other formats like NetworkX, Tigramite,
    graphml and gml.
    """
    def __init__(self, graph, logger: Logger = None) -> None:
        self.graph = graph
        if logger is not None:
            self.logger = logger
        else:
            self.logger = init_logger("Export")
    

    def nx(self) -> MultiDiGraph:
        """Converts a cg graph into a NetworkX MultiDiGraph and returns it.
        This method adds the cg properties to the NetworkX individuals as NetworkX attributes.
        CAUTION: Will not add Creators because NetworkX cannot handle them. But Creators will still
        be part of properties of Nodes and Edges. Lonely Creators will be lost, because there are 
        no records of them without the properties of any CausalEdge or CausalNode. Individual types
        within the properties will be broken down to CausalNode or CausalEdge.

        :return: The converted NetworkX MultiDiGraph.
        :rtype: nx.MultiDiGraph
        """
        G_nx = MultiDiGraph()
        graph_dict = self.graph.map.all_individuals_to_dict()
        for individual in graph_dict:
            individual_type = graph_dict[individual]["type"]
            individual_name = individual
            properties_dict = graph_dict[individual]
            if individual_type == "CausalNode":
                G_nx.add_node(individual_name, **properties_dict)
            elif individual_type == "CausalEdge":
                cause = graph_dict[individual]["hasCause"][0]
                effect = graph_dict[individual]["hasEffect"][0]
                G_nx.add_edge(cause, effect, **properties_dict)
            else:
                self.logger.error(f"Individual type '{individual_type}' unknown.")
                return False
        return G_nx


    def graphml(self, directory: str, filename: str) -> None:
        """Saves a cg graph to a given path as a .graphml-file.

        :param directory: Path to the directory under which the .graphml-file will be saved.
        :type directory: str
        :param filename: Filename of the file to be saved
        :type filename: str
        """
        # Convert cg Graph to NX Graph
        g_nx = self.nx()
        nodes = g_nx.nodes.data()
        edges = g_nx.edges.data()
        # Covert list properties to raw strings, because graphml cannot handle lists
        for node in nodes:
            for i in node[1]:
                if type(node[1][i]) in [list, owlready2.IndividualValueList]:
                    node[1][i] = str(node[1][i])
        # Covert list properties to raw strings, because graphml cannot handle lists
        for edge in edges:
            for i in edge[2]:
                if type(edge[2][i]) in [list, owlready2.IndividualValueList]:
                    edge[2][i] = str(edge[2][i])
        # Write gml file to path
        write_graphml(g_nx, f'{directory}/{filename}.graphml')


    def gml(self, directory: str, filename: str) -> None:
        """Saves a cg graph to a given path as a .gml-file.

        :param directory: Path to the directory under which the .gml-file will be saved.
        :type directory: str
        :param filename: Filename of the file to be saved
        :type filename: str
        """
        # Convert cg Graph to NX Graph
        g_nx = self.nx()
        nodes = g_nx.nodes.data()
        edges = g_nx.edges.data()
        # Covert list properties to raw strings, because gml cannot handle lists
        for node in nodes:
            for i in node[1]:
                if type(node[1][i]) in [list, owlready2.IndividualValueList]:
                    node[1][i] = str(node[1][i])
        # Covert list properties to raw strings, because gml cannot handle lists
        for edge in edges:
            for i in edge[2]:
                if type(edge[2][i]) in [list, owlready2.IndividualValueList]:
                    edge[2][i] = str(edge[2][i])
        # Write gml file to path
        write_gml(g_nx, f'{directory}/{filename}.gml')


    def tigra(self) -> Tuple[list, dict, np.ndarray, np.ndarray, int]:
        """Creates a Tigramite graph from a cg graph. Right now, this method only can handle
        edges, nodes, timelags and confidence. Nodes with multiple class types besides CausalNode
        will be broken down to type CausalNode only.

        :param graph_dict: Properties dict of a cg graph.
        :type graph_dict: dict
        :return: Tuple with the links as a boolean matrix, the variable names as a list of
        strings, the edges as dict with its cause and effect and integer containing the
        tigra timestep length. [node_names, edge_names, link_matrix, q_matrix, timestep_len_s].
        :rtype: Tuple[np.ndarray, list, dict, int]
        """
        graph_dict = self.graph.map.all_individuals_to_dict()
        if len(graph_dict) <= 1:
            raise ValueError("You can't draw an empty graph or a graph with only one node using Tigramite!")

        list_of_edges = []
        list_cg_timelags = []
        list_tigra_timelags = []
        list_edge_confidence = []
        node_names = []
        edge_names = {}
        # Get list of cg timelags:
        for individual in graph_dict:
            individual_type = graph_dict[individual]["type"]
            if individual_type == "CausalEdge":
                # Get timelag or None
                time_lag_s = graph_dict[individual].get("time_lag_s", None)
                if time_lag_s is not None:
                    list_cg_timelags.append(time_lag_s)
        # Get timestep length (smallest timelag in list_cg_timelags)
        try:
            timestep_len_s = min(list_cg_timelags)
        except ValueError:
            timestep_len_s = 1

        for individual in graph_dict:
            individual_type = graph_dict[individual]["type"]
            individual_name = individual
            # Fill list of node names
            if individual_type == "CausalNode":
                node_names.append(individual_name)
            # Fill list of edges, incl. their tigramite timelag
            if individual_type == "CausalEdge":
                cause = graph_dict[individual].get("hasCause", [None])[0]
                effect = graph_dict[individual].get("hasEffect", [None])[0]
                # If timelag exists for current edge, convert it to tigramite timeframe.
                # If it doesnt exist, set it to 0. After that add it to list_tigra_timelags
                time_lag_s = round(graph_dict[individual].get("hasTimeLag", 0)/timestep_len_s)
                list_tigra_timelags.append(time_lag_s)
                # Get confidence for current edge. set it to 0 (edge present) if it does not exist
                confidence = graph_dict[individual].get('hasConfidence', 0)
                list_edge_confidence.append(confidence)
                # Add edge with its timelag to list_of_edges
                list_of_edges.append((cause, effect, time_lag_s))
                edge_names[individual_name] = {}
                edge_names[individual_name] = {"hasCause": cause, "hasEffect": effect}

        num_of_nodes = len(node_names)
        # graph consists of nodes only
        if len(edge_names) == 0:
            link_matrix = np.zeros((num_of_nodes, num_of_nodes, 5))
            q_matrix = np.ones((num_of_nodes, num_of_nodes, 5))
            return (node_names, [], link_matrix, q_matrix, timestep_len_s)
        # if there are edges, create list of edge indices with their timelags
        edge_indices = [(node_names.index(cause), node_names.index(effect), timelag)
                            for (cause, effect, timelag) in list_of_edges]
        # Init link_matrix with the proper dimension and fill it with zeros for now.
        link_matrix = np.zeros((num_of_nodes, num_of_nodes, max(list_tigra_timelags)+1))
        # Set 1 at the right indices to give information about the timelag value
        cause_ind, effect_ind, time_ind = zip(*edge_indices)
        link_matrix[cause_ind, effect_ind, time_ind] = 1
        # Init q_matrix with the proper dimension and fill it with ones (edges not present) for now
        q_matrix = np.ones((num_of_nodes, num_of_nodes, max(list_tigra_timelags)+1))
        q_matrix[cause_ind, effect_ind, time_ind] = list_edge_confidence
        return (node_names, edge_names, link_matrix, q_matrix, timestep_len_s)

