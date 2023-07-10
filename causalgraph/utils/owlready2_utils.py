#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains various helpful methods for owlready2"""

# general imports
import logging
import re
from logging import Logger
from typing import Union, Any
import owlready2
from deprecated import deprecated

# causalgraph imports
from causalgraph.utils.logging_utils import init_logger

###################################################
#               GLOBALS                           #                        
###################################################
UTILS_LOGGER = init_logger("utils", console_handler_level=logging.WARNING)
DEFAULT_PROPERTIES = ["comment", "isDefinedBy", "label", "seeAlso", "backwardCompatibleWith",
                     "deprecated", "incompatibleWith", "priorVersion", "versionInfo", 'type']
# So far did not find a way on how to get the default properties from owlready2 https://owlready2.readthedocs.io/en/latest/annotations.html
##################################################


def create_individual_of_type(class_of_individual: Union[str, owlready2.Thing], store: owlready2.World, name_for_individual: str=None,
                              logger: Logger = UTILS_LOGGER, validate_domain_range: bool = True, **kwargs) -> owlready2.Thing:
    """Instantiates an individual of the class (type) specified.

    Wraps the default owlready2 functions with error handling and logging.
    Via the optional **kwargs one can also set properties, similar to description here:
    https://owlready2.readthedocs.io/en/v0.35/class.html#creating-individuals

    Example:
    my_connected_Edge = create_individual_of_type(class_of_individual= "CausalEdge",
                                                  hasCause = store.my_cause,
                                                  hasEffect = store.my_effect)

    :param class_of_individual: Class of individual as string or object
    :type class_of_individual: Union[str, owlready2.Thing]
    :param store: Store in which to create the individual
    :type store: owlready2.World
    :param name_for_individual: name for individual, defaults to <class_name><no>
    :type name_for_individual: str, optional
    :type logger: Logger, optional
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :param validate_domain_range: Switch to only allow creation of new individuals with valid domain and range for all properties, defaults to True
    :type validate_domain_range: bool, optional
    :return: Owlready Thing (class/property/individual) of the created individual or 'None' if creation failed
    :rtype: owlready2.Thing
    """
    class_of_individual, class_def_for_individual = get_name_and_object(class_of_individual, store)
    if class_def_for_individual is None:
        raise ValueError(f"Can not create individual'. Given class '{class_of_individual}' is unknown.")
    # Extract owlready2.Ontology for storing individuals
    individuals_store_onto = store.individuals_onto
    # Check if the desired names for the classes and individual are valid
    if not (is_valid_class_type(class_of_individual, store, logger=logger) and
            is_valid_individual_name(name_for_individual, store, logger=logger)):
        return None
    # Check if properties (given as optional kwargs) are known and have valid target-objects
    valid = validate_property_target_pairs_for_classes(class_of_individual, kwargs, store, logger=logger, validate_domain_range=validate_domain_range)
    if valid is False:
        return None
    #prop_target_pairs = {**kwargs}
    #valid = validate_property_target_pairs_for_classes()
    # Check if individual already exists
    possibly_existing_individual = get_entity_by_name(name_of_entity= name_for_individual,
                                                      store= store,
                                                      logger=logger,
                                                      suppress_warn=True)
    # If no individual existed before: Create fresh individual in 'individuals_store_onto'
    # according to 'class_def_for_individual'
    if possibly_existing_individual is None:
        if name_for_individual is None:
            new_individual = class_def_for_individual(namespace= individuals_store_onto, **kwargs)
        else:
            new_individual = class_def_for_individual(name_for_individual, namespace= individuals_store_onto, **kwargs)
        # Logging depending on additional properties or not
        if len(kwargs) > 0:
            logger.info(f"Created {class_of_individual} instance with name {new_individual.name} " +
                        f"and properties {kwargs}")
        else:
            logger.info(f"Created {class_of_individual} instance with name {new_individual.name}.")
        store.save()
        return new_individual
    else:  # If an individual already exists with the same name
        individual = possibly_existing_individual
        # If the individual already exists, but is of a different type, return None
        if not is_instance_of_type(individual, class_of_individual, store, logger=logger):
            logger.error(f"Can't create {name_for_individual}:{class_of_individual}." +
                            "Node with same name, but different type already exists:" +
                            f"{name_for_individual}:{str(possibly_existing_individual.is_a)}")
            return None
        # If individual is of correct type and new properties exist: Append properties
        if len(kwargs) > 0:
            # Update individual properties
            success = update_properties_of_individual(individual=individual, store=store, prop_dict=kwargs)
            if success is True:
                logger.info(f"{class_of_individual} with name '{name_for_individual}' already " +
                            f"existed. Added / Overwrote properties {kwargs}")
                store.save()
                return individual
            else:
                return None
        # If nothing needed to be changed. Return existing individual
        else:
            logger.info(f"Individual already exists. Returning existing '{class_of_individual}' " +
                            f"with name '{name_for_individual}'.")
            store.save()
            return individual


