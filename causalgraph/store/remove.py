#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Remove Class to remove things from the store.
Store is equivalent to owlready2 World """

# general imports
from logging import Logger
import owlready2
# causalgraph imports
from causalgraph.utils.logging_utils import init_logger
from causalgraph.utils.owlready2_utils import entity_exists, get_entity_by_name, is_instance_of_class


class Remove():
    """ Contains all methods to remove resources from the store"""
    def __init__(self, store: owlready2.World, logger: Logger = None) -> None:
        self.store = store
        self.classes_onto_prefix = store.classes_onto.name
        self.individuals_onto_prefix = store.individuals_onto.name
        if logger is not None:
            self.logger = logger
        else:
            self.logger = init_logger("Remove")
        self.logger.info("Initialized the 'remove' functionalities.")


    def causal_node(self, individual_name: str) -> bool:
        """Deletes an individual of the class "CausalNode" with the name "individual_name".
        If the node is connected with edges, these are deleted as well.

        :param individual_name: name for individual
        :type individual_name: str
        :return: 'True' if delete successful
        :rtype: bool
        """
        # return false if individual does not exist
        if entity_exists(individual_name, self.store) is False:
            self.logger.error(f"Individual '{individual_name}' does not exist.")
            return False
        # return false if individual is no CausalNode
        entity_of_right_class = is_instance_of_class(individual_name, 'CausalNode', self.store, logger= self.logger)
        if entity_of_right_class is False:
            self.logger.error(f"Individual '{individual_name}' is not of the class 'CausalNode'")
            return False
        # Delete entity if both prerequisites are met
        causal_edges_list = self._list_of_all_causal_edges_from_one_node(individual_name)
        if len(causal_edges_list) > 0 :
            self.causal_edges_from_node(individual_name)
        deletion_succ = self.delete_individual_of_type(str(individual_name), 'CausalNode')
        return deletion_succ


    def causal_edge_by_name(self, causal_edge_name: str) -> bool:
        """Deletes an individual of class "CausalEdge" with the name "causal_edge_name".

        :param causal_edge_name: name for individual
        :type causal_edge_name: str
        :return: 'True' if delete successful
        :rtype: bool
        """
        deletion_successful = self.delete_individual_of_type(str(causal_edge_name), 'CausalEdge')
        return deletion_successful


    def causal_edges(self, causal_node1: str, causal_node2:str) -> bool:
        """Deletes all CausalEdges between 'hasCause' and 'hasEffect'

        :param causalNode1: name for individual 'hasCause' or 'hasEffect'
        :type causalNode1: str
        :param causalNode2: name for individual 'hasCause' or 'hasEffect'
        :type causalNode2: str
        :return: 'True' if deletion successful
        :rtype: bool
        """
        possibly_existing_entity_cause = get_entity_by_name(causal_node1, self.store, self.logger)
        possibly_existing_entity_effect = get_entity_by_name(causal_node2, self.store, self.logger)
        cause_of_specified_class = is_instance_of_class(causal_node1, 'CausalNode', self.store, logger=self.logger)
        effect_of_specified_class = is_instance_of_class(causal_node2, 'CausalNode', self.store, logger=self.logger)
        # return false if one of the entities does not exist
        if possibly_existing_entity_cause is None or possibly_existing_entity_effect is None:
            self.logger.error("Could not delete CausalEdges between " +
                             f"{causal_node1}:{possibly_existing_entity_cause} and " +
                             f"{causal_node2}:{possibly_existing_entity_effect}. " +
                              "One or more individuals does not exist.")
            return False
        # return false if one of the entities is no CausalNode
        if cause_of_specified_class is False or effect_of_specified_class is False:
            self.logger.error(f"Could not delete CausalEdges between '{causal_node1}' and" +
                              f"{causal_node2}. Individuals are not of the specified class" +
                               "'CausalNode', they are specified as of the classes " +
                              f"{possibly_existing_entity_cause.is_a} and " +
                              f"{possibly_existing_entity_effect.is_a}.")
            return False
        # Delete entity if both prerequisites are met, dedicated logging for each
        edge_list = self._causal_edges_btw_nodes(causal_node1, causal_node2)
        if not edge_list:
            self.logger.error(f"No edges were deleted between {causal_node1} and {causal_node2}.")
            return True
        for edge in edge_list:
            edge = (str(edge).replace(f'[{self.individuals_onto_prefix}.','').replace(']',''))
            self.delete_individual_of_type(edge, 'CausalEdge')
        return True


    def causal_edges_from_node(self, causal_node: str) -> bool:
        """Deletes all CausalEdges which are connected with 'causal_node'

        :param causalNode: class name/type of individual
        :type causalNode: str
        :return: 'True' if delete successful
        :rtype: bool
        """
        # return false if individual does not exist
        if entity_exists(causal_node, self.store) is False:
            self.logger.error(f"Individual '{causal_node}' does not exist.")
            return False
        # return false if individual is no CausalNode
        entity_of_right_class = is_instance_of_class(causal_node, 'CausalNode', self.store, logger= self.logger)
        if entity_of_right_class is False:
            self.logger.error(f"Individual '{causal_node}' is not of the class 'CausalNode'")
            return False
        # Delete edges if both prerequisites are met
        edge_list = self._list_of_all_causal_edges_from_one_node(causal_node)
        if not edge_list:
            self.logger.warning(f"No edges were deleted at '{causal_node}'.")
            return True
        for edge in edge_list:
            edge = (str(edge).replace(f'[{self.individuals_onto_prefix}.','').replace(']',''))
            self.delete_individual_of_type(edge, 'CausalEdge')
        return True


    def delete_individual_of_type(self, individual_name: str, class_of_individual: str) -> bool:
        """Deletes an individual of the specified class/type.

        :param class_of_individual: class name/type of individual
        :type class_of_individual: str
        :param name_for_individual: name for individual
        :type name_for_individual: str
        :return: 'True' if delete successful
        :rtype: bool
        """
        # return false if individual does not exist
        if entity_exists(individual_name, self.store) is False:
            self.logger.error(f"Did not delete {individual_name} because it does not exist")
            return False
        # return false if individual is not of the right class
        entity_of_right_class = is_instance_of_class(individual_name, class_of_individual, self.store, logger= self.logger)
        if entity_of_right_class is False:
            self.logger.error("Could not delete individual. Individual not of specified class." +
                             f"{individual_name} is of class '{class_of_individual}")
            return False
        # Delete entity if both prerequisites are met
        entity = get_entity_by_name(individual_name, self.store, self.logger)
        owlready2.destroy_entity(entity)
        self.logger.info(f"Deleted individual {individual_name} of class {class_of_individual}")
        self.store.save()
        return True


    def _causal_edges_btw_nodes(self, causal_node1: str, causal_node2: str) -> list:
        """ Returns a list of all CausalEdges between 'causal_node1' and 'causal_node2'

        :param causal_node1: name for individual 'hasCause' or 'hasEffect'
        :type causal_node1: str
        :param causal_node2: name for individual 'hasCause' or 'hasEffect'
        :type causal_node2: str
        :return: a list of all edges between 'hasCause' and 'hasEffect'
        :rtype: list of all causal_edges
        """
        causal_node1_iri = get_entity_by_name(causal_node1, self.store, self.logger).iri
        causal_node2_iri = get_entity_by_name(causal_node2, self.store, self.logger).iri
        list_causal_edges = list(self.store.sparql("""
            SELECT ?CausalEdge
            WHERE {
            """ + f"""
            <{causal_node1_iri}> ^{self.classes_onto_prefix}:hasCause ?CausalEdge .
            <{causal_node2_iri}> ^{self.classes_onto_prefix}:hasEffect ?CausalEdge 
            """ + "}"
            ))
        list_causal_edges_the_other_way = list(self.store.sparql("""
            SELECT ?CausalEdge
            WHERE {
            """ + f"""
            <{causal_node1_iri}> ^{self.classes_onto_prefix}:hasEffect ?CausalEdge .
            <{causal_node2_iri}> ^{self.classes_onto_prefix}:hasCause ?CausalEdge 
            """ + "}"
            ))
        list_edges = list_causal_edges_the_other_way + list_causal_edges
        return list_edges


    def _list_of_all_causal_edges_from_one_node(self, causal_node: str) -> list:
        """Returns a list of all CausalNodes which are connected with 'causal_node'

        :param causal_node: class name/type of individual
        :type causal_node: str
        :return: a list of all edges on 'causalNode'
        :rtype: list
        """
        # get nodes that are connected to the specified node via incoming or outgoing edges
        causal_node_iri = get_entity_by_name(causal_node, self.store, self.logger).iri
        list_nodes_has_cause = list(self.store.sparql ("""
            SELECT ?CausalEdge
            WHERE {
            """ + f"""
            <{causal_node_iri}> ^{self.classes_onto_prefix}:hasCause ?CausalEdge . 
            """ + "}"
            ))
        list_nodes_has_effect = list(self.store.sparql ("""
            SELECT ?CausalEdge
            WHERE {
            """ + f"""
            <{causal_node_iri}> ^{self.classes_onto_prefix}:hasEffect ?CausalEdge . 
            """ + "}"
            ))
        result = list_nodes_has_cause + list_nodes_has_effect
        return result
        