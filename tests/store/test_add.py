#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/store/add.py
"""

# general imports
import os
from pathlib import Path
import pytest
import owlready2
# causalgraph imports
from causalgraph import Graph
from causalgraph.utils.owlready2_utils import get_entity_by_name
from causalgraph.utils.owlready2_utils import get_all_causalnodes
from causalgraph.utils.owlready2_utils import is_instance_of_class
from causalgraph.utils.owlready2_utils import count_instances_of_type


########################################
###         Fixtures                 ###
########################################
# Temporary sql_db for every test
@pytest.fixture(name= "sql_test_db_path")
def fixture_sql_test_db_path(tmpdir) -> str:
    test_db_relative_path = os.path.join(tmpdir, "test_add.sqlite3")
    yield test_db_relative_path
    os.remove(test_db_relative_path)


@pytest.fixture(name= "testdata_dir")
def fixture_testdata_dir() -> Path:
    testdata_dir = Path(__file__).absolute().parent.parent / 'testdata'
    return testdata_dir


@pytest.fixture(name= "graph")
def fixture_test_graph(sql_test_db_path) -> Graph:
    graph = Graph(sql_db_filename=sql_test_db_path)
    yield graph
    graph.store.close()


@pytest.fixture(name= "pizza_graph")
def fixture_pizza_graph(graph, testdata_dir) -> Graph:
    pizza_onto_file = str(Path.joinpath(testdata_dir, 'pizza.owl'))
    graph.import_ontology(pizza_onto_file)
    return graph


########################################
###              Tests               ###
########################################
def test_added_nodes_persisted(graph: Graph, sql_test_db_path: str):
    """Test that the graph is persisted in the database"""
    # Create two nodes and an edge in the "old"-world
    graph.add.causal_node("test_node")
    graph.add.causal_edge("test_cause", "test_effect")
    individuals = str(list(graph.store.individuals()))
    graph.store.close()
    # Creating a NEW world, reusing persisted individuals in 'sql_test_db_path'
    new_store = owlready2.World()
    new_store.set_backend(filename=sql_test_db_path)
    reloaded_individuals = str(list(new_store.individuals()))
    new_store.close()
    # Assert that all the preexisting individuals are also present in the new graph.store
    assert individuals == reloaded_individuals


def test_add_individual_of_type_with_opt_kwargs(graph: Graph):
    """Test that the individual is initialized with the correct properties"""
    # Create two base nodes
    node1_name = graph.add.causal_node()
    node1 = get_entity_by_name(node1_name, graph.store)
    node2_name = graph.add.causal_node()
    node2 = get_entity_by_name(node2_name, graph.store)
    # Connect two nodes, creating references along with it
    edge_name = graph.add.individual_of_type("CausalEdge", hasCause=[node1], hasEffect=[node2])
    edge = get_entity_by_name(edge_name, graph.store)
    # Assert type and the two connections
    assert is_instance_of_class(edge_name, "CausalEdge", graph.store)
    assert edge.hasCause == [node1]
    assert edge.hasEffect == [node2]


# Tests for causal_add function
def test_multiple_causalnode_instantiation_(graph: Graph):
    """Test that node creation works properly"""
    num_of_causal_node_creations = 5
    # SPARQL query to get all Instances of type "CausalNode"
    causal_nodes_before = count_instances_of_type("CausalNode", graph.add.store)
    for _ in range(num_of_causal_node_creations):
        graph.add.causal_node()
    causal_nodes_after = count_instances_of_type("CausalNode", graph.add.store)
    assert (causal_nodes_after - causal_nodes_before) == num_of_causal_node_creations


def test_causalnode_multiple_instantiation_same_name_same_type(graph: Graph):
    """Test that adding the same node multiple times adds it only once"""
    ## Expected behavior: No new node is created.
    new_instance_name = "new_causal_node"
    num_of_recreations = 3
    causal_nodes_before = count_instances_of_type("CausalNode", graph.add.store)
    # Try to instantiate the same node multiple times
    for _ in range(num_of_recreations):
        graph.add.causal_node(new_instance_name)
    causal_nodes_after = count_instances_of_type("CausalNode", graph.add.store)
    # Assert that only 1 node is added, not 'num_of_recreations' times the node
    assert (causal_nodes_after - causal_nodes_before) == 1


def test_causalnode_instantiation_name_with_different_type_already_exists(graph: Graph):
    """When adding an existing node with a different type no new node is created"""
    instance_name = "double_node"
    graph.add.individual_of_type("Event", instance_name)
    ## Testing
    causal_nodes_before = count_instances_of_type("CausalNode", graph.add.store)
    # Try to instantiate a causal node with same name as event Node:
    created_instance_name = graph.add.causal_node(instance_name)
    causal_nodes_after = count_instances_of_type("CausalNode", graph.add.store)
    # Assert that no causal node is created and that 'None' is returned
    assert (causal_nodes_after - causal_nodes_before) == 0
    assert created_instance_name is None


def test_causal_node_creation_with_creator(graph: Graph):
    """Test that a creator can be initialized and added to a node"""
    # Initialize a new creator
    creator_node_name = graph.add.individual_of_type('Creator', "creator_node")
    creator_node = get_entity_by_name(creator_node_name, graph.store)
    # Create a node which was created by the creator
    causal_node_name = graph.add.causal_node(hasCreator=[creator_node])
    causal_node = get_entity_by_name(causal_node_name, graph.store)
    assert creator_node_name in str(causal_node.hasCreator)


### Tests for graph.add.causal_edge
def test_create_edge_without_preexisting_nodes(graph: Graph):
    """Test that force-creating nodes works when adding an edge"""
    causal_edges_before = count_instances_of_type("CausalEdge", graph.add.store)
    causal_nodes_before = count_instances_of_type("CausalNode", graph.add.store)
    # Create an edge and both nodes
    graph.add.causal_edge("cause", "effect", force_create = True)
    causal_edges_after = count_instances_of_type("CausalEdge", graph.add.store)
    causal_nodes_after = count_instances_of_type("CausalNode", graph.add.store)
    # Assert that exactly two causal nodes and one edge were created
    assert (causal_edges_after - causal_edges_before) == 1
    assert (causal_nodes_after - causal_nodes_before) == 2


def test_create_edge_with_one_preexisting_node(graph: Graph):
    """Test that nodes are only force-created if they don't exist yet"""
    graph.add.causal_node("preexisting_cause")
    causal_edges_before = count_instances_of_type("CausalEdge", graph.add.store)
    causal_nodes_before = count_instances_of_type("CausalNode", graph.add.store)
    # Create an edge and both nodes
    graph.add.causal_edge("preexisting_cause", "effect", force_create = True)
    causal_edges_after = count_instances_of_type("CausalEdge", graph.add.store)
    causal_nodes_after = count_instances_of_type("CausalNode", graph.add.store)
    # Assert that exactly two causal nodes and one edge were created
    assert (causal_edges_after - causal_edges_before) == 1
    assert (causal_nodes_after - causal_nodes_before) == 1