def update_properties_of_individual(individual: Union[str, owlready2.Thing], store: owlready2.World, prop_dict: dict,
                                    logger: Logger = UTILS_LOGGER, validate_domain_range: bool = True) -> bool:
    """Updates the properties of an individual with the properties
       and values given in the dictionary.


    :param individual: The individual object to be updated or its name.
    :type individual: Union[str, owlready2.Thing]
    :param store: Store in which to update the individual
    :type store: owlready2.World
    :param prop_dict: Dictionary containing properties and their new values
    :type prop_dict: dict
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :param validate_domain_range: Switch to only allow creation of new individuals with valid domain and range for all properties, defaults to True
    :type validate_domain_range: bool, optional
    :return: True if update successful, else False
    :rtype: bool
    """
    # Check if individual exists and get its name and object
    individual_name, individual_obj = get_name_and_object(individual, store)
    if individual_obj is None:
        logger.warning(f"Individual '{individual_name}' does not exist.")
        return False
    # Check if the updates are valid
    classes = individual_obj.is_a
    valid = validate_property_target_pairs_for_classes(classes, prop_dict, store, logger=logger, validate_domain_range=validate_domain_range)
    if valid is False:
        logger.error(f"Can not update individual '{individual_name}' with properties_dict: {prop_dict}. Property-Value pairs are not valid.")
        return False
    # Update the properties as specified in the dictionary
    for prop, val in prop_dict.items():
        # Delete if the value is None
        if val is None:
            try: # For single values
                individual_obj.__setattr__(prop, None)
            except ValueError: # For lists of individuals
                individual_obj.__setattr__(prop, [])
            continue
        # Update lists of individuals
        if isinstance(val, list) and entity_exists(val[0], store):
            entity_list = [get_entity_by_name(i, store) for i in val]
            individual_obj.__setattr__(prop, entity_list)
        else: # Update single values
            individual_obj.__setattr__(prop, val)
    return True


def get_name_and_object(entity: Union[str, owlready2.Thing], store: owlready2.World, suppress_warn=False,
                        logger: Logger = UTILS_LOGGER) -> tuple:
    """Retrieve the name and corresponding object from the provided entity. The passed entity
    could be the owlready2 entity object or its name as string. 

    :param entity: The string or owlready entity
    :type entity: Union[str, owlready2.Thing]
    :param store: The Owlready2 World instance.
    :type store: owlready2.World
    :param suppress_warn: Switch, to surpress logs, defaults to False
    :type suppress_warn: bool, optional
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: A tuple containing the name and object associated with the entity.
    :rtype: tuple
    """
    name = None
    object = None
    # If entity is a string, get the object from the store
    if isinstance(entity, str):
        name = entity
        object = get_entity_by_name(name_of_entity=name, store=store, logger=logger, suppress_warn=suppress_warn)
    # If entity is not a string, check if it has a .name attribute and then try to get the object from the store
    elif hasattr(entity, 'name'):
        name = entity.name
        object = get_entity_by_name(name_of_entity=name, store=store, logger=logger, suppress_warn=suppress_warn)
    # Return resulting name and object or default to (None,None) if no case is matched
    return name, object


def get_entity_by_name(name_of_entity: str, store: owlready2.World,
                       logger: Logger = UTILS_LOGGER, suppress_warn=False) -> owlready2.EntityClass:
    """Returns entity (class/property/individual) found under given name.
    Returns none if no entity is found.

    :param name_of_entity: Name of the entity to search for
    :type name_of_entity: str
    :param store: Store in which to check for the entities existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :param suppress_warn: Switch, to surpress logs, defaults to False
    :type suppress_warn: bool, optional
    :raises ValueError: If unexpectedly found more than one possible entity
    :return: Entity Object (class/property/individual)
    :rtype: owlready2.EntityClass
    """
    possible_objects = store.search(iri=f"*#{name_of_entity}")
    if len(possible_objects) == 0:
        if not suppress_warn:
            logger.warning(f"""No entity (class/property/individual) found under given name.
                               Searched for {name_of_entity}""")
        return None
    elif len(possible_objects) > 1:
        error_msg = f"""More than one entity (class/property/individual) found under given name.
                        Searched for {name_of_entity} and got {possible_objects}"""
        logger.exception(error_msg)
        raise ValueError(error_msg)
    else:
        return possible_objects[0]


