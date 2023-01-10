#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Edit Class to edit things in the store.
Store is equivalent to owlready2 World """

# general imports
from logging import Logger
import owlready2
# causalgraph imports
import causalgraph.utils.owlready2_utils as owlutils
from causalgraph.utils.logging_utils import init_logger


class Edit():
    """ Contains all methods to edit resources in the store"""
    def __init__(self, store: owlready2.World, logger: Logger = None) -> None:
        self.store = store
        if logger is not None:
            self.logger = logger
        else:
            self.logger = init_logger("Edit")
        self.logger.info("Initialized the 'edit' functionalities.")


    def rename_individual(self, old_name: str, new_name: str) -> bool:
        """This method changes the name of an individual. To change it, pass the old name as
        well as the new desired name. The return value is True if the change was successful,
        False if not.

        :param old_name: Current name of the individual to be renamed.
        :type old_name: str
        :param new_name: Desired new name of the individual
        :type new_name: str
        :return: True if renaming was successful, False if not.
        :rtype: bool
        """
        # Return False if individual with old_name does not exist.
        indi_old_name = owlutils.get_entity_by_name(name_of_entity=old_name, store=self.store)
        if indi_old_name is None:
            self.logger.warning(f'Name change not successful because the individual {old_name}' +
                                 'does not exist.')
            return False
        # Check if new_name is already taken
        indi_new_name = owlutils.get_entity_by_name(new_name, self.store, suppress_warn=True)
        if indi_new_name is not None:
            self.logger.warning(f'Name change not successful because the new name {new_name}' +
                                 'is already taken.')
            return False
        # Renaming individuals and check success
        indi_old_name.name = new_name
        # Success check not absolutely necessary, but in there for safety's sake.
        indi_old_name = owlutils.get_entity_by_name(old_name, self.store, suppress_warn=True)
        indi_new_name = owlutils.get_entity_by_name(new_name, self.store, suppress_warn=True)
        self.store.save()
        if indi_old_name is None and indi_new_name is not None:
            self.logger.info(f'Renaming individual {old_name} to {new_name} has been successful.')
            return True
        self.logger.warning(f'Something went wrong while renaming {old_name} to {new_name}' +
                             'although the required name is not taken.')
        return False


    def type_to_subtype(self, name_of_entity: str, new_type: str) -> bool:
        """This method changes the type of an individual. Only subtypes are allowed as new types.
        To change the type, pass the name of the individual and the new desired (sub)type.
        The return value is True if the type change was successful, False if not or the new
        type is the same as the current one.

        :param name_of_entity: Name (IRI) of the individual to be changed.
        :type name_of_entity: str
        :param new_type: Name (IRI) of the desired type.
        :type new_type: str
        :return: True if type change was successful, False if not or type didn't change
        :rtype: bool
        """
        # Get individual and its current type(s) by node_name
        individual = owlutils.get_entity_by_name(name_of_entity=name_of_entity, store=self.store)
        # Initiate empty lists for collecting types that should (not) be changed
        types_to_keep = []
        types_to_update = []
        # Get new subtype object and check if it exists
        exists_check = owlutils.entity_exists(entity_name=new_type, store=self.store)
        if exists_check is False:
            self.logger.warning(f'Changing subtype failed. New subtype {new_type} does not ' +
                                 'exist in the Ontology.')
            return False
        # Check if new_subtype_object is related to current_subtype, if so it needs to be updated
        new_subtype_object = owlutils.get_entity_by_name(name_of_entity=new_type, store=self.store)
        for current_type in individual.is_a:
            current_type_subtypes = owlutils.get_subclasses(current_type.name, self.store)
            # If new type is a valid subtype of the old type: substitute old type, else: keep type
            if [new_subtype_object] in current_type_subtypes:
                types_to_update.append(current_type)
            else:
                types_to_keep.append(current_type)
        # The list "types_to_update" will be empty if there is currently no type that is related to
        # "new_type" and therefore also not allowed to be specialized in the subtype "new_type"
        if types_to_update == []:
            self.logger.warning(f'None of the current types of {name_of_entity} is allowed to be' +
                                 'changed to the subtype {new_type}')
            return False
        # Generate list of new types from types_to_keep and new_subtype_object
        new_types = types_to_keep
        new_types.append(new_subtype_object)
        # Swap current types of individual with new ones
        individual.is_a = new_types
        self.store.save()
        types_to_update_names = [i.name for i in types_to_update]
        self.logger.info(f'Changing type(s) { {*types_to_update_names} } to {new_type} successful.')
        return True


    def properties(self, individual_name: str, prop_dict: dict) -> bool:
        """Updates the properties of an individual with the properties
           and values given in the dictionary.

        :param individual_name: Name of the individual
        :type individual_name: str
        :param prop_dict: Dictionary containing properties and their new values
        :type prop_dict: dict
        :return: True if update successful, else False
        :rtype: bool
        """
        update_prop_result = owlutils.update_properties_of_individual(individual_name=individual_name, logger=self.logger, store=self.store, prop_dict=prop_dict)
        return update_prop_result


    def property(self, individual_name: str, property_name: str, value) -> bool:
        """Updates one property of an individual

        :param individual_name: Name of the individual
        :type individual_name: str
        :param property_name: Property to be updated
        :type property_name: str
        :param value: New value of the property
        :type value: _type_
        :return: True if update successful, else False
        :rtype: bool
        """
        prop_dict = {property_name: value}
        return self.properties(individual_name, prop_dict)


    def delete_property(self, individual_name: str, property_name: str) -> bool:
        """Deletes a property from an individual

        :param individual_name: Name of the individual
        :type individual_name: str
        :param property_name: Property to be deleted
        :type property_name: str
        :return: True if deletion successful, else False
        :rtype: bool
        """
        prop_dict = {property_name: None}
        return self.properties(individual_name, prop_dict)


    def description(self, individual_name: str, new_comment: list) -> bool:
        """Sets/changes the description (comment) of an individual

        :param individual_name: Name of the individual
        :type individual_name: str
        :param new_comment: New description as a list of strings
        :type new_comment: list
        :return: True if update successful, else False
        :rtype: bool
        """
        return self.property(individual_name, 'comment', new_comment)
        