def test_add_causal_edge_default_name(graph: Graph):
    """Test that creates causal edge without passing edge name, thus using default name"""
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    default_edge_name = graph.add.causal_edge(cause_node, effect_node)
    assert default_edge_name == 'causaledge1'

def test_add_causal_edge_by_name_twice(graph: Graph):
    """Test that creating the same edge twice works only once"""
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    edge_name = 'sameEdgeName'
    edge_node_not_none = graph.add.causal_edge(cause_node, effect_node, edge_name)
    edge_node_none = graph.add.causal_edge(cause_node, effect_node, edge_name)
    # Assertions
    assert edge_node_not_none is not None
    assert edge_node_none is None


## Test add causal_edges with additional properties like timeLag and confidence
def test_add_time_lag_and_confidence_to_causal_edge(graph: Graph):
    """Test that known properties like confidence can be added to an edge while
    unknown properties are not added"""
    # Expected behavior: Only known properties are added. Unknown are not added.
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    edge_node_name = graph.add.causal_edge(cause_node, effect_node)
    confidence_value = 0.5
    timelag_value = 3.2
    # Test adding the properties. Quatsch should not work
    edge_node = get_entity_by_name(edge_node_name, graph.store)
    edge_node.hasConfidence = confidence_value
    edge_node.hasTimeLag = timelag_value
    edge_node.quatsch = 22.3
    # Assertions
    properties_of_edge = [str(edge_property) for edge_property in list(edge_node.get_properties())]
    quatsch_included = any('quatsch' in prop for prop in properties_of_edge)
    assert edge_node.hasConfidence == confidence_value
    assert edge_node.hasTimeLag == timelag_value
    assert quatsch_included is False