def get_all_causalnodes(store: owlready2.World) -> list:
    """Returns a list of CausalNode individuals and their subclasses
    for all CausalNodes of a given graph world.

    :param store: Store in which the data is stored
    :type store: owlready2.World
    :return: List of all CausalNode individuals and their subclasses
    from the given graph world.
    :rtype: list
    """
    # SPARQL Query to get all CausalNodes and their SubClasses
    causal_node_iri = get_entity_by_name("CausalNode", store, suppress_warn=True).iri
    nodes_and_subclasses = list(store.sparql("""
        SELECT ?x
        { ?x a [rdfs:subClassOf* """ + f"<{causal_node_iri}>]" + " .}"
    ))
    return nodes_and_subclasses


def get_all_causaledges(store: owlready2.World) -> list:
    """Returns a list of CausalEdge individuals and their subclasses for all
    CausalEdges of a given graph world.

    :param store: Store in which the data is stored
    :type store: owlready2.World
    :return: List of all CausalEdge individuals and their subclasses from
    the given graph world.
    :rtype: list
    """
    # SPARQL Query to get all CausalEdges and their SubClasses
    causal_edge_iri = get_entity_by_name("CausalEdge", store, suppress_warn=True).iri
    edges_and_subclasses = list(store.sparql("""
        SELECT ?x
        { ?x a [rdfs:subClassOf* """ + f"<{causal_edge_iri}>]" + " .}"
    ))
    return edges_and_subclasses


def get_subclasses(type: Union[str, owlready2.Thing], store: owlready2.World,
                   logger: Logger = UTILS_LOGGER) -> list:
    """Generates a list of all the subclasses of a class, including the class
    itself in the list.

    :param type: Name or object of the type / class to get the subclasses of
    :type type: Union[str, owlready2.Thing]
    :param store: Store
    :type store: owlready2.World
    :param logger: Logging handler, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: List of all subclasses and the class itself, None if failure
    :rtype: list
    """
    # Determine IRI of class as base for SPARQL Query
    class_name, class_obj = get_name_and_object(type, store, logger=logger)
    if class_obj is None:
        logger.warning(f"Class '{class_name}' does not exist. Returning 'None' as subclasses.")
        return None
    else:
        subclasses_list = list(store.sparql("""
            SELECT ?x
            { ?x rdfs:subClassOf* """ + f"<{class_obj.iri}> ." + " }"
            ))
    return subclasses_list


def count_instances_of_type(type: Union[str, owlready2.Thing], store: owlready2.World, include_subtypes=False):
    """Returns the number of instances of type 'typename' in world. 
    Optional kwarg 'include_subtypes' allows to also incloud insance of subtypes of typename in count. 

    :param typename: Name or object of the type / class to be counted
    :type typename: Union[str, owlready2.Thing]
    :param store: Store in which the data is stored
    :type store: owlready2.World
    :param include_subtypes: Switch to also include subtypes of typename in count, defaults to False
    :type include_subtypes: bool
    :return: Number of <typename> in <world>
    :rtype: int
    """
    typename, type_obj = get_name_and_object(type, store)
    # Use Path expressions to include subtypes
    if include_subtypes== True:
        num_of_type_instances = len(list(store.sparql("""
            SELECT ?x
            { ?x a/rdfs:subClassOf* """ + f"<{type_obj.iri}>" + " . }")))
    else:
        num_of_type_instances = len(list(store.sparql("""
            SELECT ?x
            { ?x a """ + f"<{type_obj.iri}>" + " . }")))
    return num_of_type_instances


def entity_exists(entity: Union[str, owlready2.Thing], store: owlready2.World) -> bool:
    """Indicates whether an entity (individual, class) exists or not.
    If you want to check the class as well, use 'is_instance_of_type'.

    :param entity: Individual or its name
    :type entity: Union[str, owlready2.Thing]
    :param store: Store
    :type store: owlready2.World
    :return: True if exists, False else
    :rtype: bool
    """
    try:
        var_to_check = entity.name
    except AttributeError:
        var_to_check = entity
    possible_individual = get_entity_by_name(var_to_check, store, suppress_warn=True)
    if possible_individual is None:
        return False
    else:
        return True

