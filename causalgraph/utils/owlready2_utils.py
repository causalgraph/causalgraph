#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains various helpful methods for owlready2"""

# general imports
import logging
from logging import Logger
import owlready2
# causalgraph imports
from causalgraph.store.edit import Edit
from causalgraph.utils.logging_utils import init_logger
# Global declaration of default utils_logger
utils_logger = init_logger("utils", console_handler_level=logging.WARNING)


def create_individual_of_type(class_of_individual: str, store: owlready2.World, name_for_individual: str=None,
                              logger: Logger = utils_logger, **kwargs) -> str:
    """Instantiates an individual of the class (type) specified.

    Wraps the default owlready2 functions with error handling and logging.
    Via the optional **kwargs one can also set properties, similar to description here:
    https://owlready2.readthedocs.io/en/v0.35/class.html#creating-individuals

    Example:
    my_connected_Edge = create_individual_of_type(class_of_individual= "CausalEdge",
                                                  hasCause = [store.my_cause],
                                                  hasEffect = [store.my_effect])

    :param class_of_individual: class name of individual
    :type class_of_individual: str
    :param store: Store in which to create the individual
    :type store: owlready2.World
    :param name_for_individual: name for individual, defaults to <class_name><no>
    :type name_for_individual: str, optional
    :param logger: Logger Object, defaults to utils_logger
    :type logger: Logger, optional
    :param logger: Logger Object, defaults to utils_logger
    :type logger: Logger, optional
    :return: final name of individual or 'None' if creation failed
    :rtype: str
    """
    # Extract owlready2.Ontology for storing individuals
    individuals_store_onto = store.individuals_onto
    # Check if the desired names for the classes and individual are valid
    if not (is_valid_class_type(class_of_individual, store, logger=logger) and
            is_valid_individual_name(name_for_individual, store, logger=logger)):
        return None
    # Check if properties (given as optional kwargs) are known and have valid target-objects
    for prop, target_objects in kwargs.items():
        valid = validate_property_target_pairs(prop, target_objects, store, logger=logger)
        if not valid:
            return None
    # Check if individual already exists
    possibly_existing_individual = get_entity_by_name(name_of_entity= name_for_individual,
                                                      store= store,
                                                      logger=logger,
                                                      suppress_warn=True)
    # Get Object for class_type, this is necessary to instantiate an individual from this class.
    class_def_for_individual = get_entity_by_name(name_of_entity= class_of_individual,
                                                  store= store,
                                                  logger=logger)
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
        return new_individual.name
    else:
        # Append properties if individual_already exists
        if not is_instance_of_class(name_for_individual, class_of_individual, store, logger=logger):
            logger.error(f"Can't create {name_for_individual}:{class_of_individual}." +
                            "Node with same name, but different type already exists:" +
                            f"{name_for_individual}:{str(possibly_existing_individual.is_a)}")
            return None
        elif len(kwargs) > 0:
            # Update individual properties
            success = update_properties_of_individual(individual_name=name_for_individual, store=store, prop_dict=kwargs)
            if success is True:
                logger.info(f"{class_of_individual} with name '{name_for_individual}' already " +
                            f"existed. Added / Overwrote properties {kwargs}")
                store.save()
                return name_for_individual
            return None
        else:
            logger.info(f"Individual already exists. Returning existing '{class_of_individual}' " +
                            f"with name '{name_for_individual}'.")
            store.save()
            return name_for_individual


def update_properties_of_individual(individual_name: str, store: owlready2.World, prop_dict: dict,
                                    logger: Logger = utils_logger) -> bool:
    """Updates the properties of an individual with the properties
       and values given in the dictionary.


    :param individual_name: Name of the individual
    :type individual_name: str
    :param store: Store in which to update the individual
    :type store: owlready2.World
    :param prop_dict: Dictionary containing properties and their new values
    :type prop_dict: dict
    :param logger: Logger Object, defaults to utils_logger
    :type logger: Logger, optional
    :return: True if update successful, else False
    :rtype: bool
    """
    # Get individual if it exists
    individual = get_entity_by_name(individual_name, store)
    if individual is None:
        return False
    indi_type = [type.name for type in individual.is_a][0]
    # Check if the updates are allowed
    for prop, val in prop_dict.items():
        # Check if the individual is allowed to have the given property
        prop_allowed = validate_prop_for_type(indi_type, prop, store, logger)
        if not prop_allowed:
            logger.warning(f'The property {prop} is not allowed for {individual}!')
            return False
        # Check if the value has the right data type for the property
        type_allowed = validate_data_type_for_property(prop, val, logger)
        if not type_allowed:
            logger.warning(f'Data type {type(val)} not allowed for property {prop}')
            return False
    # Update the properties as specified in the dictionary
    for prop, val in prop_dict.items():
        # Delete if the value is None
        if val is None:
            try: # For single values
                individual.__setattr__(prop, None)
            except ValueError: # For lists of individuals
                individual.__setattr__(prop, [])
            continue
        # Update lists of individuals
        if isinstance(val, list) and entity_exists(val[0], store):
            entity_list = [get_entity_by_name(i, store) for i in val]
            individual.__setattr__(prop, entity_list)
        else: # Update single values
            individual.__setattr__(prop, val)
    return True


