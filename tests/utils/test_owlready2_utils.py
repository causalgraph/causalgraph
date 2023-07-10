#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/utils/owlready2_utils.py
"""

# general imports
import pytest
import owlready2
import os
from pathlib import Path
# causalgraph imports
from causalgraph import Graph
import causalgraph.utils.owlready2_utils as owlutils


########################################
###         Fixtures                 ###
########################################
# Temporary sql_db and Graph for every test
@pytest.fixture(name="sql_test_db_path")
def fixture_sql_test_db_path(tmpdir) -> str:
    test_db_relative_path = os.path.join(tmpdir, "test_readwrite.sqlite3")
    yield test_db_relative_path
    os.remove(test_db_relative_path)

@pytest.fixture(name="G")
def fixture_G(sql_test_db_path: str) -> Graph:
    return Graph(sql_db_filename=sql_test_db_path)

# Create Graph with access to validation-test-onto to test validation functions
@pytest.fixture(name="validation_G")
def fixture_graph(sql_test_db_path) -> Graph:
    validation_onto_path = Path(__file__).absolute().parent.parent / 'testdata' / 'validation-test-onto.owl'
    return Graph(sql_db_filename=sql_test_db_path, external_ontos=[validation_onto_path])

########################################
###         Helpers                  ###
########################################
def assert_validate_target_in_range_of_prop(G: Graph, prop_name: str, target_good_examples: list, target_bad_examples: list):
    prop =  owlutils.get_entity_by_name(prop_name, G.store)
    for good_target in target_good_examples:
        assert owlutils._validate_target_in_range_of_prop(good_target, prop, G.store) is True, f"Property '{prop.name}' did not accept type '{type(good_target)}'. Defined Range of '{prop.name}': '{prop.range}'."
    for bad_target in target_bad_examples:
        assert owlutils._validate_target_in_range_of_prop(bad_target, prop, G.store) is False, f"Property '{prop.name}' accepted type '{type(bad_target)}', but outside defined range of: '{prop.range}'."

def assert_validate_single_datatype_constraint(constraint: owlready2.ConstrainedDatatype, good_examples: list, bad_examples: list):
    for literal in good_examples:
        valid, violations = owlutils._validate_single_constraint_for_literal(literal, constraint)
        assert valid is True, f"Literal '{literal}' did not pass constraint '{constraint}'"
    for literal in bad_examples:
        valid, violations = owlutils._validate_single_constraint_for_literal(literal, constraint)
        assert valid is False, f"Literal '{literal}' passed constraint '{constraint}' but should not have passed."

########################################
###              Tests               ###
########################################

def test_determine_prop_type_and_if_functional(G: Graph):
    # 1) Assert for functional object property by getting the functional ObjectProperty hasCause first
    func_object_prop = owlutils.get_entity_by_name("hasCause", G.store)
    prop_type, is_functional = owlutils._determine_prop_type_and_if_functional(func_object_prop, G.store)
    assert prop_type == 'ObjectProperty', "Does not recognize 'hasCause' as ObjectProperty"
    assert is_functional is True, "Does not recognize functional property 'hasCause'"
    # 2) ASsert for non functional object property, without getting the property first
    prop_type, is_functional = owlutils._determine_prop_type_and_if_functional("isCausing", G.store)
    assert prop_type == 'ObjectProperty', "Does not recognize 'isCausing' as ObjectProperty"
    assert is_functional is False, "Does not recognize ObjectProperty 'isCausing' as not functional"
    # 3) Assert for functional data property 'hasTimeLag'
    prop_type, is_functional = owlutils._determine_prop_type_and_if_functional("hasTimeLag", G.store)
    assert prop_type == 'DataProperty', "Does not recognize 'hasTimeLag' as DataProperty"
    assert is_functional is True, "Does not recognize data property 'hasTimeLag' as functional"
    # 4) Assert for data property 'comment' does result in None, None (because comment is a DefaultProperty, which cannot be checked)
    prop_type, is_functional = owlutils._determine_prop_type_and_if_functional("comment", G.store)
    assert prop_type == None, "Does not recognize 'comment' as a DefaultProperty. Should have returned 'None'"
    assert is_functional == None, "Does not recognize data property 'comment' as a DefaultProperty. Should have returned 'None'"
    # 5) Assert raises ValueError for non properties ('CausalNode') or non existing entities ('thisDoesNotExist')
    with pytest.raises(ValueError):
        prop_type, is_functional = owlutils._determine_prop_type_and_if_functional("CausalNode", G.store)
        prop_type, is_functional = owlutils._determine_prop_type_and_if_functional("thisDoesNotExist", G.store)

def test_validate_if_entity_is_property(G: Graph):
    # Define test-cases:
    good_examples = ["hasCause", owlutils.get_entity_by_name("hasTimeLag", G.store), "comment"]
    bad_examples = ["Doesnotexist", G.add.causal_node("test_node"), "CausalEdge"]
    # Assert that all is working as expected
    for example in good_examples:
        assert owlutils.validate_if_entity_is_property(example, G.store) is True, f"Function '_validate_if_entity_is_property' did not return 'True' for valid property '{example}'."
    for example in bad_examples:
        assert owlutils.validate_if_entity_is_property(example, G.store) is False, f"Function '_validate_if_entity_is_property' did not return 'False' for invalid property '{example}'."

def test_validate_any_class_in_domain_of_prop(validation_G: Graph):
    G = validation_G
    test_node = G.add.causal_node("test_node")
    node_classes = test_node.is_a
    edge = G.add.causal_edge("cause", "effect", "test_edge", force_create=True)
    edge_classes = edge.is_a
    # 1) Assert correct entity & property Case: 'CausalEdge' is in domain of 'hasCause'
    assert owlutils._validate_any_class_in_domain_of_prop(classes=edge_classes, prop='hasCause', store=G.store) is True , "Function '_validate_any_class_in_domain_of_prop' did not return 'True' for valid entity-property pair 'CausalEdge hasCause'."
    # 2) Assert no Domain specified -> True
    assert owlutils._validate_any_class_in_domain_of_prop(classes=edge_classes, prop='noDomainRangeObjectProperty', store=G.store) is True , "Function '_validate_any_class_in_domain_of_prop' did not return 'True' for a property without specified Domain."
    # 4) Assert property outside domain: 'hasCause' has domain 'CausalEdge' and not 'CausalNode'
    assert owlutils._validate_any_class_in_domain_of_prop(classes=node_classes, prop='hasCause', store=G.store) is False , "Function '_validate_any_class_in_domain_of_prop' did not return 'False' for property with wrong domain."
    # 4) Assert invalid property Case: 'False' to be returned if the function excuted on a non property
    assert owlutils._validate_any_class_in_domain_of_prop(classes=node_classes, prop='CausalEdge', store=G.store) is False , "Function '_validate_any_class_in_domain_of_prop' did not return 'False' for non-property 'CausalEdge'."
    # 5) Assert invalid entity Case: 'False' to be returned if function executed on 'non-existing-entity'
    assert owlutils._validate_any_class_in_domain_of_prop(classes=['not-existing-node'], prop='hasCause', store=G.store) is False , "Function '_validate_any_class_in_domain_of_prop' did not return 'False' for non-existing entity 'not-existing-node'."

def test_validate_constraints():
    # 1) Assert length constraint
    constraint = owlready2.ConstrainedDatatype(str, length=5)
    good_examples = ['12345', 'abcde']
    bad_examples = ['123456', 2.0]
    assert_validate_single_datatype_constraint(constraint, good_examples, bad_examples)
    # 2) Asert min_length, max_length constraints
    constraint = owlready2.ConstrainedDatatype(str, min_length=5, max_length=10)
    good_examples = ['12345', 'abcde', '1234567890']
    bad_examples = ['1234', '123456789101112', 2.0]
    assert_validate_single_datatype_constraint(constraint, good_examples, bad_examples)
    # 3) Assert pattern / regex constraints
    constraint = owlready2.ConstrainedDatatype(str, pattern=r"^[a-zA-Z]+\.[a-zA-Z]+-\d+$")#
    good_examples = ['a.b-23', 'ras.sad-0'] 
    bad_examples = ['nodots', 'no.num-bers']
    assert_validate_single_datatype_constraint(constraint, good_examples, bad_examples)
    # 4) Assert min_inclusive, max_inclusive constraints
    constraint = owlready2.ConstrainedDatatype(float, min_inclusive=0, max_inclusive=10)
    good_examples = [0.0, 5.0, 10.0]
    bad_examples = [-0.1, 10.1, 2]
    assert_validate_single_datatype_constraint(constraint, good_examples, bad_examples)
    # 5) Assert min_exclusive, max_exclusive constraints for float
    constraint = owlready2.ConstrainedDatatype(float, min_exclusive=0, max_exclusive=10)
    good_examples = [0.1, 9.9]
    bad_examples = [-0.1, 10.1, 2, 10.0, 0.0]
    assert_validate_single_datatype_constraint(constraint, good_examples, bad_examples)
    # 6) Assert min_exclusive, max_exclusive constraints for int
    constraint = owlready2.ConstrainedDatatype(int, min_exclusive=0, max_exclusive=10)
    good_examples = [1, 9]
    bad_examples = [-1, 0, 10, 11, 2.0]
    assert_validate_single_datatype_constraint(constraint, good_examples, bad_examples)
    # 7) Assert total_digits, fraction_digits constraints
    constraint = owlready2.ConstrainedDatatype(float, total_digits=5, fraction_digits=2)
    good_examples = [321.01, 123.22]
    bad_examples = [321.001, 1, 12345.0]
    assert_validate_single_datatype_constraint(constraint, good_examples, bad_examples)
    
def test_validate_constraints_for_literal():
    # Set up two constraints for two different datatypes (to allow int and float)
    constraintFloat = owlready2.ConstrainedDatatype(float, min_exclusive=0.0, max_exclusive=10.0)
    constraintInt = owlready2.ConstrainedDatatype(int, min_exclusive=0, max_exclusive=10)
    example_int = 5
    # 1) Assert that for int lieteral, single constraint validation returns False for float constraint abd true for int literal
    result_for_float_constraint, _ = owlutils._validate_single_constraint_for_literal(example_int, constraintFloat)
    assert result_for_float_constraint is False, "Function '_validate_single_constraint_for_literal' did not return 'False' for float constraint on int literal."
    result_for_int_constraint, _ = owlutils._validate_single_constraint_for_literal(example_int, constraintInt)
    assert result_for_int_constraint is True, "Function '_validate_single_constraint_for_literal' did not return 'True' for int constraint on int literal."
    # 2) Assert that if both constraints are passed, true is returned
    result_for_both_constraints = owlutils._validate_constraints_for_literal(example_int, [constraintFloat, constraintInt])
    assert result_for_both_constraints is True


def test_validate_target_in_range_of_prop(validation_G: Graph):
    # 0) Generate CausalNode as test Object
    G = validation_G
    test_node = G.add.causal_node("test_node")
    test_edge  = G.add.causal_edge("cause", "effect", "test_edge", force_create=True)
    # 1) Test for functional object Property 'hasCause' which should only accept single objects of type 'CausalNode'
    prop_name = "hasCause"
    good_targets = [test_node, "test_node"]
    bad_targets = ["non existing node", test_edge, "test_edge", [test_node]]
    assert_validate_target_in_range_of_prop(G, prop_name, good_targets, bad_targets)
    # 2)  Test for object Property 'isCausing' which should only accept things of type list['CausalEdge']
    prop_name = "isCausing"
    good_targets = [[test_edge]]
    bad_targets = [test_edge, [test_node], 0.5] # Does not accept single 'CausalEdges', lists with content 'CausalNode' or floats
    assert_validate_target_in_range_of_prop(G, prop_name, good_targets, bad_targets)
    # 3) Test for functional dataProperty 'hasTimeLag' which should be a single float literal >= 0.0
    prop_name = "hasTimeLag"
    good_targets = [0.5, 6]
    bad_targets = ["a string", [0.5], -0.5,  test_node]  # Does not acccept strings, lists or CausalNodes
    # 4) Test for functional dataProperty 'hasCofnidence' which should be a single float literal [0,1]
    prop_name = "hasTimeLag"
    good_targets = [0.5, 1.0, 0.0]
    bad_targets = ["a string", [0.5], -0.5,  test_node]  # Does not acccept strings, lists or CausalNodes
    assert_validate_target_in_range_of_prop(G, prop_name, good_targets, bad_targets)
    # 5) Test for non functional dataProperty 'StringRangeNonFunctionalDataProperty' which could contain multiple string literals
    prop_name = "StringRangeNonFunctionalDataProperty"
    good_targets = [["a string"], ["string1", "string2"]] # Only accepts lists of strings
    bad_targets = ["String not in list", [0.5, "string"], [test_node]]
    # 6) Test for property with no range specified everything is accepted
    prop_name = "noDomainRangeFunctionalDataProperty"
    good_targets = ["a string", 0.5, test_node]     # Accepts everything that is not a list
    bad_targets = [["a list is not accepted", 0.5]]

def test_get_entity_by_name(G: Graph):
    """Test that retrieving an entity from the store works"""
    node = G.add.causal_node()
    node_e_b_n = owlutils.get_entity_by_name(node.name, G.store)
    assert node_e_b_n is not None


def test_entity_exists(G: Graph):
    """Test that checking if an entity exists works"""
    # Assert that the node exists after creation
    node_obj = G.add.causal_node("test_node")
    assert owlutils.entity_exists(node_obj, G.store) is True
    # Assert that the node does not exist anymore after removal
    G.remove.causal_node(node_obj)
    assert owlutils.entity_exists(node_obj, G.store) is False


def test_get_name_and_object(G: Graph):
    # Use old functions to get object, and assert that naming is consistent
    name = "hasCause"
    object= owlutils.get_entity_by_name(name, G.store)
    assert name == object.name, "Name and object name are not consistent"
    # Test via name
    name_new, object_new = owlutils.get_name_and_object(name, G.store)
    assert name == name_new, "Did not find object via name"
    assert object == object_new, "Did not find object via name"
    # Test via object 
    name_new, object_new = owlutils.get_name_and_object(object, G.store)
    assert name == name_new, "Did not find object via object"
    assert object == object_new, "Did not find object via object"


def test_is_instance_of_type(G: Graph):
    """Test that checking if an individual belongs to a
    certain class works"""
    G.add.causal_node("cause")
    G.add.causal_node("effect")
    edge_name = G.add.causal_edge("cause", "effect")
    assert owlutils.is_instance_of_type("cause", "CausalNode", G.store)
    assert owlutils.is_instance_of_type(edge_name, "CausalEdge", G.store)

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_is_instance_of_class(G: Graph):
    """Test if still works and displays deprecation warning"""
    G.add.causal_node("cause")
    G.add.causal_node("effect")
    edge_name = G.add.causal_edge("cause", "effect")
    # Assert functionality is the same as in test_is_instance_of_type
    assert owlutils.is_instance_of_class("cause", "CausalNode", G.store)
    assert owlutils.is_instance_of_class(edge_name, "CausalEdge", G.store)
    # Assert that deprecation warning is displayed when calling is_instance_of_class
    with pytest.deprecated_call():
        owlutils.is_instance_of_class("cause", "CausalNode", G.store)

def test_is_instance_of_type_with_non_existing_individual(G: Graph):
    """Test that checking if a non-existing individual belongs to a certain
    class does not work"""
    should_be_false = owlutils.is_instance_of_type(individual= "does_not_exist",
                                                    type= "CausalNode",
                                                    store= G.store)
    assert should_be_false is False


def test_is_instance_of_type_with_subclasses(G: Graph):
    """Test that checking if an individual belongs to a class or one of
    its subclasses works"""
    # Event is subtype of CausalNode and should therefore yield true
    event_node_obj = owlutils.create_individual_of_type("Event", G.store)
    assert owlutils.is_instance_of_type(individual=event_node_obj,
                                         type="CausalNode",
                                         store=G.store,
                                         include_subtypes=True)


def test_is_valid_class_type(G: Graph):
    """Test that checking if a string is a valid class name works"""
    should_be_false = owlutils.is_valid_class_type("InvalidClass", G.store)
    should_be_true  = owlutils.is_valid_class_type("CausalEdge", G.store)
    assert should_be_false is False
    assert should_be_true  is True


def test_none_creation_of_node_with_same_name_as_class(G: Graph):
    """Test if node creation with invalid name returns 'None'"""
    # Make sure that valid and invalid name are set correctly
    invalid_name = "Event"
    should_be_false = owlutils.is_valid_individual_name(invalid_name, G.store)
    should_be_true = owlutils.is_valid_individual_name("valid_name", G.store)
    assert should_be_false is False
    assert should_be_true is True
    new_node = 'Not None'
    new_node = G.add.individual_of_type(class_of_individual= "Event", name_for_individual=invalid_name)
    assert new_node is None


def test_none_creation_of_node_with_unknown_properties(G: Graph):
    """Test that creating an individual with properties that are not allowed
    does not work"""
    # Create sample edge for testing
    edge_object = G.add.causal_edge("cause", "effect", "correct_edge_name", force_create=True)
    # Test if misspelled property_type yields None
    wrong_node = G.add.individual_of_type(class_of_individual= "CausalNode",
                                          wrong_property_type = [edge_object])
    assert wrong_node is None


def test_none_creation_of_node_with_unknown_target_object_for_property(G: Graph):
    """Test that creating a node with a non-existing cause does not work"""
    # Create sample edge for testing
    edge = G.add.causal_edge(cause_node="cause",
                            effect_node="effect",
                            name_for_edge="correct_edge_name",
                            force_create=True)
    misspelled_edge_name = owlutils.get_entity_by_name(f'misspelled{edge.name}', G.store)
    assert misspelled_edge_name is None
    # Test if misspelled property_type yields None when validation enabled
    unknown_node = owlutils.create_individual_of_type(class_of_individual= "CausalNode",
                                                      store=G.store,
                                                      validate_domain_range=True,
                                                      hasCause=misspelled_edge_name)
    assert unknown_node is None, "Validation did not detect that 'misspelled_edge_name' is a non existing entity."
    # Test if misspelled property_type yields None when validation disabled
    unknown_node = owlutils.create_individual_of_type(class_of_individual= "CausalNode",
                                                        store=G.store,
                                                        validate_domain_range=False,
                                                        hasCause=misspelled_edge_name)
    assert unknown_node is not None, "Should have passed with disabled validation."


def test_update_of_property_via_create_individual_of_type(G: Graph):
    """Test that if a node is added twice with more properties,
    these properties shall be added."""
    event_node_obj = owlutils.create_individual_of_type("Event", G.store)
    my_comment = "This should be added when called the second time"
    event_node_updated = owlutils.create_individual_of_type(class_of_individual="Event",
                                                            store=G.store,
                                                            name_for_individual=event_node_obj.name,
                                                            comment=[my_comment])
    # Assert that same name is returned twice (and not None for event_node_updated)
    assert event_node_updated.comment == [my_comment]


def test_get_all_causalnodes_and_edges(G: Graph):
    """Test that retrieving all nodes and edges works properly"""
    # Create graph with example set 'flat_tire' -> the first 6 individuals are nodes
    nodes_list = ['bumpy_feeling', 'flat_tire', 'thorns_on_road',
                  'noise', 'glass_on_road', 'steering_problems']
    edge_names = ['noise_flat_tire', 'bumpy_feeling_flat_tire', 'steering_problems_flat_tire',
                  'glass_flat_tire', 'thorns_flat_tire']
    edge_dict = {
        # <edge_name>: [<cause>, <effect>]
        edge_names[0]: ['flat_tire', 'noise'],
        edge_names[1]: ['flat_tire', 'bumpy_feeling'],
        edge_names[2]: ['flat_tire', 'steering_problems'],
        edge_names[3]: ['glass_on_road', 'flat_tire'],
        edge_names[4]: ['thorns_on_road', 'flat_tire'],
    }
    # Add nodes and edges
    for node in nodes_list:
        G.add.causal_node(node)
    for edge in edge_dict:
        edge_name = edge
        cause = edge_dict[list(edge_dict.keys())[0]][0]
        effect = edge_dict[list(edge_dict.keys())[0]][1]
        G.add.causal_edge(cause, effect, edge_name)
    nodes_from_func = owlutils.get_all_causalnodes(G.store)
    edges_from_func = owlutils.get_all_causaledges(G.store)
    # Check nodes and nodes_list
    nodes_to_check = [node[0].name for node in nodes_from_func]
    check_1 = set(nodes_list) == set(nodes_to_check)
    # Check edges and edge_dict
    edges_to_check = [edges_from_func[i][0].name for i, _ in enumerate(edges_from_func)]
    check_2 = set(edge_names) == set(edges_to_check)
    G.store.close()
    assert check_1 is True
    assert check_2 is True


def test_get_subclasses_for_content(G: Graph):
    """Test that retrieving the subclasses of a class works properly"""
    subclasses_of_causalnode = owlutils.get_subclasses("CausalNode", G.store)
    subclasses_without_prefix = [node_as_list[0].name for node_as_list in subclasses_of_causalnode]
    # "CausalNode", "Event" should be in subclasses
    assert "CausalNode" in subclasses_without_prefix
    assert "Event" in subclasses_without_prefix
    # 'Creator' should not be in subclasses
    assert "Creator" not in subclasses_without_prefix
    # Should return None if invalid class name is called
    return_for_incorrect_class_name = owlutils.get_subclasses("does_not_exist", G.store)
    assert return_for_incorrect_class_name is None


def test_get_subclasses_none_return_for_non_existing_class(G: Graph):
    """Test that retrieving subclasses for a class that does not exist results in None"""
    # Should return None if invalid class name is called
    return_for_incorrect_class_name = owlutils.get_subclasses("does_not_exist", G.store)
    assert return_for_incorrect_class_name is None