@deprecated(version='0.1.0', reason="Function was renamed and improved. USE 'is_instance_of_type' INSTEAD.")
def is_instance_of_class(individual: Union[str, owlready2.Thing],  type: Union[str, owlready2.EntityClass], store: owlready2.World,
                         include_subtypes= False, logger: Logger = UTILS_LOGGER) -> bool:
    """Deprecated since causalgraph 0.1.0, use 'is_instance_of_type' instead.
    Checks if an instance 'individual' has type <type>

    :param individual: Individual object or its name
    :type individual: Union[str, owlready2.Thing]
    :param type: Name or object of type / (=class)
    :type type Union[str, owlready2.EntityClass]
    :param store: Store in which to check for class' existence
    :type store: owlready2.World
    :param include_subtypes: Switch to also include subtypes of typename in check, defaults to False
    :type include_subtypes: bool
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: True if instance with name in class exists
    :rtype: bool
    """
    return is_instance_of_type(individual, type, store, include_subtypes, logger)


def is_instance_of_type(individual: Union[str, owlready2.Thing],  type: Union[str, owlready2.EntityClass], store: owlready2.World,
                         include_subtypes= False, logger: Logger = UTILS_LOGGER) -> bool:
    """Checks if an instance 'individual' has type <type>

    :param individual: Individual object or its name
    :type individual: Union[str, owlready2.Thing]
    :param type: Name or object of type / (=class)
    :type type Union[str, owlready2.EntityClass]
    :param store: Store in which to check for class' existence
    :type store: owlready2.World
    :param include_subtypes: Switch to also include subtypes of typename in check, defaults to False
    :type include_subtypes: bool
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: True if instance with name in class exists
    :rtype: bool
    """
    # Check if individual and type exists
    individual_name, individual_obj = get_name_and_object(individual, store, logger=logger)
    type_name, type_obj = get_name_and_object(type, store, logger=logger)
    if individual_obj is None:
        logger.warning(f"Individual '{individual_name}' does not exist.")
        return False
    # Give answer directly, if subtypes should not be included
    if include_subtypes is False:
        try:
            return type_name in str(individual_obj.is_a)
        except TypeError:
            return False
    # Handling subtypes
    if include_subtypes is True:
        # Check for each type of individual, if the type is part of a subtype
        # of the type to check (class_name)
        for individual_class in individual_obj.is_a:
            if is_subclass_of(individual_class, type_obj, store, logger=logger) == True:
                return True
        # Return False if not included in a subclass
        return False

def is_subclass_of(potential_subclass: Union[str, owlready2.Thing],  parent_class: Union[str, owlready2.EntityClass], store: owlready2.World,
                   logger: Logger = UTILS_LOGGER, suppress_warn = False) -> bool:
    """Checks if an class 'potential_subclass' is subclass of 'parent_class'

    :param potential_subclass: Class object or its name to check if subclass of parentclass
    :type potential_subclass: Union[str, owlready2.Thing]
    :param parent_class: Potential parent class object or its name
    :type parent_class: Union[str, owlready2.Thing]
    :param store: Store in which to check for class' existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: True if instance with name in class exists
    :rtype: bool
    """
    # Check if individual and type exists
    potential_subclass_name, potential_subclass_obj = get_name_and_object(potential_subclass, store, logger=logger, suppress_warn=True)
    parent_class_name, parent_class_obj = get_name_and_object(parent_class, store, logger=logger, suppress_warn=True)
    if potential_subclass_obj is None or parent_class_obj is None:
        if suppress_warn is False:
            logger.warning(f"Did not find class '{potential_subclass_name}' or '{parent_class_name}'.")
        return False
    # Check if potential_subclass is subclass of parent_class
    class_names_to_check = [node[0].name for node in get_subclasses(parent_class, store, logger)]
    if potential_subclass_name in class_names_to_check:
        return True
    else:
        logger.debug(f"Did not find class '{potential_subclass_name}' in subclasses of '{parent_class_name}'(subclasses={class_names_to_check})'.")
        return False