def get_entity_by_name(name_of_entity: str, store: owlready2.World,
                       logger: Logger = utils_logger, suppress_warn=False) -> owlready2.EntityClass:
    """Returns entity (class/property/individual) found under given name.
    Returns none if no entity is found.

    :param name_of_entity: Name of the entity to search for
    :type name_of_entity: str
    :param store: Store in which to check for the entities existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to utils_logger
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


def get_subclasses(class_name: str, store: owlready2.World,
                   logger: Logger = utils_logger) -> list:
    """Generates a list of all the subclasses of a class, including the class
    itself in the list.

    :param class_name: Name of the class
    :type class_name: str
    :param store: Store
    :type store: owlready2.World
    :param logger: Logging handler, defaults to utils_logger
    :type logger: Logger, optional
    :return: List of all subclasses and the class itself, None if failure
    :rtype: list
    """
    # Determine IRI of class as base for SPARQL Query
    if entity_exists(class_name, store):
        class_iri = get_entity_by_name(class_name, store, suppress_warn=True).iri
        subclasses_list = list(store.sparql("""
            SELECT ?x
            { ?x rdfs:subClassOf* """ + f"<{class_iri}> ." + " }"
            ))
    else:
        logger.warning(f"Class '{class_name}' does not exist. Returning 'None' as subclasses.")
        return None
    return subclasses_list


def count_instances_of_type(typename: str, store: owlready2.World):
    """Returns the number of instances of type 'typename' in world

    :param typename: Typename to be counted
    :type typename: str
    :param store: Store in which the data is stored
    :type store: owlready2.World
    :return: Number of <typename> in <world>
    :rtype: int
    """
    type_iri = get_entity_by_name(typename, store, suppress_warn=True).iri
    num_of_type_instances = len(list(store.sparql("""
        SELECT ?x
        { ?x a """ + f"<{type_iri}>" + " . }")))
    return num_of_type_instances


def entity_exists(entity_name: str, store: owlready2.World) -> bool:
    """Indicates whether an entity (individual, class) exists or not.
    If you want to check the class as well, use 'is_instance_of_class'.

    :param entity_name: Name for individual
    :type entitiy_name: str
    :param store: Store
    :type store: owlready2.World
    :return: True if exists, False else
    :rtype: bool
    """
    possible_individual = get_entity_by_name(entity_name, store, suppress_warn=True)
    if possible_individual is None:
        return False
    else:
        return True

def is_instance_of_class(individual_name: str,  class_name: str, store: owlready2.World,
                         include_subtypes= False, logger: Logger = utils_logger) -> bool:
    """Checks if an instance with name 'individual_name' has type <class_name>

    :param individual_name: Name of individual
    :type individual_name: str
    :param class_name: Name of class (=type)
    :type class_name: str
    :param store: Store in which to check for class' existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to utils_logger
    :type logger: Logger, optional
    :return: True if instance with name in class exists
    :rtype: bool
    """
    possibly_existing_individual = get_entity_by_name(individual_name, store, logger=logger)
    if possibly_existing_individual is None:
        return False
    if include_subtypes is False:
        return class_name in str(possibly_existing_individual.is_a)
    if include_subtypes is True:
        # Check for each type of individual, if the type is part of a subtype
        # of the type to check (class_name)
        class_names_to_check = [node[0].name for node in get_subclasses(class_name, store, logger)]
        for class_type_of_individual in possibly_existing_individual.is_a:
            if class_type_of_individual.name in class_names_to_check:
                return True
        # Return False if not included in a subclass
        return False


def is_valid_class_type(class_to_check: str, store: owlready2.World, logger: Logger = utils_logger) -> bool:
    """Checks if the class_to_check is valid.
    The class is valid if an ontological description exists
    in the store and thus individuals can be created from it.

    :param class_to_check: Class Name
    :type class_to_check: str
    :param store: Store in which to check for class' existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to utils_logger
    :type logger: Logger, optional
    :return: if class_name_is_valid
    :rtype: bool
    """
    class_names = [owlclass.name for owlclass in store.classes()]
    if class_to_check not in class_names:
        logger.warning(f"No individual created. Class type unknown: {class_to_check}")
        return False
    return True


def is_valid_individual_name(individual_name: str, store: owlready2.World, logger: Logger = utils_logger) -> bool:
    """Checks if a proposed name for an individual is allowed.
    Prohibited are individual names identical to class names.

    :param individual_name: Individual name to check
    :type individual_name: str
    :param store: Store in which to check for classes' existence
    :type store: owlready2.World
    :param logger: Logger Object, defaults to utils_logger
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


def validate_property_target_pairs(prop_str: str, target, store: owlready2.World, logger: Logger = utils_logger) -> bool:
    """Checks if pair of property and target are valid.

    :param prop_str: Property to check
    :type prop_str: str
    :param target: list of target objects or single target for this property
    :type target: list or single value
    :param store: Store
    :type store: owlready2.World
    :param logger: logger, defaults to utils_logger
    :type logger: Logger, optional
    :return: True, if property_target is valid
    :rtype: bool
    """
    # Load available properties from ontologies and default annotation properties as defined here:
    # https://owlready2.readthedocs.io/en/latest/annotations.html
    available_properties = [prop.name for prop in store.properties()]
    default_properties = ["comment", "isDefinedBy", "label", "seeAlso", "backwardCompatibleWith",
                          "deprecated", "incompatibleWith", "priorVersion", "versionInfo"]
    # If part of default properties return true, otherwise check properly
    if prop_str in default_properties:
        return True
    # Check if valid property
    if prop_str not in available_properties:
        logger.warning(f"No individual created. Property unknown: '{prop_str}'. ")
        return False
    # Switch Case depending on target is a list or a single_value
    if type(target) == list:
        for onto_object in target:
            try:
                _ = get_entity_by_name(onto_object.name, store, logger=logger)
                return True
            except AttributeError:
                logger.warning(f"No individual created. Target-object for property {prop_str} " +
                               f"does not exist. Can't find individual '{onto_object}''.")
                return False
    # For Single Values
    else:
        _ = target
        return True
        # TODO Implement test, if correct data type for single_value
        # (e.g. for confidence that is float)


def get_range_of_property(store: owlready2.World, property_name: str) -> list:
    """Returns a list of Individual Class Types. This list contains all Class Types that are in range
    of the passed property_name.

    :param store: Owlready2 World/store
    :type store: owlready2.World
    :param property_name: Name of the property (e. g. isCausing)
    :type property_name: str
    :return: List of Objects that are in range of the passed property_name
    :rtype: list
    """
    props = list(store.properties())
    property = next((x for x in props if x.name == property_name), None)
    return property.range


def validate_prop_for_type(type_str: str, prop: str, store: owlready2.World, logger: Logger) ->bool:
    """Validates if the given type of individual (CausalNode/ CausalEdge/ Creator)
    is allowed to have the given property
    # TODO implement fully

    :param type_str: Type of class - either CausalNode/ CausalEdge or Creator
    :type type_str: str
    :param prop: Name of the property
    :type prop: str
    :param store: Current store
    :type store: owlready2.World
    :param logger: Logger
    :type logger: Logger
    :return: True if the property is allowed for the type else false
    :rtype: bool
    """
    # Check if the property exists
    default_props = ["comment", "isDefinedBy", "label", "seeAlso", "backwardCompatibleWith",
                     "deprecated", "incompatibleWith", "priorVersion", "versionInfo", 'type']
    available_props = [prop.name for prop in store.properties()]
    if prop not in default_props and prop not in available_props:
        logger.warning(f"The property {prop} is not valid. Please check its spelling!")
        return False
    # Case CausalNode
    node_classes = [subclass[0].name for subclass in get_subclasses("CausalNode", store)]
    if type_str in node_classes and prop in ['hasConfidence', 'hasTimeLag']:
        return False
    # Case Creator
    creator_classes = [subclass[0].name for subclass in get_subclasses('Creator', store)]
    if type_str in creator_classes and prop in ['hasConfidence', 'hasTimeLag']:
        return False
    # Return True if there were no violations
    return True


def validate_data_type_for_property(prop: str, val, logger: Logger) -> bool:
#    """Validates that the data type of the value is correct for the given property
#    e.g. hasTimeLag should be a float.
#
#    :param prop: The name of a property
#    :type prop: str
#    :param val: The value of the property
#    :type val: _type_
#    :param logger: Logger
#    :type logger: Logger
#    :return: True if data type is valid for the property. else False
#    :rtype: bool
#    """
    # NOTE: Check here that in a list of individuals all individuals exist,
    # otherwise nothing is updated.
    # Example: prop_dict = {'comment': 'New comment', 'hasCreator': ['Creator', 'ABC']}
    # (ABC is not a valid creator) Make sure that neither 'comment' nor 'hasCreator' are
    # updated since either everything is updated or nothing
    return True
    