def test_add_confidence_timelag_during_create_to_causal_edge(graph: Graph):
    """Test that setting the confidence and the timelag of an edge works"""
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    confidence_value = 0.5
    timelag_value = 3.2
    edge_node_name = graph.add.causal_edge(cause_node_name= cause_node,
                                           effect_node_name= effect_node,
                                           confidence=confidence_value,
                                           time_lag_s=timelag_value)
    # Test if confidence is implemented correctly
    edge_node = get_entity_by_name(edge_node_name, graph.store)
    assert edge_node.hasConfidence == confidence_value
    assert edge_node.hasTimeLag == timelag_value


def test_add_confidence_exceeds_range(graph: Graph):
    """Test that confidence values are between 0.0 and 1.0"""
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    edge_node_none = graph.add.causal_edge(cause_node, effect_node, confidence=3.0)
    assert edge_node_none is None
    edge_node_none = graph.add.causal_edge(cause_node, effect_node, confidence=-0.01)
    assert edge_node_none is None
    edge_node_none = graph.add.causal_edge(cause_node, effect_node, confidence=0)
    assert edge_node_none is None
    edge_none_not_none = graph.add.causal_edge(cause_node, effect_node, confidence=1.0)
    assert edge_none_not_none is not None


def test_add_timelag_exceeds_range(graph: Graph):
    """Test that the timelag of an edge has to be positive"""
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    edge_node_none = graph.add.causal_edge(cause_node, effect_node, time_lag_s=-0.2)
    assert edge_node_none is None


def test_add_confidence_via_optional_kwargs(graph: Graph):
    """Test that the confidence of an edge can be set during creation"""
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    confidence_value = 0.8
    edge_node_name = graph.add.causal_edge(cause_node_name= cause_node,
                                           effect_node_name= effect_node,
                                           hasConfidence= confidence_value)
    # Test if confidence is implemented correctly
    edge_node = get_entity_by_name(edge_node_name, graph.store)
    assert edge_node.hasConfidence == confidence_value


def test_update_confidence(graph: Graph):
    """Test that the confidence of an edge can be updated"""
    cause_node = graph.add.causal_node()
    effect_node = graph.add.causal_node()
    old_confidence_value = 0.8
    new_confidence_value = 0.2
    edge_node_name = graph.add.causal_edge(cause_node_name= cause_node,
                                           effect_node_name= effect_node,
                                           hasConfidence= old_confidence_value)
    # Test if confidence is implemented correctly
    edge_node = get_entity_by_name(edge_node_name, graph.store)
    check_old_confidence_value = edge_node.hasConfidence
    edge_node.hasConfidence = new_confidence_value
    check_new_confidence_value = edge_node.hasConfidence
    assert old_confidence_value == check_old_confidence_value
    assert new_confidence_value == check_new_confidence_value