def is_valid_class_type(class_to_check: str, store: owlready2.World, logger: Logger = UTILS_LOGGER) -> bool:
    """Checks if the class_to_check is valid.
    The class is valid if an ontological description exists
    in the store and thus individuals can be created from it.

    :param class_to_check: Class Name
    :type class_to_check: str
    :param store: Store in which to check for class' existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: if class_name_is_valid
    :rtype: bool
    """
    class_names = [owlclass.name for owlclass in store.classes()]
    if class_to_check not in class_names:
        logger.warning(f"No individual created. Class type unknown: {class_to_check}")
        return False
    return True

def is_valid_individual_name(individual_name: str, store: owlready2.World, logger: Logger = UTILS_LOGGER) -> bool:
    """Checks if a proposed name for an individual is allowed.
    Prohibited are individual names identical to class names.

    :param individual_name: Individual name to check
    :type individual_name: str
    :param store: Store in which to check for classes' existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: True if individual_name is valid
    :rtype: bool
    """
    class_names = [owlclass.name for owlclass in store.classes()]
    if individual_name in class_names:
        logger.warning("No individual created. Prohibited to choose individual name identical to" +
                      f" class name. Choose different name from type '{individual_name}'")
        return False
    return True

def validate_property_target_pairs_for_classes(owl_class: Union[str, owlready2.Thing, list[Union[str, owlready2.Thing]]], 
                                            prop_target_pairs: dict[Union[str, owlready2.Thing], Union[str, owlready2.Thing]], 
                                            store: owlready2.World, logger: Logger = UTILS_LOGGER,
                                            validate_domain_range: bool = True) -> bool:

    logger.debug(f"Validating property target pairs for class '{owl_class}' of type {type(owl_class)} and properties '{prop_target_pairs}'")
    # 0) Check inputs and extract potentially multiple class definitons. Will return true if any of the classes are valid for the property target pair 
    if type(owl_class) in [list, owlready2.util.CallbackList]:
        classes = [get_name_and_object(cl, store, logger=logger, suppress_warn=False)[1] for cl in owl_class]
    else:
        classes = [get_name_and_object(owl_class, store, logger=logger, suppress_warn=False)[1]]
    # If any class can not be found return warning
    if None in classes:
        logger.warning(f"Could not validate property target pairs for class '{owl_class}'. Some class unknown in '{classes}'. ")
        return False
    # Ensure that prop_target_pairs is not empty 
    if len(prop_target_pairs) == 0:
        return True
    #### Loop over all property target pairs  
    for property, target in prop_target_pairs.items():
        # 1) Detect default properties and pass (=are not validated)
        if property in DEFAULT_PROPERTIES:
            logger.debug(f"Skipping validation for default property: '{property}'")
            continue
        # 2) Try to get property to check if it exists
        prop_str, prop = get_name_and_object(property, store, logger=logger, suppress_warn=True)
        if prop is None:
            logger.warning(f"Could not validate property target pairs. Property unknown: '{prop_str}'. ")
            return False
        if validate_domain_range is True:
            # 3) Check domain of property
            domain_valid = _validate_any_class_in_domain_of_prop(classes, prop, store, logger=logger)
            if domain_valid is False:
                logger.warning(f"Property Target-Pairs invalid. Classes '{classes}' not in domain of Property '{prop_str}'.")
                return False
            # 4) Check if target is in range of property
            range_valid = _validate_target_in_range_of_prop(target, property, store, logger=logger)
            if range_valid is False:
                logger.warning(f"Property Target-Pairs invalid. Targets '{target}' not in range of Property '{prop_str}'.")
                return False
    # 5) Return True if all validations passed
    return True

def _validate_any_class_in_domain_of_prop(classes: list[Union[str, owlready2.Thing]], 
                                          prop: Union[str, owlready2.Thing], 
                                          store: owlready2.World, logger: Logger = UTILS_LOGGER) -> bool:

    # 1) Check if property is a property and if is default property
    if validate_if_entity_is_property(prop, store, logger=logger) is False:
        logger.warning(f"Could not validate domain of property. Given 'property' is not a property: '{prop}'. ")
        return False
    if prop in DEFAULT_PROPERTIES:
        logger.debug(f"Skipping validation for default property: '{prop}'")
        return True
    # 2) Get property and domain
    prop_str, prop = get_name_and_object(prop, store, logger=logger, suppress_warn=True)
    if prop is None:
        logger.warning(f"Could not validate property target pairs. Property unknown: '{prop_str}'. ")
        return False
    # 2) Skip validation if no domain is specified
    domain = prop.domain
    if domain == []:
        return True
    # 3) Validate Domain - Works only for imported classes
    elif len(domain) > 0:
        for owl_class in classes:
            for domain_class in domain:
                if is_subclass_of(owl_class, domain_class, store, logger=logger, suppress_warn=True) == True:
                    return True
                else:
                    prefixes_to_skip = ["owl", "rdf", "rdfs", "xml", "xsd"]
                    if any(str(domain_class).startswith(prefix) for prefix in prefixes_to_skip):
                        return True
        # Return false if no match was found
        logger.warning(f"Property '{prop_str}' has domain '{domain}' specified, but none of the classes '{classes}' are in the domain.")
        return False

