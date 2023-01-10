#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains functionalities to map a cg graph to and from a dictionary.
"""
# general imports
import owlready2
from logging import Logger
# causalgraph imports
from causalgraph.utils.logging_utils import init_logger
from causalgraph.utils.owlready2_utils import get_entity_by_name
from causalgraph.utils.owlready2_utils import create_individual_of_type
from causalgraph.utils.owlready2_utils import validate_prop_for_type
from causalgraph.utils.owlready2_utils import validate_data_type_for_property
import networkx as nx
import numpy as np
import causalgraph.utils.owlready2_utils as owlutils


class Mapping():
    def __init__(self, graph, logger: Logger = None) -> None:
        self.graph = graph
        if logger is not None:
            self.logger = logger
        else:
            self.logger = init_logger("Mapping")
        self.logger.info("Initialized the 'mapping' functionalities.")
        self.causalgraph_object_properties = [prop.name for prop in list(self.graph.classes_onto.object_properties())] + ["comment"]
        self.causalgraph_data_properties = [prop.name for prop in list(self.graph.classes_onto.data_properties())]
        self.third_party_object_properties = []
        self.third_party_data_properties = []


    def update_third_party_properties(self):
        """Updates the third party properties. This method will be called after importing new ontologies.
        """
        all_data_props = list(self.graph.store.data_properties())
        all_obj_props = list(self.graph.store.object_properties())
        for prop in all_data_props:
            if prop.name not in self.third_party_data_properties and prop.name not in self.causalgraph_data_properties:
                self.third_party_data_properties.append(prop.name)
        for prop in all_obj_props:
            if prop.name not in self.third_party_object_properties and prop.name not in self.causalgraph_object_properties:
                self.third_party_object_properties.append(prop.name)


    def all_individuals_to_dict(self) -> dict:
        """Will create a dict containing all individuals and their properties.
        Only CausalNodes and CausalEdges will be part of the dict. CausalNodes with multiple Classes
        (e. g. via third party ontology import) will be broken down to the class type CausalNode only.

        :return: Dict containing all individuals with their properties.
        :rtype: dict
        """
        dict_graph = {}
        # Get all CausalNodes and their subclasses
        causalnodes_list = owlutils.get_all_causalnodes(self.graph.store)
        # Get all CausalEdges
        causaledges_list = owlutils.get_all_causaledges(self.graph.store)
        # Handling all CausalNodes
        for causalnode in causalnodes_list:
            # Append the dict for single individuals to the dict of the whole graph
            causalnode_prop_dict = self.__add_properties_to_dict(individual=causalnode[0], indi_type='CausalNode')
            if len(causalnode_prop_dict) > 0:
                dict_graph[causalnode[0].name] = causalnode_prop_dict
        # Handling all CausalEdge
        for causaledge in causaledges_list:
            # Append the dict for single individuals to the dict of the whole graph
            causaledge_prop_dict = self.__add_properties_to_dict(individual=causaledge[0], indi_type='CausalEdge')
            if len(causaledge_prop_dict) > 0:
                dict_graph[causaledge[0].name] = causaledge_prop_dict
        return dict_graph


    def __add_properties_to_dict(self, individual: object, indi_type: str) -> dict:
        """Creates a properties dict of a single individual and returns it. Type of individual must be
        passed due to possible multi class inheritance.

        :param individual: Individual object
        :type individual: object
        :param type: Object type (e. g. CausalNode, CausalEdge)
        :type type: str
        :raises ValueError: Unvalid property Error
        :return: Properties dict of single individual
        :rtype: dict
        """
        prop_dict = {'type': indi_type, 'iri': individual.iri}
        # Iteratively fill the property dictionary
        possible_props = self.causalgraph_object_properties + self.causalgraph_data_properties + self.third_party_data_properties + self.third_party_object_properties
        for prop in individual.get_properties():
            # Validate that the property is in valid
            if prop.name not in possible_props:
                raise ValueError(f'{prop.name} is not a valid property since it is not contained in the mapping_dict!')
            # Get value of the property
            prop_value = getattr(individual, prop.name)
            if type(prop_value) in [int, float, str]:
                extracted_values = prop_value
            else:
                try:
                    extracted_values = [i.name for i in prop_value]
                except (TypeError, AttributeError):
                    try:
                        extracted_values = prop_value.name
                    except (TypeError, AttributeError):
                        extracted_values = prop_value
            prop_dict[prop.name] = extracted_values
        return prop_dict


    def graph_dict_from_nx(self, nx_graph: nx.MultiDiGraph) -> dict:
        """Generates a properties dict from a NetworkX MultiDiGraph. The edges must contain edge properties that
        matches the causalgraph or imported third party properties like "hasCause", "hasConfidence", "type" etc.

        :param nx_graph: A NetworkX MultiDiGraph. Edges must contain properties: [isCausing, isAffectedBy]
        :type nx_graph: nx.MultiDiGraph
        :return: Properties dict of whole networkX graph
        :rtype: dict
        """
        nx_nodes = nx_graph.nodes(data=True)
        nx_edges = nx_graph.edges(data=True)
        graph_dict = {}
        for node in nx_nodes:
            node_name = node[0]
            node_props_dict = dict(node[1])
            # Add node_dict to graph_dict
            graph_dict[node_name] = node_props_dict
        for edge in nx_edges:
            edge_props_dict = dict(edge[2])
            # Get edge_name by matching cause and effect for current edge within nodes
            cause = edge[0]
            effect = edge[1]
            cause_edges = graph_dict[cause]['isCausing']
            effect_edges = graph_dict[effect]['isAffectedBy']
            # Get edge name via iri
            edge_name = str(edge_props_dict['iri'])[str(edge_props_dict['iri']).find('#')+1:]
            # Add edge_dict to graph_dict
            graph_dict[edge_name] = edge_props_dict
        return graph_dict


    def graph_dict_from_tigra(self, node_names: list, edge_names: dict, link_matrix: np.ndarray, q_matrix: np.ndarray, timestep_len_s: int) -> dict:
        """Generates a properties dict from a Tigramite Graph representation. This method will only handle classic causalgraph
        properties like "hasCause", "hasEffect", "hasTimeLag" etc. Creators and third party properties will not be created.
        This method will not add a third party key/value pairs to the dict, as well as comments, creators or iris.

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
        :return: Properties dict of whole Tigramite Graph representation.
        :rtype: dict
        """
        graph_dict = {}

        # Compare number of nodes in link_matrix with the number of node_names
        if len(link_matrix) != len(node_names):
            self.logger.error("Too few nodes in the link matrix or the list of node names.")
            return False
        # Add nodes without their properties to graph_dict
        for nodes in node_names:
            graph_dict[nodes] = {"type": "CausalNode"}
        # Handle all edges, also add missing node properties
        for node_ind, matrix in enumerate(link_matrix):
            # Get indices of cause/effect pair and timelag
            possibly_edge = np.argwhere(matrix)
            # Only handle matrices with edges and timelags
            for edge in possibly_edge:
                cause = node_names[node_ind]
                effect = node_names[edge[0]]
                # Get time_lag and convert it with timestep_len_s to cg timeframe
                discrete_time_lag = edge[1]
                time_lag = discrete_time_lag * timestep_len_s
                # Get confidence
                confidence = q_matrix[node_ind, edge[0], edge[1]]
                # Get edge_name (dict key) with pair of cause and effect (values)
                try:
                    edge_name = list(edge_names.keys())[list(edge_names.values()).index({"hasCause": cause, "hasEffect": effect})]
                    # Make sure doubles edges can be handled correctly.
                    # To do so, pop the current one so the other edge is accessible in the next iteration.
                    edge_names.pop(edge_name)
                except ValueError:
                    self.logger.error(f"There is no edge with cause {cause} and effect {effect}")
                    return False
                # Add edge with its cause, effect, confidence and timelag to graph_dict
                graph_dict[edge_name] = {}
                graph_dict[edge_name].update({"hasCause": [cause]})
                if confidence != 0.0:
                    graph_dict[edge_name].update({"hasConfidence": float(confidence)})
                graph_dict[edge_name].update({"hasEffect": [effect]})
                if time_lag != 0.0:
                    graph_dict[edge_name].update({"hasTimeLag": float(time_lag)})
                graph_dict[edge_name].update({"type": "CausalEdge"})
                # Add node properties "affected_by" and "causing"
                graph_dict[cause].setdefault("isCausing", []).append(edge_name)
                graph_dict[effect].setdefault("isAffectedBy", []).append(edge_name)
        return graph_dict


    def fill_empty_graph_from_dict(self, graph_dict: dict):
        """Fills a empty graph from a passed graph_dict and returns the Graph() object.

        :param graph_dict: A causalgraph properties dict of a whole graph
        :type graph_dict: dict
        :return: The filled causalgraph object
        :rtype: causalgraph.Graph()
        """
        if type(graph_dict) not in [dict] or graph_dict == {}:
            self.logger.error("Filling graph with individuals from graph_dict wasn't successful. Passed graph_dict not valid.")
            return self.graph
        # Check if Graph is empty
        causalnodes_list = owlutils.get_all_causalnodes(self.graph.store)
        causaledges_list = owlutils.get_all_causaledges(self.graph.store)
        if causaledges_list or causalnodes_list:
            self.logger.error("Filling graph with individuals from graph_dict wasn't successful. Graph is not empty.")
            return self.graph

        # Iterate over all individuals in graph_dict
        # Handling CausalNode first
        for individual in graph_dict:
            individual_type = graph_dict[individual]['type']
            # Handling CausalNodes
            if individual_type == 'CausalNode':
                # Create props for later usage as kwargs in G.add.causal_node()
                individual_prop_dict = self.__create_individual_kwargs_props(graph_dict=graph_dict, individual=individual, type_class=individual_type)
                # Create CausalNode with props kwargs
                self.graph.add.causal_node(individual, **individual_prop_dict)      

        # Iterate over individuals over graph_dict
        # Handling CausalEdges after CausalNodes
        for individual in graph_dict:
            individual_type = graph_dict[individual]['type']
            # Handling CausalEdges
            if individual_type == 'CausalEdge':
                # Create props for later usage as kwargs in G.add.causal_edge()
                individual_prop_dict = self.__create_individual_kwargs_props(graph_dict=graph_dict, individual=individual, type_class=individual_type)
                # Create CausalEdge with props kwargs
                cause = graph_dict[individual]['hasCause'][0]
                effect = graph_dict[individual]['hasEffect'][0]
                edge_name = individual
                self.graph.add.causal_edge(cause_node_name=cause, effect_node_name=effect, name_for_edge=edge_name, **individual_prop_dict)

        # Return filled Graph() object
        return self.graph


    def __create_individual_kwargs_props(self, graph_dict: dict, individual: str, type_class: str) -> dict:
        """This method returns a props dict that can be used to passed as kwargs to the functions add.causal_node()
        or add.causal_edge(). The prop dict will not be containing the properties ["isCausing", "isAffectedBy", "hasCause", "hasEffect"].

        :param graph_dict: A causalgraph properties dict of a whole graph
        :type graph_dict: dict
        :param individual: Name of the individual
        :type individual: str
        :param type_class: Type of the individual (e. g. CausalEdge or CausalNode)
        :type type_class: str
        :return: A properties dict that can be passed as kwargs to add.causal_node() or add.causal_edge()
        :rtype: dict
        """
        individual_prop_dict = {}

        limiter = []
        if type_class == "CausalNode":
            limiter = ['isCausing', 'isAffectedBy']
        elif type_class == "CausalEdge":
            limiter = ['hasCause', 'hasEffect']
        else:
            self.logger.error(f"Type class '{type_class}' not supported. Empty dict will be returned.")
            return {}

        for prop in graph_dict[individual]:
            if prop not in ['iri', 'type']:
                # if prop is object property
                if prop in (self.causalgraph_object_properties + self.third_party_object_properties) and prop not in limiter:
                    prop_value = graph_dict[individual][prop]
                    if prop == 'comment':
                        comments = list(prop_value)
                        individual_prop_dict[prop] = comments
                    else:
                        if type(prop_value) is list:
                            for value in prop_value:
                                exists = owlutils.entity_exists(entity_name=value, store=self.graph.store)
                                if not exists:
                                    range = owlutils.get_range_of_property(store=self.graph.store, property_name=prop)
                                    new_indi_name = owlutils.create_individual_of_type(
                                        class_of_individual=range[0].name,
                                        store=self.graph.store,
                                        name_for_individual=value,
                                        logger=self.logger
                                    )
                                    new_indi = owlutils.get_entity_by_name(name_of_entity=new_indi_name, store=self.graph.store, logger=self.logger)
                                    try:
                                        individual_prop_dict[prop].append(new_indi)
                                    except:
                                        individual_prop_dict[prop] = [new_indi]
                                else:
                                    old_indi = owlutils.get_entity_by_name(name_of_entity=value, store=self.graph.store, logger=self.logger)
                                    try:
                                        individual_prop_dict[prop].append(old_indi)
                                    except:
                                        individual_prop_dict[prop] = [old_indi]
                        else:
                            exists = owlutils.entity_exists(entity_name=prop_value, store=self.graph.store)
                            if not exists:
                                range = owlutils.get_range_of_property(store=self.graph.store, property_name=prop)
                                new_indi_name = owlutils.create_individual_of_type(
                                    class_of_individual=range[0].name,
                                    store=self.graph.store,
                                    name_for_individual=prop_value,
                                    logger=self.logger
                                )
                                new_indi = owlutils.get_entity_by_name(name_of_entity=new_indi_name, store=self.graph.store, logger=self.logger)
                                individual_prop_dict[prop] = new_indi
                            else:
                                old_indi = owlutils.get_entity_by_name(name_of_entity=prop_value, store=self.graph.store, logger=self.logger)
                                individual_prop_dict[prop] = old_indi
                # if prop is data property
                elif prop in (self.causalgraph_data_properties + self.third_party_data_properties):
                    prop_value = graph_dict[individual][prop]  
                    individual_prop_dict[prop] = prop_value
                # property unknown
                else:
                    if prop not in limiter:
                        self.logger.warning(f"Property {prop} unknown. Will be skipped. For creation please import the right ontologies.")
                    
        return individual_prop_dict


    def update_graph_from_dict(self, graph_dict: dict=None):
        raise NotImplementedError


    def __validate_property(self, property: str) -> bool:
        """Checks if property is valid and therefore within the causalgraph_object_properties, causalgraph_data_properties or third_party_properties list.
        Returns True if valid, otherwise False.

        :param property: Name of property
        :type property: str
        :return: True if valid, otherwise False.
        :rtype: bool
        """
        possible_props = self.causalgraph_object_properties + self.causalgraph_data_properties + self.third_party_data_properties + self.third_party_object_properties
        return property in possible_props

