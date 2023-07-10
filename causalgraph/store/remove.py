#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Remove Class to remove things from the store.
Store is equivalent to owlready2 World """

# general imports
from logging import Logger
import owlready2
from typing import Union
# causalgraph imports
import causalgraph.utils.owlready2_utils as owlutils
from causalgraph.utils.misc_utils import strict_types
from causalgraph.utils.logging_utils import init_logger


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


    @strict_types
    def causal_node(self, entity: Union[str, owlready2.Thing]) -> bool:
        """Deletes an individual of the class "CausalNode" or its subtypes with the name "individual_name".
        If the node is connected with edges, these are deleted as well.

        :param entity: The individual object to be deleted or its name.
        :type entity: Union[str, owlready2.Thing]
        :return: 'True' if delete successful
        :rtype: bool
        """
        # Check if individual exists and get its name and object
        individual_name, individual_obj = owlutils.get_name_and_object(entity, self.store)
        if individual_obj is None:
            self.logger.error(f"Individual '{individual_name}' does not exist.")
            return False
        # return false if individual is no CausalNode
        entity_of_right_class = owlutils.is_instance_of_type(individual_name, 'CausalNode', self.store, include_subtypes=True, logger= self.logger)
        if entity_of_right_class is False:
            self.logger.error(f"Individual '{individual_name}' is not of the class 'CausalNode' or a subclass.")
            return False
        # Delete entity if both prerequisites are met
        causal_edges_list = self._list_of_all_causal_edges_from_one_node(individual_name)
        if len(causal_edges_list) > 0 :
            self.causal_edges_from_node(individual_name)
        deletion_succ = self.delete_individual_of_type(individual_name, 'CausalNode', include_subtypes=True)
        return deletion_succ


    @strict_types
    def causal_edge(self, causal_edge: Union[str, owlready2.Thing]) -> bool:
        """Deletes an individual of class "CausalEdge" with the name "causal_edge" or
        the specific CausalEdge object.

        :param causal_edge: The individual edge object to be deleted or its name.
        :type causal_edge: Union[str, owlready2.Thing]
        :return: 'True' if delete successful
        :rtype: bool
        """
        deletion_successful = self.delete_individual_of_type(causal_edge, 'CausalEdge')
        return deletion_successful


    @strict_types
    def causal_edges(self, causal_node1: Union[str, owlready2.Thing], causal_node2: Union[str, owlready2.Thing]) -> bool:
        """Deletes all CausalEdges between 'hasCause' and 'hasEffect'

        :param causalNode1: First Node individual object of 'hasCause' or 'hasEffect'. Can also be just the name of it.
        :type causalNode1: Union[str, owlready2.Thing]
        :param causalNode2: Second Node individual object of 'hasCause' or 'hasEffect'. Can also be just the name of it.
        :type causalNode2: Union[str, owlready2.Thing]
        :return: 'True' if deletion successful
        :rtype: bool
        """
        causal_node1_name, causal_node1_obj = owlutils.get_name_and_object(causal_node1, self.store)
        causal_node2_name, causal_node2_obj = owlutils.get_name_and_object(causal_node2, self.store)
        # Return false if at least one of the nodes does not exist
        if causal_node1_obj is None or causal_node2_obj is None:
            self.logger.error("Could not delete CausalEdges between " +
                              f"[{causal_node1_name}|{causal_node1_obj}] and " +
                              f"[{causal_node2_name}|{causal_node2_obj}]. " +
                              "One or more individuals does not exist.")
            return False
        # Return false if at least one node is not really a CausalNode
        cause_of_specified_class = owlutils.is_instance_of_type(causal_node1_name, 'CausalNode', self.store, logger=self.logger, include_subtypes=True)
        effect_of_specified_class = owlutils.is_instance_of_type(causal_node2_name, 'CausalNode', self.store, logger=self.logger, include_subtypes=True)
        if cause_of_specified_class is False or effect_of_specified_class is False:
            self.logger.error(f"Could not delete CausalEdges between '[{causal_node1_name}|{causal_node1_obj}]' and " +
                              f"[{causal_node2_name}|{causal_node2_obj}]. Individuals are not of the specified class" +
                               "'CausalNode', they are specified as of the classes " +
                              f"{causal_node1_obj.is_a} and " +
                              f"{causal_node2_obj.is_a}.")
            return False
        # Delete entity if both prerequisites are met, dedicated logging for each
        edge_list = self._causal_edges_btw_nodes(causal_node1_name, causal_node2_name)
        if not edge_list:
            self.logger.error(f"No edges were deleted between '{causal_node1_name}' and '{causal_node2_name}'.")
            return True
        for edge in edge_list:
            edge = (str(edge).replace(f'[{self.individuals_onto_prefix}.','').replace(']',''))
            self.delete_individual_of_type(edge, 'CausalEdge')
        return True


    @strict_types
    def causal_edges_from_node(self, causal_node: Union[str, owlready2.Thing]) -> bool:
        """Deletes all CausalEdges which are connected with 'causal_node'

        :param causalNode: Object or name of the affected CausalNode
        :type causalNode: str
        :return: 'True' if delete successful
        :rtype: bool
        """
        causal_node_name, causal_node_obj = owlutils.get_name_and_object(causal_node, self.store)
        # Return false if individual does not exist
        if causal_node_obj is None:
            self.logger.error(f"Individual '[{causal_node_name}|{causal_node_obj}]' does not exist.")
            return False
        # Return false if individual is no CausalNode
        entity_of_right_class = owlutils.is_instance_of_type(causal_node_name, 'CausalNode', self.store, logger=self.logger, include_subtypes=True)
        if entity_of_right_class is False:
            self.logger.error(f"Individual '{causal_node_name}' is not of the class 'CausalNode'")
            return False
        # Delete edges if both prerequisites are met
        edge_list = self._list_of_all_causal_edges_from_one_node(causal_node_name)
        if not edge_list:
            self.logger.warning(f"No edges were deleted at '{causal_node_name}'.")
            return True
        for edge in edge_list:
            self.delete_individual_of_type(edge[0], 'CausalEdge')
        return True


    @strict_types
    def delete_individual_of_type(self, individual: Union[str, owlready2.Thing], type_of_individual: Union[str, owlready2.EntityClass], include_subtypes = False) -> bool:
        """Deletes an individual of the specified class/type.

        :param individual: The object to be deleted or its name.
        :type individual: Union[str, owlready2.Thing],
        :param type_of_individual: Class name or owlready EntityClass object of individual class.
        :type type_of_individual: Union[str, owlready2.EntityClass]
        :param include_subtypes: Switch to also include subtypes of typename in check, defaults to False
        :type include_subtypes: bool
        :return: 'True' if delete successful
        :rtype: bool
        """
        individual_name, individual_obj = owlutils.get_name_and_object(individual, self.store)
        # Check if individual (still) exists
        if individual_obj is None:
            self.logger.error(f"Did not delete {individual_name} because it does not exist")
            return False
        # return false if individual is not of the right class
        type_name, type_obj = owlutils.get_name_and_object(type_of_individual, self.store)
        entity_of_right_class = owlutils.is_instance_of_type(individual_name, type_obj, self.store, include_subtypes=include_subtypes, logger=self.logger)
        if entity_of_right_class is False:
            subclasses = owlutils.get_subclasses(type_obj, self.store, self.logger)
            if include_subtypes == True:
                error_msg = f"""Could not delete individual. Individual not of specified class or any of its subtypes.
                          '{individual_name}' is of class(es) '{individual_obj.is_a}'. Passed Class '{type_name}' or any of it's subclasses '{subclasses}'."""
            else:
                error_msg = f"""Could not delete individual. Individual not of specified class.
                          '{individual_name}' is of class(es) '{individual_obj.is_a}'. Passed Class '{type_name}'. Use option 'include_subtypes=True' if you also want to allow removal for subclasses of '{type_name}' """
            self.logger.error(error_msg)
            return False
        # Delete entity if both prerequisites are met based on type
        owlready2.destroy_entity(individual_obj)
        self.logger.info(f"Deleted entity '{individual_name}' of class '{individual_obj.is_a}'")
        self.store.save()
        return True


    @strict_types
    def entity(self, entity: Union[str, owlready2.Thing]) -> bool:
        """Removes entity from store. Entity can be provided as object or as string identifer.

        :param entity: Entity to remove
        :type entity: owlready2.Thing | str
        :return: deletion successful
        :rtype: bool
        """
        # Check Inputs and if entity exists in store
        if type(entity)==str:
            entity_str = entity
            entity = owlutils.get_entity_by_name(entity, self.store, self.logger, suppress_warn=True)
        elif type(entity) in list(self.store.classes()):
            entity_str = entity.get_name()
        else:
            self.logger.error(f"Did not delete '{entity}' because it was not found in store.")
            return False
        # Check Type of entity in case special treatment necessary
        if owlutils.is_instance_of_type(entity_str, 'CausalNode', self.store, include_subtypes=True, logger=self.logger):
            return self.causal_node(entity_str)
        elif owlutils.is_instance_of_type(entity_str, 'CausalEdge', self.store, include_subtypes=True, logger=self.logger):
            return self.causal_edge(entity_str)
        else:
            owlready2.destroy_entity(entity)
            self.logger.info(f"Deleted entity '{entity_str}' of class '{entity.is_a}'")
            self.store.save()
            return True


    def _causal_edges_btw_nodes(self, causal_node1: Union[str, owlready2.Thing], causal_node2: Union[str, owlready2.Thing]) -> list:
        """ Returns a list of all CausalEdges between 'causal_node1' and 'causal_node2'

        :param causal_node1: First Node individual object of 'hasCause' or 'hasEffect'. Can also be just the name of it.
        :type causal_node1: Union[str, owlready2.Thing]
        :param causal_node2: Second Node individual object of 'hasCause' or 'hasEffect'. Can also be just the name of it.
        :type causal_node2: Union[str, owlready2.Thing]
        :return: a list of all edges between 'hasCause' and 'hasEffect'
        :rtype: list of all causal_edges
        """
        causal_node1_iri = owlutils.get_entity_by_name(causal_node1, self.store, self.logger).iri
        causal_node2_iri = owlutils.get_entity_by_name(causal_node2, self.store, self.logger).iri
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
        causal_node_iri = owlutils.get_entity_by_name(causal_node, self.store, self.logger).iri
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
        