def _validate_target_in_range_of_prop(target: Union[str, owlready2.Thing], prop: Union[str, owlready2.Thing],
                                      store: owlready2.World, logger: Logger = UTILS_LOGGER) -> bool:
    # 0) Get property and check
    prop_str, prop = get_name_and_object(prop, store, logger=logger, suppress_warn=True)
    if prop is None:
        raise ValueError(f"Could not validate property target pairs. Property not found: '{prop_str}'. ")
    # 1) Validate Property (is property and not default property) and 
    if validate_if_entity_is_property(prop, store, logger=logger) is False:
        logger.warning(f"Could not validate range of property. Given 'property':'{prop}' is not a property. ")
        return False
    if prop in DEFAULT_PROPERTIES:
        logger.debug(f"Skipping validation of range for default property: '{prop}'")
        return True
    # 2) if target is None -> return True (None is valid for all properties and used to "unassign a property"
    if target is None:
        logger.debug(f"Skipping validation of range for property '{prop}'. Target is 'None'.")
        return True
    # 3) get property type ('DataProperty', 'ObjectProperty') and if functional`(True/False)`
    prop_type, is_functional = _determine_prop_type_and_if_functional(prop, store, logger=logger)
    # 4) Validate ObjectProperty -> Target Object should exist and be in Range
    if prop_type == 'ObjectProperty':
        if is_functional is True:
            if type(target) == list:
                logger.warning(f"Target '{target}' was given in a list, but property '{prop_str}' is functional. Only single target allowed.")
                return False
            else:
                return _validate_targets_in_object_property_range(target, prop, store, logger=logger)
        elif is_functional is False: # Target should already be a list, as expected from _targets_in_object_property_range
            if type(target) != list:
                logger.warning(f"Single Target '{target}' was given, but property '{prop_str}' is functional and expects a list of targets. Passs as [target].")
                return False
            else:
                return _validate_targets_in_object_property_range(target, prop, store, logger=logger)
    # 5) Validate DataProperty -> Target should be of correct datatype and satisfy constraints
    elif prop_type == 'DataProperty':
        if is_functional is True:
            if type(target) == list:
                logger.warning(f"Target '{target}' was given in a list, but property '{prop_str}' is functional. Only single target allowed.")
                return False
            else:
                return _validate_targets_in_data_property_range(target, prop, store, logger=logger)
        elif is_functional is False: # Target should already be a list, as expected from _targets_in_object_property_range
            if type(target) != list:
                logger.warning(f"Single Target '{target}' was given, but property '{prop_str}' is functional and expects a list of targets. Passs as [target].")
                return False
            else:
                return _validate_targets_in_data_property_range(target, prop, store, logger=logger)
    else:
        raise RuntimeError(f"Could not validate range of property. Got unexpected result from '_determine_prop_type_and_if_functional': ({prop_type}, {is_functional})") 
    # 6) Return True if all validations passed
    return True

def _validate_targets_in_object_property_range(targets: Union[str, owlready2.Thing, list[Union[str, owlready2.Thing]]], prop: Union[str, owlready2.Thing],
                                                store: owlready2.World, logger: Logger = UTILS_LOGGER) -> bool:
    # 0) Assert that type of targets is list / otherwise convert to list (allow same handling for functional and non functional properties)
    if type(targets) != list:
        targets = [targets]
    # 1) Get property and check
    prop_str, prop = get_name_and_object(prop, store, logger=logger, suppress_warn=True)
    if prop is None:
        raise ValueError(f"Could not validate range of ObjectProperty. Property unknown: '{prop_str}'. ")
    # 2) For target in targets check if target exists and type is in range
    range = prop.range
    for target in targets:
        # 2.1) Check if target exists
        if entity_exists(target, store) is False:
            logger.warning(f"Target '{target}'  not valid for ObjectProperty '{prop_str}'. Target does not exist.")
            return False
        # 2.2) Check if target is in range
        if range == []:
            continue
        elif len(range) > 0:
            for range_type in range:
                if is_instance_of_type(target, range_type, store, include_subtypes=True, logger=logger):
                    continue
                else:
                    logger.warning(f"Target '{target}' of type '{type(target)}' not valid for ObjectProperty '{prop_str}'. TargetType is not in range '{range}'.")
                    return False
        else:
            raise RuntimeError(f"Could not validate range of property. Got unexpected result from 'prop.range': {range}. Expected list of length > 0.")
    # 3) Return True only if all validations passed
    return True
    
