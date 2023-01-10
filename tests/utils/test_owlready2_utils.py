#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/utils/owlready2_utils.py
"""

# general imports
import os
import pytest
# causalgraph imports
from causalgraph import Graph
import causalgraph.utils.owlready2_utils as owlutils


########################################
###         Fixtures                 ###
########################################
# Temporary sql_db for every test
@pytest.fixture(name= "sql_test_db_path")
def fixture_sql_test_db_path(tmpdir) -> str:
    test_db_relative_path = os.path.join(tmpdir, "test_readwrite.sqlite3")
    yield test_db_relative_path
    os.remove(test_db_relative_path)


@pytest.fixture(name= "test_graph")
def fixture_test_graph(sql_test_db_path: str) -> Graph:
    return Graph(sql_db_filename=sql_test_db_path)


########################################
###              Tests               ###
########################################
def test_get_entity_by_name(test_graph: Graph):
    """Test that retrieving an entity from the store works"""
    node_name = test_graph.add.causal_node()
    node_element = owlutils.get_entity_by_name(node_name, test_graph.store)
    assert node_element is not None


def test_entity_exists(test_graph: Graph):
    """Test that checking if an entity exists works"""
    # Assert that the node exists after creation
    node_name = test_graph.add.causal_node("test_node")
    assert owlutils.entity_exists(node_name, test_graph.store) is True
    # Assert that the node does not exist anymore after removal
    test_graph.remove.causal_node(node_name)
    assert owlutils.entity_exists(node_name, test_graph.store) is False


def test_is_instance_of_class(test_graph: Graph):
    """Test that checking if an individual belongs to a
    certain class works"""
    test_graph.add.causal_node("cause")
    test_graph.add.causal_node("effect")
    edge_name = test_graph.add.causal_edge("cause", "effect")
    assert owlutils.is_instance_of_class("cause", "CausalNode", test_graph.store)
    assert owlutils.is_instance_of_class(edge_name, "CausalEdge", test_graph.store)


def test_is_instance_of_class_with_non_existing_individual(test_graph: Graph):
    """Test that checking if a non-existing individual belongs to a certain
    class does not work"""
    should_be_false = owlutils.is_instance_of_class(individual_name= "does_not_exist",
                                                    class_name= "CausalNode",
                                                    store= test_graph.store)
    assert should_be_false is False


def test_is_instance_of_class_with_subclasses(test_graph: Graph):
    """Test that checking if an individual belongs to a class or one of
    its subclasses works"""
    # Event is subtype of CausalNode and should therefore yield true
    event_node_name = owlutils.create_individual_of_type("Event", test_graph.store)
    assert owlutils.is_instance_of_class(individual_name= event_node_name,
                                         class_name= "CausalNode",
                                         store= test_graph.store,
                                         include_subtypes=True)


def test_is_valid_class_type(test_graph: Graph):
    """Test that checking if a string is a valid class name works"""
    should_be_false = owlutils.is_valid_class_type("InvalidClass", test_graph.store)
    should_be_true  = owlutils.is_valid_class_type("CausalEdge", test_graph.store)
    assert should_be_false is False
    assert should_be_true  is True


def test_none_creation_of_node_with_same_name_as_class(test_graph: Graph):
    """Test if node creation with invalid name returns 'None'"""
    # Make sure that valid and invalid name are set correctly
    invalid_name = "Event"
    should_be_false = owlutils.is_valid_individual_name(invalid_name, test_graph.store)
    should_be_true = owlutils.is_valid_individual_name("valid_name", test_graph.store)
    assert should_be_false is False
    assert should_be_true is True
    new_node = 'Not None'
    new_node = owlutils.create_individual_of_type(class_of_individual= "Event",
                                                  store= test_graph.store,
                                                  name_for_individual=invalid_name)
    assert new_node is None


def test_none_creation_of_node_with_unknown_properties(test_graph: Graph):
    """Test that creating an individual with properties that are not allowed
    does not work"""
    # Create sample edge for testing
    edge_name = test_graph.add.causal_edge("cause", "effect", "correct_edge_name")
    edge_object = owlutils.get_entity_by_name(edge_name, test_graph.store)
    # Test if misspelled property_type yields None
    wrong_node = owlutils.create_individual_of_type(class_of_individual= "CausalNode",
                                                    store= test_graph.store,
                                                    wrong_property_type = [edge_object])
    assert wrong_node is None


def test_none_creation_of_node_with_unknown_target_object_for_property(test_graph: Graph):
    """Test that creating a node with a non-existing cause does not work"""
    # Create sample edge for testing
    edge_name = test_graph.add.causal_edge(cause_node_name= "cause",
                                           effect_node_name= "effect",
                                           name_for_edge= "correct_edge_name")
    misspelled_edge_name = owlutils.get_entity_by_name(f'misspelled{edge_name}', test_graph.store)
    assert misspelled_edge_name is None
    # Test if misspelled property_type yields None
    unknown_node = owlutils.create_individual_of_type(class_of_individual= "CausalNode",
                                                      store= test_graph.store,
                                                      hasCause = [misspelled_edge_name])
    assert unknown_node is None


def test_update_of_property_via_create_individual_of_type(test_graph: Graph):
    """Test that if a node is added twice with more properties,
    these properties shall be added."""
    event_node_name = owlutils.create_individual_of_type("Event", test_graph.store)
    my_comment = "This should be added when called the second time"
    event_node_updated = owlutils.create_individual_of_type(class_of_individual= "Event",
                                                            store= test_graph.store,
                                                            name_for_individual= event_node_name,
                                                            comment = [my_comment])
    # Assert that same name is returned twice (and not None for event_node_updated)
    event_node = test_graph.get_entity(event_node_updated)
    assert event_node.comment == [my_comment]


def test_get_all_causalnodes_and_edges(test_graph: Graph):
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
        test_graph.add.causal_node(node)
    for edge in edge_dict:
        edge_name = edge
        cause = edge_dict[list(edge_dict.keys())[0]][0]
        effect = edge_dict[list(edge_dict.keys())[0]][1]
        test_graph.add.causal_edge(cause, effect, edge_name)
    nodes_from_func = owlutils.get_all_causalnodes(test_graph.store)
    edges_from_func = owlutils.get_all_causaledges(test_graph.store)
    # Check nodes and nodes_list
    nodes_to_check = [node[0].name for node in nodes_from_func]
    check_1 = set(nodes_list) == set(nodes_to_check)
    # Check edges and edge_dict
    edges_to_check = [edges_from_func[i][0].name for i, _ in enumerate(edges_from_func)]
    check_2 = set(edge_names) == set(edges_to_check)
    test_graph.store.close()
    assert check_1 is True
    assert check_2 is True


def test_get_subclasses_for_content(test_graph: Graph):
    """Test that retrieving the subclasses of a class works properly"""
    subclasses_of_causalnode = owlutils.get_subclasses("CausalNode", test_graph.store)
    subclasses_without_prefix = [node_as_list[0].name for node_as_list in subclasses_of_causalnode]
    # "CausalNode", "Event" should be in subclasses
    assert "CausalNode" in subclasses_without_prefix
    assert "Event" in subclasses_without_prefix
    # 'Creator' should not be in subclasses
    assert "Creator" not in subclasses_without_prefix
    # Should return None if invalid class name is called
    return_for_incorrect_class_name = owlutils.get_subclasses("does_not_exist", test_graph.store)
    assert return_for_incorrect_class_name is None


def test_get_subclasses_none_return_for_non_existing_class(test_graph: Graph):
    """Test that retrieving subclasses for a class that does not exist results in None"""
    # Should return None if invalid class name is called
    return_for_incorrect_class_name = owlutils.get_subclasses("does_not_exist", test_graph.store)
    assert return_for_incorrect_class_name is None
