#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Edit Class to edit things in the store.
Store is equivalent to owlready2 World """

# general imports
from logging import Logger
import owlready2
from typing import Union
# causalgraph imports
import causalgraph.utils.owlready2_utils as owlutils
from causalgraph.utils.misc_utils import strict_types
from causalgraph.utils.logging_utils import init_logger


class Edit():
    """ Contains all methods to edit resources in the store"""
    def __init__(self, store: owlready2.World, logger: Logger = None, validate_domain_range: bool = True) -> None:
        self.store = store
        self.validate_domain_range = validate_domain_range
        if logger is not None:
            self.logger = logger
        else:
            self.logger = init_logger("Edit")
        self.logger.info("Initialized the 'edit' functionalities.")


    @strict_types
    def rename_individual(self, old_name_obj: Union[str, owlready2.Thing], new_name: str) -> bool:
        """This method changes the name of an individual. To change it, pass the old name or the
        the individual it self as well as the new desired name. The return value is True if the
        change was successful, False if not.

        :param old_name_obj: The object of the individual to be changed or its name as str.
        :type old_name_obj: Union[str, owlready2.Thing],
        :param new_name: Desired new name of the individual
        :type new_name: str
        :return: True if renaming was successful, False if not.
        :rtype: bool
        """
        indi_old_name_name, ind_old_name_obj = owlutils.get_name_and_object(old_name_obj, self.store)

        # If a Thing was passed, then check if it (still) exists
        if ind_old_name_obj is None:
            self.logger.warning(f"Name change not successful because the individual '{indi_old_name_name}'" +
                                 " does not exist.")
            return False        
        # Check if new_name is already taken
        indi_new_name_obj = owlutils.get_entity_by_name(new_name, self.store, suppress_warn=True)
        if indi_new_name_obj is not None:
            self.logger.warning(f"Name change not successful because the new name '{new_name}'" +
                                 " is already taken.")
            return False
        # Renaming individuals and check success
        ind_old_name_obj.name = new_name
        # Success check not absolutely necessary, but in there for safety's sake.
        ind_old_name_obj = owlutils.get_entity_by_name(indi_old_name_name, self.store, suppress_warn=True)
        indi_new_name_obj = owlutils.get_entity_by_name(new_name, self.store, suppress_warn=True)
        self.store.save()
        if ind_old_name_obj is None and indi_new_name_obj is not None:
            self.logger.info(f"Renaming individual '{indi_old_name_name}' to '{new_name}' has been successful.")
            return True
        self.logger.warning(f"Something went wrong while renaming '{indi_old_name_name}' to '{new_name}'" +
                             " although the required name is not taken.")
        return False


    @strict_types
    def type_to_subtype(self, entity: Union[str, owlready2.Thing], new_type: Union[str, owlready2.EntityClass]) -> bool:
        """This method changes the type of an individual. Only subtypes are allowed as new types.
        To change the type, pass the name of the individual and the new desired (sub)type.
        The return value is True if the type change was successful, False if not or the new
        type is the same as the current one.

        :param entity: The individual object to be changed or its name.
        :type entity: Union[str, owlready2.Thing]
        :param new_type: The name of the new (sub)type or the owlready EntityClass object.
        :type new_type: Union[str, owlready2.EntityClass]
        :return: True if type change was successful, False if not or type didn't change
        :rtype: bool
        """
        individual_name, individual_obj = owlutils.get_name_and_object(entity, self.store)
        # Exit func if individual does not exist
        if individual_obj is None:
            self.logger.error(f"Changing subtype failed. Entity '{individual_name}' does not exist.")
            return False
        # Initiate empty lists for collecting types that should (not) be changed
        types_to_keep = []
        types_to_update = []

        # Get new subtype object and check if it exists
        new_subtype_name, new_subtype_obj = owlutils.get_name_and_object(new_type, self.store)
        if new_subtype_obj == None:
            self.logger.warning(f'Changing subtype failed. New subtype {new_type} does not ' +
                                 'exist in the Ontology.')
            return False
        # Check if subtype is valid for passed individual
        for current_type in individual_obj.is_a:
            current_type_subtypes = owlutils.get_subclasses(current_type, self.store)
            # If new type is a valid subtype of the old type: substitute old type, else: keep type
            if [new_subtype_obj] in current_type_subtypes:
                types_to_update.append(current_type)
            else:
                types_to_keep.append(current_type)
        # The list "types_to_update" will be empty if there is currently no type that is related to
        # "new_type" and therefore also not allowed to be specialized in the subtype "new_type"
        if types_to_update == []:
            self.logger.warning(f"None of the current types of '{individual_name}' is allowed to be" +
                                f"changed to the subtype {new_subtype_name}")
            return False
        # Generate list of new types from types_to_keep and new_subtype_obj
        new_types = types_to_keep
        new_types.append(new_subtype_obj)
        # Swap current types of individual with new ones
        individual_obj.is_a = new_types
        self.store.save()
        types_to_update_names = [i.name for i in types_to_update]
        self.logger.info(f'Changing type(s) { {*types_to_update_names} } to {new_subtype_name} successful.')
        return True


    @strict_types
    def properties(self, entity: Union[str, owlready2.Thing], prop_dict: dict) -> bool:
        """Updates the properties of an individual with the properties
           and values given in the dictionary.

        :param entity: The individual object to be changed or its name.
        :type entity: Union[str, owlready2.Thing]
        :param prop_dict: Dictionary containing properties and their new values
        :type prop_dict: dict
        :return: True if update successful, else False
        :rtype: bool
        """
        individual_name, _ = owlutils.get_name_and_object(entity, self.store)
        update_prop_result = owlutils.update_properties_of_individual(individual=individual_name,
                                                                      logger=self.logger,
                                                                      store=self.store,
                                                                      prop_dict=prop_dict,
                                                                      validate_domain_range=self.validate_domain_range)
        return update_prop_result


    @strict_types
    def property(self, entity: Union[str, owlready2.Thing], property: Union[str, owlready2.PropertyClass], value) -> bool:
        """Updates one property of an individual

        :param entity: The individual object to be changed or its name.
        :type entity: Union[str, owlready2.Thing]
        :param property: The property name or the owlready PropertyClass object.
        :type property: Union[str, owlready2.PropertyClass]
        :param value: New value of the property
        :type value: _type_
        :return: True if update successful, else False
        :rtype: bool
        """
        individual_name, _ = owlutils.get_name_and_object(entity, self.store)
        property_name, _ = owlutils.get_name_and_object(property, self.store)
        prop_dict = {property_name: value}
        return self.properties(individual_name, prop_dict)


    @strict_types
    def delete_property(self, entity: Union[str, owlready2.Thing], property: Union[str, owlready2.PropertyClass]) -> bool:
        """Deletes a property from an individual

        :param entity: The individual object to be changed or its name.
        :type entity: Union[str, owlready2.Thing]
        :param property_name: Property to be deleted, passed as name string or the owlready PropertyClass object.
        :type property_name: Union[str, owlready2.PropertyClass]
        :return: True if deletion successful, else False
        :rtype: bool
        """
        individual_name, _ = owlutils.get_name_and_object(entity, self.store)
        property_name, _ = owlutils.get_name_and_object(property, self.store)
        prop_dict = {property_name: None}
        return self.properties(individual_name, prop_dict)


    @strict_types
    def description(self, entity: Union[str, owlready2.Thing], new_comment: list) -> bool:
        """Sets/changes the description (comment) of an individual

        :param entity: The individual object to be changed or its name.
        :type entity: Union[str, owlready2.Thing]
        :param new_comment: New description as a list of strings
        :type new_comment: list
        :return: True if update successful, else False
        :rtype: bool
        """
        individual_name, _ = owlutils.get_name_and_object(entity, self.store)
        return self.property(individual_name, 'comment', new_comment)
        