def _validate_targets_in_data_property_range(targets: Union[str, owlready2.Thing, list[Union[str, owlready2.Thing]]], prop: Union[str, owlready2.Thing],
                                             store: owlready2.World, logger: Logger = UTILS_LOGGER) -> bool:
    # 0) Assert that type of targets is list / otherwise convert to list (allow same handling for functional and non functional properties)
    if type(targets) != list:
        targets = [targets]
    # 1) Get property and check
    prop_str, prop = get_name_and_object(prop, store, logger=logger, suppress_warn=True)
    if prop is None:
        raise ValueError(f"Could not validate range of DataProperty. Property unknown: '{prop_str}'.")
    # 2) Pass if no range is specified and extract allowed datatypes and constraints if present
    range = prop.range 
    if range == []:
        return True
    elif len(range) > 0:
        # Get Types and constraints if present 
        constraints = [ele for ele in range if type(ele) == owlready2.ConstrainedDatatype]
        allowed_datatypes = [ele for ele in range if type(ele) != owlready2.ConstrainedDatatype]
    # 3) Validate that each target is of allowed datatype and satisfies constraints
    for target in targets:
        # If no constraints present: Check if datatype correct, if constraints present: Also check if datatype constraints are satisfied
        if len(constraints) == 0:
            if type(target) not in allowed_datatypes:
                logger.warning(f"Target '{target}' of type '{type(target)}' not valid for DataProperty '{prop_str}'. Target is not in allowed datatypes: {allowed_datatypes}.")
                return False
        elif len(constraints) >= 1:
            validation_result = _validate_constraints_for_literal(target, constraints, logger=logger)
            if validation_result is False:
                return False
        else:
            raise RuntimeError(f"Could not validate DataTypeConstraints. Got unexpected number of Constraints (>1): {constraints}.")
    # 4) Return True only if all validations passed
    return True

def _validate_constraints_for_literal(literal: Any, constraints: Union[list[owlready2.ConstrainedDatatype], owlready2.ConstrainedDatatype],
                                     logger: Logger = UTILS_LOGGER) -> bool:
    # Call _validate_single_constraint_for_literal for each constraint in constraints
    if type(constraints) != list:
        constraints = [constraints]
    # Get validation results for each constraint
    validation_results = []
    violations = [] 
    for constraint in constraints:
        single_result, single_violations_list = _validate_single_constraint_for_literal(literal, constraint, logger=logger, suppress_warn=True)
        validation_results.append(single_result)
        violations.extend(single_violations_list)
    # If any constraint set of datatype + restrictions is met: return True, otherwise False
    if True in validation_results:
        return True
    else:
        violations = ';'.join(violations)
        logger.warning(f"Constraint Validation(s) failed with: {violations}.")
        return False