def test_correct_initialization_of_classes_and_individuals_namespace(graph: Graph):
    """Test that ALL baseline classes store in 'classes_onto', 'individuals_onto' is empty"""
    # Setup and Test Baseline for Individuals
    num_individuals_before_in_classes_onto = len(list(graph.classes_onto.individuals()))
    num_individuals_before_in_individuals_onto = len(list(graph.individuals_onto.individuals()))
    assert num_individuals_before_in_classes_onto == 0
    assert num_individuals_before_in_individuals_onto == 0
    # Setup and test baseline for classes
    num_classes_before_in_classes_onto = len(list(graph.classes_onto.classes()))
    num_classes_before_in_individuals_onto = len(list(graph.individuals_onto.classes()))
    assert num_classes_before_in_classes_onto > 0
    assert num_classes_before_in_individuals_onto == 0


def test_causal_node_in_correct_namespace_and_type(graph: Graph):
    """Test that individual is in correct ontology and of correct type"""
    # Setup, get baselines for ontologies:
    test_node_name = graph.add.causal_node()
    test_node_object = get_entity_by_name(test_node_name, graph.store)
    assert test_node_object.is_a == [get_entity_by_name('CausalNode', graph.store)]
    assert test_node_object.namespace.name == graph.individuals_onto.name


def test_causal_edge_in_correct_namespace_and_type(graph: Graph):
    """Test that individual is in correct ontology and of correct type"""
    # Setup, get baselines for ontologies:
    node_a = graph.add.causal_node()
    node_b = graph.add.causal_node()
    edge_ab = graph.add.causal_edge(node_a, node_b)
    test_edge_object = get_entity_by_name(edge_ab, graph.store)
    assert test_edge_object.is_a == [get_entity_by_name('CausalEdge', graph.store)]
    assert test_edge_object.namespace.name == graph.individuals_onto.name


def test_add_individual_of_type_of_correct_namespace_and_type(graph: Graph):
    """Test that individual is in correct ontology and of correct type"""
    # Setup, get baselines for ontologies:
    class_for_individual = 'Creator'
    individual_name = graph.add.individual_of_type(class_for_individual)
    individual_object = get_entity_by_name(individual_name, graph.store)
    assert individual_object.is_a == [get_entity_by_name(class_for_individual, graph.store)]
    assert individual_object.namespace.name == graph.individuals_onto.name
    # Assert that no individual created in classes_onto
    assert len(list(graph.classes_onto.individuals())) == 0


def test_adding_of_comments_after_creation(graph: Graph):
    """Test that comments can be added to nodes"""
    # Setup and add comment in two ways
    node1 = get_entity_by_name(graph.add.causal_node(), graph.store)
    node1.comment = ["This one get's a comment after creation"]
    node2 = get_entity_by_name(graph.add.individual_of_type("Event",
                               comment= "This one gets a comment right away"),
                               store= graph.store)
    # Setup a node which has no comments (for reference)
    no_comment_node = get_entity_by_name(graph.add.causal_node(), graph.store)
    # Do a (SPARQL) query to search for all nodes with a comment starting with "This.."
    all_commented_nodes = graph.store.search(comment="This*")
    all_comented_nodes_iris = [node.iri for node in all_commented_nodes]
    # Assert that 'node1' and 'node2' have comments and 'no_comment_node' does not
    assert node1.iri in all_comented_nodes_iris
    assert node2.iri in all_comented_nodes_iris
    assert no_comment_node.iri not in all_comented_nodes_iris


