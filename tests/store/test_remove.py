#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/store/remove.py
"""

# general imports
import os
import pytest
# causalgraph imports
from causalgraph import Graph
from causalgraph.utils.owlready2_utils import get_entity_by_name
from causalgraph.utils.owlready2_utils import count_instances_of_type


########################################
###         Fixtures                 ###
########################################
# Temporary sql_db for every test
@pytest.fixture(name= "sql_test_db_path")
def fixture_sql_test_db_path(tmpdir) -> str:
    test_db_relative_path = os.path.join(tmpdir, "test_remove.sqlite3")
    yield test_db_relative_path
    os.remove(test_db_relative_path)

# Create Graph class with access to add and remove
@pytest.fixture(name= "graph")
def fixture_graph(sql_test_db_path) -> Graph:
    graph = Graph(sql_db_filename=sql_test_db_path)
    yield graph
    graph.store.close()


########################################
###              Tests               ###
########################################
def test_delete_calling_with_none(graph: Graph):
    should_be_false = graph.remove.delete_individual_of_type(None, None)
    assert should_be_false is False


## Test remove causal_nodes function
def test_remove_not_existing_causalnode(graph: Graph):
    """Test that the remove functionality works properly"""
    # Expected behavior: first remove should be true, second false, because node does not exist
    test_node = graph.add.causal_node()
    should_be_true = graph.remove.causal_node(test_node)
    should_be_false = graph.remove.causal_node(test_node)
    assert should_be_true is True
    assert should_be_false is False


def test_remove_multiple_causalnodes(graph: Graph):
    """Test that adding and then removing nodes works properly"""
    num_of_causal_node_creations = 5
    for i in range(num_of_causal_node_creations):
        graph.add.causal_node(str(i))
    causal_nodes_added = count_instances_of_type("CausalNode", graph.store)
    assert causal_nodes_added == num_of_causal_node_creations
    # deletes 5 nodes from the graph
    for i in range(num_of_causal_node_creations):
        graph.remove.causal_node(str(i))
    causal_nodes_after = count_instances_of_type("CausalNode", graph.store)
    # Assert that all causal nodes are deleted
    assert causal_nodes_after == 0


def test_causalnode_delete_of_incorrect_type(graph: Graph):
    """Test that remove.causal_node() only works for nodes and not other types"""
    # Expected behavior: Instance not deleted, as of wrong class ("Event"),  returnes False
    instance_name = graph.add.individual_of_type("Event")
    causal_nodes_before = count_instances_of_type("CausalNode", graph.store)
    # Try to delete a causal node with the same name as event node:
    delete_success = graph.remove.causal_node(instance_name)
    causal_nodes_after = count_instances_of_type("CausalNode", graph.store)
    # Assert that no causal node is deleted and that 'None' is returned
    assert (causal_nodes_after and causal_nodes_before) == 0
    assert delete_success is False


def test_delete_a_node_with_a_wrong_class(graph: Graph):
    """Test that a wrong type name leads to an individual not being deleted"""
    causal_nodes_before = count_instances_of_type("CausalNode", graph.store)
    graph.add.causal_node("cause")
    graph.add.causal_node("effect")
    delete_node = graph.remove.delete_individual_of_type("cause", "nonexistent_node")
    causal_nodes_after = count_instances_of_type("CausalNode", graph.store)
    # Assert that no causal node is deleted and that 'False' is returned
    assert delete_node is False and causal_nodes_before == 0 and causal_nodes_after == 2


def test_causalnode_delete_from_a_reloaded_graph(sql_test_db_path: str):
    """Test that an individual can be deleted from a reloaded graph as well"""
    # Setup old Graph and add a causal node
    graph = Graph(sql_db_filename=sql_test_db_path)
    causal_node_name = graph.add.causal_node("cause")
    num_causal_nodes = count_instances_of_type("CausalNode", graph.store)
    graph.store.save()
    graph_new = Graph(sql_db_filename=sql_test_db_path)
    reloaded_num_causal_nodes = count_instances_of_type("CausalNode", graph_new.store)
    assert num_causal_nodes == reloaded_num_causal_nodes
    assert get_entity_by_name(causal_node_name, graph_new.store) is not None
    # Try to delete a causal node from the reloaded graph
    graph_new.remove.causal_node(causal_node_name)
    # Assert that this causal node was deleted
    assert (reloaded_num_causal_nodes - 1) == count_instances_of_type("CausalNode", graph_new.store)
    assert get_entity_by_name(causal_node_name, graph_new.store) is None


### Test for Removing Causal Edges
def test_remove_edge_from_non_existing_causalnode(graph: Graph):
    """Test that an edge can only be deleted if the nodes it connects exist"""
    # Expected behavior: False should be returned if cause_node or effect_node does not exist
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    graph.add.causal_edge(cause_node, effect_node)
    # Testing if False is returned if one of the edges does not exist
    graph.remove.causal_node(cause_node)
    should_be_false = graph.remove.causal_edges(cause_node, effect_node)
    assert should_be_false is False


def test_remove_multiple_causaledges_with_name(graph: Graph):
    """Tets that removing multiple edges works"""
    num_of_causal_edge_creations = 5
    # adds 5 edges to the graph
    graph.add.causal_node("cause")
    graph.add.causal_node("effect")
    for i in range(num_of_causal_edge_creations):
        graph.add.causal_edge("cause", "effect", str(i))
    causal_edge_added = count_instances_of_type("CausalEdge", graph.store)
    assert causal_edge_added == num_of_causal_edge_creations
    # deletes 5 nodes from the graph
    for i in range(num_of_causal_edge_creations):
        graph.remove.causal_edge_by_name(str(i))
    causal_edge_after = count_instances_of_type("CausalEdge", graph.store)
    # Assert that all causal edges are deleted
    assert causal_edge_after == 0


def test_remove_multiple_causaledges_with_nodes(graph: Graph):
    """Test that 5 edges between the same two nodes are added and
    all are deleted in one go"""
    num_of_causal_edge_creations = 5
    # adds 5 edge between the same nodes
    graph.add.causal_node("cause")
    graph.add.causal_node("effect")
    for i in range(num_of_causal_edge_creations):
        graph.add.causal_edge("cause", "effect", str(i))
    causal_edges_before = count_instances_of_type("CausalEdge", graph.store)
    assert causal_edges_before == 5
    # deletes all 5 edges at once
    graph.remove.causal_edges("cause", "effect")
    causal_edges_after = count_instances_of_type("CausalEdge", graph.store)
    # Assert that all causal edge are deleted
    assert causal_edges_after == 0


def test_causaledges_delete_multiple_times(graph: Graph):
    """Test that one edge is deleted and nothing more"""
    graph.add.causal_node("cause")
    graph.add.causal_node("effect")
    graph.add.causal_edge("cause", "effect")
    first_remove_should_be_true = graph.remove.causal_edges("cause", "effect")
    second_remove_should_be_false = graph.remove.causal_edges("cause", "effect")
    ## Assertions
    assert first_remove_should_be_true is True
    assert second_remove_should_be_false is True


def test_causal_edge_order_dependency(graph: Graph):
    """Test that edges are deleted irrespective of
    the order of cause and effect"""
    graph.add.causal_node("nodeA")
    graph.add.causal_node("nodeB")
    graph.add.causal_edge("nodeA", "nodeB", "edgeAB")
    graph.add.causal_edge("nodeB", "nodeA", "edgeBA")
    edges_before = count_instances_of_type("CausalEdge", graph.store)
    assert edges_before == 2
    # Delete edges between A and B -> Should delete both edges regardless of direction
    graph.remove.causal_edges("nodeB", "nodeA")
    # Assert that both edges are non-existent anymore and all causel edges deleted
    assert get_entity_by_name("edgeAB", graph.store) is None
    assert get_entity_by_name("edgeBA", graph.store) is None
    edges_after_remove = count_instances_of_type("CausalEdge", graph.store)
    assert edges_after_remove == 0


def test_remove_causal_edges_wrong_input_type(graph: Graph):
    """Test that nothing gets deleted due to wrong type used in remove.causal_edges"""
    graph.add.causal_edge("nodeA", "nodeB", "edgeAB")
    graph.add.causal_edge("nodeB", "nodeC", "edgeBC")
    edges_before = count_instances_of_type("CausalEdge", graph.store)
    # Try to delete nodes between AB and BC -> Should delete nothing and return False
    remove_successful = graph.remove.causal_edges("edgeAB", "edgeBC")
    edges_after_remove = count_instances_of_type("CausalEdge", graph.store)
    # Assert that nothing got deleted
    assert edges_before == edges_after_remove
    assert remove_successful is False


## Tests for causal_edges_from_node
def test_remove_all_causal_edges_from_node(graph: Graph):
    """Test that all edges from the node are deleted irrespective
    of the order of cause and effect"""
    graph.add.causal_node("nodeA")
    graph.add.causal_node("nodeB")
    graph.add.causal_edge("nodeA", "nodeB", "edge_ab")
    graph.add.causal_edge("nodeB", "nodeA", "edge_ba")
    edges_before = count_instances_of_type("CausalEdge", graph.store)
    # Delete all edges from node 'nodeB' -> Should delete all edges regardless of direction
    deletion_successful = graph.remove.causal_edges_from_node("nodeB")
    edges_after_remove = count_instances_of_type("CausalEdge", graph.store)
    # Assert that all edges are deleted, which were connected with 'nodeB'
    assert deletion_successful is True
    assert get_entity_by_name("edge_ab", graph.store) is None
    assert get_entity_by_name("edge_ba", graph.store) is None
    assert (edges_before - edges_after_remove) == 2


def test_remove_all_edge_from_non_existing_causalnode(graph: Graph):
    """Test that False is returned since node does not exist"""
    should_be_false = graph.remove.causal_edges_from_node("DoesNotExist")
    assert should_be_false is False


def test_remove_causal_edge_from_node_wrong_input_type(graph: Graph):
    """Test that nothing is removed when input type for
    causal_edges_from_node is wrong"""
    graph.add.causal_edge("nodeA", "nodeB", "edgeAB")
    num_individuals_before_remove = len(list(graph.store.individuals()))
    should_be_false = graph.remove.causal_edges_from_node("edgeAB")
    num_individuals_after_remove = len(list(graph.store.individuals()))
    ## Assert no Individuals deleted and returned correct bool for deletion success
    assert should_be_false is False
    assert num_individuals_before_remove == num_individuals_after_remove


def test_delete_empty_node_with_causal_edges_from_node(graph: Graph):
    """Test that removing edges works if there are none as well"""
    graph.add.causal_node("nodeA")
    assert graph.remove.causal_edges_from_node("nodeA") is True


### Test if adjacent edges are removed correctly
def test_edges_correctly_removed_if_adjacent_causal_node_is_deleted(graph: Graph):
    """Test that if a node is deleted, then the causal edges connected to it should
    be deleted as well"""
    graph.add.causal_node("nodeA")
    graph.add.causal_node("nodeB")
    graph.add.causal_edge("nodeA", "nodeB", "edgeAB")
    graph.remove.causal_node("nodeA")
    node_a = get_entity_by_name("nodeA", graph.store)
    node_b = get_entity_by_name("nodeB", graph.store)
    edge_ab = get_entity_by_name("edgeAB", graph.store)
    # Assertion that node_a and connected edge_ab are deleted, but not node_b
    assert node_a is None
    assert edge_ab is None
    assert node_b is not None


### Test if also adjacent properties are removed correctly
def test_remove_causal_node_adjacent_properties_correctly_removed(graph: Graph):
    """Test that if a node is deleted, then adjacent properties are updated as well"""
    # Setup: Create two causal nodes and one causal edge
    graph.add.causal_node("cause_node")
    # Make 'creator_node' the creator of cause_node
    graph.add.individual_of_type('Creator', "creator_node")
    creator_node = get_entity_by_name("creator_node", graph.store)
    cause_node = get_entity_by_name("cause_node", graph.store)
    cause_node.hasCreator = [creator_node]
    # Assert that hasCreator was created:
    has_creator_node = get_entity_by_name("hasCreator", graph.store)
    all_has_creator_instances = list(has_creator_node.get_relations())
    assert len(all_has_creator_instances) == 1
    # Test: Delete causal_node
    graph.remove.causal_node("cause_node")
    graph.store.save()
    # Assertion that creator_node is not deleted, but the property 'hasCreator'
    # between cause_node and creator_node is
    creator_node_after_remove = get_entity_by_name("creator_node", graph.store)
    assert creator_node_after_remove is not None
    has_creator_instances_after_remove = list(has_creator_node.get_relations())
    assert len(has_creator_instances_after_remove) == 0


### Delete a individual of type
def test_delete_individual_of_type(graph: Graph):
    """Test that an individual of type creator is deleted"""
    # Create the node "creator_node" of class "Creator"
    graph.add.individual_of_type('Creator', "creator_node")
    nodes_before = count_instances_of_type("Creator", graph.store)
    assert nodes_before == 1
    # Deletes "creator_node" of the class "Creator"
    assert graph.remove.delete_individual_of_type("creator_node",'Creator') is True
    nodes_after = count_instances_of_type("Creator", graph.store)
    # Assertation that "creator_node" of class "Creator" is deleted
    assert nodes_after == 0