def _validate_single_constraint_for_literal(literal: Any, constraint: owlready2.ConstrainedDatatype,
                                            logger: Logger = UTILS_LOGGER, suppress_warn: bool =False) -> tuple[bool, list[str]]:
    """Validates if the given literal is valid for the given constraint.

    :param literal: Any literal (e.g. string, int, float)
    :type literal: Any
    :param constraint: The Constraint to evaluate against
    :type constraint: owlready2.ConstrainedDatatype
    :param logger: logger, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :param suppress_warn: Switch to suppress logging of warnings, defaults to False
    :type suppress_warn: bool, optional
    :raises NotImplementedError: For WhiteSpaces Constraint, as unclear what is evaluated
    :return: True if all constraints are fulfilled, False otherwise
    :rtype: bool
    """
    validation_bool = True # Set to False if any constraint is violated
    violations_list = [] # List of violated constraints (new messages are appended)
    # 1) Check if base data type is fulfilled -> if not fulfilled immediately return False
    if type(literal) != constraint.base_datatype:
        violations_list.append(f"Value '{literal}' of type '{type(literal)}' not of correct base datatype, as specified by ConstrainedDatatype '{constraint}'.")
        validation_bool = False
    else:
        # 2) If base data type is correct: Check for all constraints if they are fulfilled
        if hasattr(constraint, "length"):
            if len(literal) != constraint.length:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'length' Constraint: '{constraint}'")
                validation_bool = False 
        if hasattr(constraint, "min_length"):
            if len(literal) < constraint.min_length:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'min_length' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "max_length"):
            if len(literal) > constraint.max_length:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'max_length' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "pattern"):
            if re.match(constraint.pattern, literal) is None:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'pattern' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "white_space"):
            raise NotImplementedError(f"Constraint 'white_space' not implemented yet. Constraint: '{constraint}'")
        if hasattr(constraint, "max_inclusive"):
            if literal > constraint.max_inclusive:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'max_inclusive' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "max_exclusive"):
            if literal >= constraint.max_exclusive:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'max_exclusive' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "min_inclusive"):
            if literal < constraint.min_inclusive:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'min_inclusive' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "min_exclusive"):
            if literal <= constraint.min_exclusive:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'min_exclusive' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "total_digits"):
            if len(str(literal).replace('.', '')) != constraint.total_digits:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'total_digits' Constraint: '{constraint}'")
                validation_bool = False
        if hasattr(constraint, "fraction_digits"):
            if len(str(literal).split('.')[1]) != constraint.fraction_digits:
                violations_list.append(f"Value '{literal}' of type '{type(literal)}' violates 'fraction_digits' Constraint: '{constraint}'")
                validation_bool = False
    # Logging
    if validation_bool is False and suppress_warn is False:
        violations = ';'.join(violations_list)
        logger.warning(f"Constraint Validation(s) failed with: {violations}.")
    # Return True if all constraints are fulfilled
    return validation_bool, violations_list


def validate_if_entity_is_property(entity: Union[str, owlready2.Thing],
                                store: owlready2.World, logger: Logger = UTILS_LOGGER) -> bool:
    """Validates if a given entity is a property

    :param entity: Entity to check
    :type entity: Union[str, owlready2.Thing]
    :param store: Store
    :type store: owlready2.World
    :param logger: logger, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :return: True, if entity is property, False Else
    :rtype: bool
    """
    # Handling for default properties
    if entity in DEFAULT_PROPERTIES:
        return True
    # Handling for other properties
    prop_str, prop_obj = get_name_and_object(entity, store, logger=logger, suppress_warn=True)
    if prop_obj is None:
        logger.warning(f"Could not validate if entity is property. Entity unknown: '{entity}'. ")
        return False
    if prop_str in [prop.name for prop in store.properties()]:
        return True
    else:
        logger.debug(f"Entity '{prop_str}' is not a property. Is of type '{type(prop_obj)}'.")
        return False

def _determine_prop_type_and_if_functional(property: Union[str, owlready2.Thing], store: owlready2.World, logger: Logger = UTILS_LOGGER) -> tuple[str, bool]:
    """Determines if the property is a 'ObjectProperty' or 'DataProperty' and if it is functional (=can be applied only once to each subject).
    Also checks if the passed argument 'property' exists and is a property. Raises ValueError if not.

    :param property: name or object of property to check
    :type property: Union[str, owlready2.Thing]
    :param store: cg.store
    :type store: owlready2.World
    :param logger: logger, defaults to UTILS_LOGGER
    :type logger: Logger, optional
    :raises ValueError: Can't be found or it is undeterminable if ObjectProperty or DataProperty
    :return: Tuple('PropertyType':str, functional:bool), PropertyTypes: 'ObjectProperty' or 'DataProperty' 
    :rtype: tuple(str, bool)
    """
    
    prop_str, prop = get_name_and_object(property, store)
    # Only proceed if the property is of type property
    if prop is None:
        if property in DEFAULT_PROPERTIES:
            logger.debug(f"Can't determine prop type or if functional for default property: '{property}'. Returning (None, None)")
            return None, None
        else:
            raise ValueError(f"'{property}' could not be found.")
    # Assert Property Type
    if prop in list(store.object_properties()):
        result_type = "ObjectProperty"
    elif prop in list(store.data_properties()):
        result_type = "DataProperty"
    else:
        raise ValueError(f"'{property}' of type '{type(property)}' is neither an ObjectProperty nor a DataProperty.")
    # Determine if functional or not
    if prop.is_functional_for("this argument here does not seem to matter in owlready2"):
        result_functional = True
    else:
        result_functional = False
    return result_type, result_functional
