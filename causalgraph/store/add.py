#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Add Class to add things to the store.
Store is equivalent to owlready2 World """

# general imports
import itertools
from logging import Logger
import owlready2
from typing import Union
# causalgraph imports
import causalgraph.utils.owlready2_utils as owlutils
from causalgraph.utils.misc_utils import strict_types
from causalgraph.utils.logging_utils import init_logger


class Add():
    """ Contains all methods to add resources to the store """
    def __init__(self, store: owlready2.World, logger: Logger = None, validate_domain_range: bool = True) -> None:
        self.store = store
        self.validate_domain_range = validate_domain_range
        if logger is not None:
            self.logger = logger
        else:
            self.logger = init_logger("Add")
        self.logger.info("Initialized the 'add' functionalities.")
        self.classes_prohibited_from_causal_connections = self._init_classes_prohibited_for_causal_connections()


    def _init_classes_prohibited_for_causal_connections(self) -> list:
        """Configuration function which returns a flattened list of all classes excluded
        from causal connections. For those classes and their subclasses it is not allowed
        to draw causal_connections in between.

        :return: list of excluded classes and subclasses.
        :rtype: list
        """
        # defines baseline for classes between whose individuals no CausalEdges are allowed
        base_prohibitions = ['CausalEdge', 'CausalGraph', 'Creator']
        # get subclasses as well and flatten list
        prohibited_with_subtypes = [owlutils.get_subclasses(class_name, self.store) for class_name in base_prohibitions]
        flattened_prohibited_with_subtypes = list(itertools.chain.from_iterable(prohibited_with_subtypes))
        return flattened_prohibited_with_subtypes


    @strict_types
    def individual_of_type(self, class_of_individual: Union[str, owlready2.Thing], name_for_individual: str = None, 
                           validate_domain_range: bool = None, **kwargs) -> owlready2.EntityClass:
        """Instantiates an individual of the class(type) specified.

        Wraps the default owlready2 functions with error handling and logging.
        Via the optional **kwargs one can also set properties, similar to description here:
        https://owlready2.readthedocs.io/en/v0.35/class.html#creating-individuals

        Example:
        edge_name = graph.add.individual_of_type(class_of_individual= "CausalEdge",
                                                 hasCause=node1,
                                                 hasEffect=node2,
                                                 comment= ["an optional comment"])

        :param class_of_individual: class of individual as name or object
        :type class_of_individual: str
        :param name_for_individual: name for individual, defaults to <class_name><no>
        :type name_for_individual: str, optional
        :param validate_domain_range: Switch to only allow creation of new individuals with valid domain and range for all properties, defaults to 'Graph.validate_domain_range'
        :type validate_domain_range: bool, optional
        :return: Entity Object (class/property/individual) of the created individual or 'None' if creation failed
        :rtype: owlready2.EntityClass
        """
        if validate_domain_range is None:
            validate_domain_range = self.validate_domain_range
        return owlutils.create_individual_of_type(class_of_individual=class_of_individual,
                                                  store=self.store,
                                                  name_for_individual=name_for_individual,
                                                  logger=self.logger,
                                                  validate_domain_range=validate_domain_range,
                                                  **kwargs)


    @strict_types
    def causal_node(self, individual_name: str = None, validate_domain_range: bool = None, **kwargs) -> owlready2.EntityClass:
        """Creates an individual of class "CausalNode" with the name 'individual_name'.
        If no name is given, the name is automatically generated from the Class name and a number.
        Via the optional **kwargs, arbitrary properties can be set, similar to description here:
        https://owlready2.readthedocs.io/en/v0.35/class.html#creating-individuals

        Example for adding a creator individual named 'supercreator':
        causal_node_name = add.causal_node(hasCreator=[creator_node], comment=["optional comment"])

        :param instance_name: desired name for individual, defaults to causalnode<no>
        :type instance_name: str, optional
        :param validate_domain_range: Switch to only allow creation of new individuals with valid domain and range for all properties, defaults to 'Graph.validate_domain_range'
        :type validate_domain_range: bool, optional
        :return: Entity Object of the created CausalNode or 'None' if no new CausalNode was created
        :rtype: owlready2.EntityClass
        """
        if validate_domain_range is None:
            validate_domain_range = self.validate_domain_range
        causal_node_object = owlutils.create_individual_of_type(class_of_individual= 'CausalNode',
                                                              store= self.store,
                                                              name_for_individual= individual_name,
                                                              logger= self.logger,
                                                              validate_domain_range=validate_domain_range,
                                                              **kwargs)
        self.store.save()
        return causal_node_object


    @strict_types
    def causal_edge(self, cause_node: Union[str, owlready2.Thing], effect_node: Union[str, owlready2.Thing], name_for_edge: str = None,
                    confidence: float = None, time_lag_s: float = None, force_create: bool = False, validate_domain_range: bool = None,
                    **kwargs) -> owlready2.EntityClass:
       
        """Adds a 'CausalEdge' between Nodes with names 'cause_node' and 'effect_node'.

        Via the optional **kwargs, arbitrary properties can be set, similar to description here:
        https://owlready2.readthedocs.io/en/v0.35/class.html#creating-individuals

        Example (equivalent):
        - edge_name= graph.add.causal_edge(cause_node= cause_node,
                                            effect_node = effect_node,
                                            confidence= 0.2,
                                            comment= ["an optional comment"])
        - edge_name2= graph.add.causal_edge(cause_node= cause_node,
                                            effect_node= effect_node,
                                            hasConfidence= 0.2,
                                            comment= ["an optional comment"])

        :param cause_node: A existing CausalNode object or the name of it. Describes the cause node.
        :type cause_node: Union[str, owlready2.Thing]
        :param effect_node: A existing CausalNode object or the name of it. Describes the effect node.
        :type effect_node: Union[str, owlready2.Thing]
        :param name_for_edge: optional name for the edge, defaults to None
        :type name_for_edge: str, optional
        :param confidence: confidence in the edge's existence, defaults to None
        :type confidence: float, optional
        :param time_lag_s: time lag between cause and effect in seconds, defaults to None
        :type time_lag_s: float, optional
        :param force_create: Enable force creation of missing cause/effect node with type
        'CausalNode', defaults to False
        :type force_create: bool, optional
        :param validate_domain_range: Switch to only allow creation of new individuals with valid domain and range for all properties, defaults to 'Graph.validate_domain_range'
        :type validate_domain_range: bool, optional
        :return: Entity Object of the created CausalEdge or 'None' if no new CausalEdge was created
        :rtype: owlready2.EntityClass
        """
        if validate_domain_range is None:
            validate_domain_range = self.validate_domain_range

        # Get names and objects of cause and effect node
        cause_node_name, cause_node_obj = owlutils.get_name_and_object(cause_node, self.store, True)
        effect_node_name, effect_node_obj = owlutils.get_name_and_object(effect_node, self.store, True)

        # If a Thing was passed, then check if it (still) exists
        if (cause_node_name is None and cause_node_obj is None):
            self.logger.error(f"The passed cause object '{cause_node}' does not exist.")
            return None
        elif (effect_node_name is None and effect_node_obj is None):
            self.logger.error(f"The passed effect object '{effect_node}' does not exist.")
            return None

        # Check if edge already exists
        edge_existing = owlutils.get_entity_by_name(name_for_edge, self.store, suppress_warn=True)
        if edge_existing is not None:
            self.logger.warning(f"Can't create CausalEdge {name_for_edge}. Name already taken.")
            return None
        # Check if both nodes exist, else: return None or force create node if specified
        for node_name in (cause_node_name, effect_node_name):
            if not owlutils.entity_exists(node_name, self.store):
                if force_create is False:
                    self.logger.error(f"Cannot create CausalEdge between {cause_node_name} --> " +
                                      f"{effect_node_name}. Node '{node_name}' can't be found.")
                    return None
                # Force create missing node with name 'node_name' of type 'CausalNode'
                # Only if option 'create_causal_node= True'
                self.logger.warning(f"Node '{node_name}' did not exist. Creating Node " +
                                    f"of type 'CausalNode' with name '{node_name}' now.")
                self.causal_node(node_name)
        # Check if Nodes have Type CausalNode, if not: Store to add CausalNode type
        # (only if NOT of a type which is excluded from drawing CausalEdges in between)
        nodes_that_need_causal_node_type_added = []
        for node_name in (cause_node_name, effect_node_name):
            if owlutils.is_instance_of_type(node_name, 'CausalNode', self.store, include_subtypes=True):
                pass
            else:
                # Check if class_type is part of types prohibited for new nodes:
                node = owlutils.get_entity_by_name(node_name, self.store)
                class_type = node.is_a
                if class_type not in self.classes_prohibited_from_causal_connections:
                    nodes_that_need_causal_node_type_added.append(node)
                else:
                    self.logger.warning(f"Node '{node_name}' can not be used as part of a " +
                                        f"'CausalEdge' since its class '{class_type} is " +
                                         "prohibited for CausalEdges.")
                    return None
        # Add the CausalNode Type if necessary:
        for node in nodes_that_need_causal_node_type_added:
            # Check if CausalNode is already within node types
            node_types = node.is_a
            causal_node_object = owlutils.get_entity_by_name("CausalNode", self.store)
            if causal_node_object not in node_types:
                # if yes: append
                self.logger.debug(f"Node '{node_name}' does not inherit from 'CausalNode' yet." +
                                   "Adding 'CausalNode' as further class.")
                node.is_a.append(owlutils.get_entity_by_name("CausalNode", self.store))
            else:
                # if not: don't append
                pass
        # Get Object representation of nodes
        cause_node = owlutils.get_entity_by_name(cause_node_name, self.store, logger=self.logger)
        effect_node = owlutils.get_entity_by_name(effect_node_name, self.store, logger=self.logger)
        # Add additional properties to edge, depending on inputs
        edge_properties_dict = dict(hasCause=cause_node, hasEffect=effect_node)
        if confidence is not None:
            if 0.0 <= confidence <= 1.0:
                edge_properties_dict['hasConfidence'] = confidence
            else:
                self.logger.error(f"Cannot create CausalEdge between {cause_node_name} --> " +
                                  f"{effect_node_name}. Specified confidence {confidence} " +
                                   "exceeds range [0,1]. ")
                return None
        if time_lag_s is not None:
            if time_lag_s >= 0.0:
                edge_properties_dict['hasTimeLag'] = time_lag_s
            else:
                self.logger.error(f"Cannot create CausalEdge between '{cause_node_name}--> " +
                                  f"{effect_node_name}. Specified time_lag_s {time_lag_s} " +
                                   "is negative.")
                return None
        # Create edge with objects
        if name_for_edge is not None:                    
            new_edge_object = owlutils.create_individual_of_type(
                class_of_individual="CausalEdge",
                store=self.store,
                name_for_individual=name_for_edge,
                logger=self.logger,
                validate_domain_range=validate_domain_range,
                **edge_properties_dict, **kwargs
            )
        else:
            new_edge_object = owlutils.create_individual_of_type(
                class_of_individual="CausalEdge",
                store=self.store,
                name_for_individual=None,
                logger=self.logger,
                validate_domain_range=validate_domain_range,
                **edge_properties_dict, **kwargs
            )
        if new_edge_object is not None:
            self.logger.info(f"Created CausalEdge between cause '{cause_node_name}' and effect " +
                            f"'{effect_node_name}'")
            self.store.save()
        else:
            self.logger.warning("Creation failed. No Edge added between cause" +
                                f"{cause_node_name} and effect {effect_node_name}")
        return new_edge_object