def test_adding_of_comments_with_add(graph: Graph):
    """Test that comments are added to different types of individuals"""
    # Setup comment string
    comment_to_test = "This should be the comment for all the nodes, this is added to"
    # Create mini graph with nodes, all having comments
    node1_name = graph.add.causal_node()
    node1 = graph.get_entity(node1_name)
    node_with_comment_name = graph.add.causal_node(comment=[comment_to_test])
    node_with_comment = graph.get_entity(node_with_comment_name)
    # Create and retrieve edge
    edge_name = graph.add.causal_edge(cause_node_name= node1_name,
                                      effect_node_name= node_with_comment_name,
                                      comment= [comment_to_test])
    edge_with_comment = graph.get_entity(edge_name)
    # Create and retrieve event
    event_name = graph.add.individual_of_type(class_of_individual= "Event",
                                              name_for_individual="MyEvent",
                                              comment=[comment_to_test])
    event_with_comment = graph.get_entity(event_name)
    # Do a (SPARQL) query to search for all nodes with a comment starting with "This.."
    all_commented_nodes = graph.store.search(comment=comment_to_test)
    all_comented_nodes_iris = [node.iri for node in all_commented_nodes]
    # Assert that *_with comment have comments via sparql
    assert node_with_comment.iri in all_comented_nodes_iris
    assert edge_with_comment.iri in all_comented_nodes_iris
    assert event_with_comment.iri in all_comented_nodes_iris
    # Assert that node1 is not in the ones with comments:
    assert node1.iri not in all_comented_nodes_iris
    # Assert via property access:
    assert node_with_comment.comment == [comment_to_test]


### Tests with Pizza ontology active in pizza_graph
def test_creation_of_pizza(pizza_graph: Graph):
    """Test that a pizza can be created from the pizza ontology"""
    my_pizza_name = pizza_graph.add.individual_of_type("Margherita")
    assert len(pizza_graph.store.search(iri=f"*#{my_pizza_name}")) > 0
    assert get_entity_by_name(my_pizza_name, pizza_graph.store) is not None


def test_causal_edge_btwn_pizzas(pizza_graph: Graph):
    # Setup and assert setup
    pizza_name_one = pizza_graph.add.individual_of_type("Margherita")
    pizza_name_two = pizza_graph.add.individual_of_type("Siciliana")
    assert not is_instance_of_class(pizza_name_one, 'CausalNode', pizza_graph.store)
    assert not is_instance_of_class(pizza_name_two, 'CausalNode', pizza_graph.store)
    # Test if edge is created sucessfully
    resulting_edge_name = pizza_graph.add.causal_edge(pizza_name_one, pizza_name_two)
    assert get_entity_by_name(resulting_edge_name, pizza_graph.store) is not None
    # Test if both pizzas are now also of type 'CausalNode'
    assert is_instance_of_class(pizza_name_one, 'CausalNode', pizza_graph.store)
    assert is_instance_of_class(pizza_name_two, 'CausalNode', pizza_graph.store)
    # Double check: Test if pizza now is also included in get_all_causalnodes()
    causalnode_names = [node[0].name for node in get_all_causalnodes(pizza_graph.store)]
    assert pizza_name_one in causalnode_names
    assert pizza_name_two in causalnode_names


def test_causal_edge_btwn_pizza_and_causal_node(pizza_graph: Graph):
    # Setup and assert setup
    pizza_name_one = pizza_graph.add.individual_of_type("Margherita")
    causal_node_name = pizza_graph.add.causal_node()
    assert not is_instance_of_class(pizza_name_one, 'CausalNode', pizza_graph.store)
    # Test if edge is created sucessfully
    resulting_edge_name = pizza_graph.add.causal_edge(pizza_name_one, causal_node_name)
    assert get_entity_by_name(resulting_edge_name, pizza_graph.store) is not None
    # Test if both pizzas are now also of type 'CausalNode' and therefore
    # included in get_all_causalnodes()
    assert is_instance_of_class(pizza_name_one, 'CausalNode', pizza_graph.store)


def test_prohibited_creation_of_edge_between_creator_and_causal_node(pizza_graph: Graph):
    class_to_test = "Creator"
    creator_node_name = pizza_graph.add.individual_of_type(class_to_test)
    causal_node_name = pizza_graph.add.causal_node()
    # Assert that 'class_to_test' is in list of classes excluded for causal_connections
    assert class_to_test in [node[0].name for node in
                             pizza_graph.add.classes_prohibited_from_causal_connections]
    # Try to create edge with one node, which is not allowed to be part of a causal connection
    potential_edge = pizza_graph.add.causal_edge(creator_node_name, causal_node_name)
    # Should result in none
    assert potential_edge is None
