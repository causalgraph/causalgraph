#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/store/edit.py
"""

# general imports
import os
from pathlib import Path
import pytest
# causalgraph imports
from causalgraph import Graph
import causalgraph.utils.mapping as maputils
import causalgraph.utils.owlready2_utils as owlutils
from causalgraph.utils.owlready2_utils import get_entity_by_name


########################################
###            Fixtures              ###
########################################
# Temporary sql_db for every test
@pytest.fixture(name= "sql_test_db_path")
def fixture_sql_test_db_path(tmpdir) -> str:
    test_db_relative_path = os.path.join(tmpdir, "test_edit.sqlite3")
    yield test_db_relative_path
    os.remove(test_db_relative_path)


@pytest.fixture(name= "testdata_dir")
def fixture_testdata_dir() -> Path:
    testdata_dir = Path(__file__).absolute().parent.parent / 'testdata'
    return testdata_dir


@pytest.fixture(name= "graph")
def fixture_test_graph(sql_test_db_path) -> Graph:
    # Init graph
    graph = Graph(sql_db_filename=sql_test_db_path)
    # Init creators
    creator_node_name1 = graph.add.individual_of_type("Creator", name_for_individual="Creator1")
    creator_node_name2 = graph.add.individual_of_type("Creator", name_for_individual="Creator2")
    creator_node1 = owlutils.get_entity_by_name(creator_node_name1, graph.store)
    creator_node2 = owlutils.get_entity_by_name(creator_node_name2, graph.store)
    # Init nodes
    graph.add.causal_node('Node 1')
    graph.add.causal_node('Node 2')
    graph.add.causal_node('Node 3')
    graph.add.causal_node('Node 4')
    # Init edges
    graph.add.causal_edge(cause_node_name= 'Node 1',
                          effect_node_name= 'Node 3',
                          name_for_edge= 'Edge 1',
                          confidence= 0.6,
                          time_lag_s= 3)
    graph.add.causal_edge(cause_node_name= 'Node 2',
                          effect_node_name= 'Node 3',
                          name_for_edge= 'Edge 2',
                          time_lag_s= 3,
                          hasCreator= [creator_node1])
    graph.add.causal_edge(cause_node_name= 'Node 3',
                          effect_node_name= 'Node 4',
                          name_for_edge= 'Edge 3',
                          confidence= 0.6,
                          time_lag_s= 3,
                          hasCreator= [creator_node2])
    yield graph
    graph.store.close()


@pytest.fixture(name="faults_graph")
def fixture_faults_graph(graph, testdata_dir) -> Graph:
    faults_onto_file = str(Path.joinpath(testdata_dir, 'faults.owl'))
    graph.import_ontology(faults_onto_file)
    return graph

@pytest.fixture(name="pizza_graph")
def fixture_pizza_graph(graph, testdata_dir) -> Graph:
    pizza_onto_file = str(Path.joinpath(testdata_dir, 'pizza.owl'))
    graph.import_ontology(pizza_onto_file)
    return graph


########################################
###              Tests               ###
########################################
def test_renaming_individuals(graph: Graph):
    """Test that individuals can be renamed"""
    # Init basic graph with properties
    graph.add.causal_node("cause_1")
    graph.add.causal_node("effect_1")
    graph.add.individual_of_type("Creator", "creator_1")
    creator_1 = graph.get_entity(name_of_entity= "creator_1")
    graph.add.causal_edge(cause_node_name= "cause_1",
                               effect_node_name= "effect_1",
                               name_for_edge= "edge_1",
                               confidence= 0.5,
                               time_lag_s= 5,
                               hasCreator= [creator_1])
    graph.add.individual_of_type("Event", "event_1")
    # Rename all individuals
    graph.edit.rename_individual("cause_1", "cause_1_new")
    graph.edit.rename_individual("effect_1", "effect_1_new")
    graph.edit.rename_individual("creator_1", "creator_1_new")
    graph.edit.rename_individual("edge_1", "edge_1_new")
    graph.edit.rename_individual("event_1", "event_1_new")
    # Check if old names are gone
    old_names_list = ["cause_1", "effect_1", "creator_1", "edge_1", "event_1"]
    for old_name in old_names_list:
        check = graph.get_entity(name_of_entity=old_name, suppress_warn=True)
        assert check is None
    # Check if new names exist
    new_names_list = ["cause_1_new", "effect_1_new", "creator_1_new", "edge_1_new", "event_1_new"]
    for new_name in new_names_list:
        check = graph.get_entity(name_of_entity=new_name, suppress_warn=True)
        assert check is not None
    # Check if properties still exist
    cause_1_new = graph.get_entity(name_of_entity="cause_1_new", suppress_warn=True)
    effect_1_new = graph.get_entity(name_of_entity="effect_1_new", suppress_warn=True)
    edge_1_new = graph.get_entity(name_of_entity="edge_1_new", suppress_warn=True)
    creator_1_new = graph.get_entity(name_of_entity="creator_1_new", suppress_warn=True)
    assert str(cause_1_new.isCausing) == "[cg_store.edge_1_new]"
    assert str(effect_1_new.isAffectedBy) == "[cg_store.edge_1_new]"
    assert str(edge_1_new.hasCause) == "[cg_store.cause_1_new]"
    assert str(edge_1_new.hasEffect) == "[cg_store.effect_1_new]"
    assert str(edge_1_new.hasCreator) == "[cg_store.creator_1_new]"
    assert edge_1_new.hasConfidence == 0.5
    assert edge_1_new.hasTimeLag == 5
    assert str(creator_1_new.created) == "[cg_store.edge_1_new]"


def test_renaming_individuals_foreign_onto(pizza_graph: Graph):
    """Test that individuals can be renamed in the pizza ontology"""
    # Init basic graph with foreign ontology and properties
    pizza_graph.add.individual_of_type("Creator", "creator_1")
    creator_1 = pizza_graph.get_entity(name_of_entity="creator_1")
    pizza_graph.add.causal_edge(cause_node_name= "cause_1",
                                effect_node_name= "effect_1",
                                name_for_edge= "edge_1",
                                confidence=0.5,
                                time_lag_s=5,
                                hasCreator=[creator_1],
                                force_create=True)
    pizza_graph.add.individual_of_type("Event", "event_1")
    # Rename all individuals
    pizza_graph.edit.rename_individual("cause_1", "cause_1_new")
    pizza_graph.edit.rename_individual("effect_1", "effect_1_new")
    pizza_graph.edit.rename_individual("edge_1", "edge_1_new")
    pizza_graph.edit.rename_individual("creator_1", "creator_1_new")
    pizza_graph.edit.rename_individual("event_1", "event_1_new")
    # Check if old names are gone
    old_names_list = ["cause_1", "effect_1", "creator_1", "edge_1", "event_1"]
    for old_name in old_names_list:
        check = pizza_graph.get_entity(name_of_entity= old_name, suppress_warn=True)
        assert check is None
    new_names_list = ["cause_1_new", "effect_1_new", "creator_1_new", "edge_1_new", "event_1_new"]
    for new_name in new_names_list:
        check = pizza_graph.get_entity(name_of_entity= new_name, suppress_warn=True)
        assert check is not None
    # Check if properties still exist
    cause_1_new = pizza_graph.get_entity(name_of_entity="cause_1_new", suppress_warn=True)
    effect_1_new = pizza_graph.get_entity(name_of_entity="effect_1_new", suppress_warn=True)
    edge_1_new = pizza_graph.get_entity(name_of_entity="edge_1_new", suppress_warn=True)
    creator_1_new = pizza_graph.get_entity(name_of_entity="creator_1_new", suppress_warn=True)
    assert edge_1_new.hasTimeLag == 5
    assert edge_1_new.hasConfidence == 0.5
    assert str(edge_1_new.hasCause) == "[cg_store.cause_1_new]"
    assert str(creator_1_new.created) == "[cg_store.edge_1_new]"
    assert str(cause_1_new.isCausing) == "[cg_store.edge_1_new]"
    assert str(edge_1_new.hasEffect) == "[cg_store.effect_1_new]"
    assert str(edge_1_new.hasCreator) == "[cg_store.creator_1_new]"
    assert str(effect_1_new.isAffectedBy) == "[cg_store.edge_1_new]"


def test_renaming_individual_already_exist(graph: Graph, pizza_graph: Graph):
    """Test that renaming an individual to an existing name does not work"""
    # Init basic graph with properties
    graph.add.causal_node("cause_1")
    graph.add.causal_node("effect_1")
    graph.add.individual_of_type("Creator", "creator_1")
    creator_1 = graph.get_entity(name_of_entity="creator_1")
    graph.add.causal_edge(cause_node_name= "cause_1",
                          effect_node_name= "effect_1",
                          name_for_edge= "edge_1",
                          confidence=0.5,
                          time_lag_s=5,
                          hasCreator=[creator_1])
    graph.add.individual_of_type("Event", "event_1")
    # Create a pizza individual just in case this does not work with foreign ontos.
    pizza_graph.add.causal_node("maga_name")
    # Check if rename_individual() returns False when trying to select a name that is already taken
    result = graph.edit.rename_individual("cause_1", "effect_1")
    assert result is False
    result = graph.edit.rename_individual("effect_1", "cause_1")
    assert result is False
    result = graph.edit.rename_individual("edge_1", "effect_1")
    assert result is False
    result = graph.edit.rename_individual("creator_1", "edge_1")
    assert result is False
    result = graph.edit.rename_individual("event_1", "edge_1")
    assert result is False
    result = pizza_graph.edit.rename_individual("maga_name", "edge_1")


def test_renaming_individual_not_exist(graph: Graph, pizza_graph: Graph):
    """Test that renaming returns False when renaming non-existing individuals"""
    # Init basic graph with properties
    graph.add.individual_of_type("Creator", "creator_1")
    creator_1 = graph.get_entity(name_of_entity="creator_1")
    graph.add.causal_edge(cause_node_name= "cause_1",
                          effect_node_name= "effect_1",
                          name_for_edge= "edge_1",
                          confidence=0.5,
                          time_lag_s=5,
                          hasCreator=[creator_1],
                          force_create=True)
    graph.add.individual_of_type("Event", "event_1")
    # Create a Pizza individual just in case this does not work with foreign ontos.
    pizza_graph.add.causal_node("maga_name")
    result = graph.edit.rename_individual("does_not_exist", "new_name")
    assert result is False


def test_change_type_to_subtype_known_onto(faults_graph: Graph):
    """Test that the type of an individual can be changed
    to one of its subtypes"""
    graph = faults_graph
    graph.add.causal_node("node_1")
    graph.add.individual_of_type("Creator", "creator_1")
    results = []
    # Change type of individual to its first layer subtypes
    res_node_1 = graph.edit.type_to_subtype(name_of_entity="node_1", new_type="State")
    res_creator_1 = graph.edit.type_to_subtype(name_of_entity="creator_1", new_type="Human_Creator")
    results.extend([res_node_1, res_creator_1])
    # Change type of individual to its second layer subtypes
    graph.add.causal_node("node_2")
    graph.add.individual_of_type("Creator", "creator_2")
    result_node_2 = graph.edit.type_to_subtype(name_of_entity="node_2", new_type="HumanInput_Event")
    result_creator_2 = graph.edit.type_to_subtype(name_of_entity="creator_2",
                                                  new_type="LearningAlgorithm_Creator")
    results.extend([result_node_2, result_creator_2])
    # Change type of individual to its third layer subtypes
    graph.add.causal_node("node_3")
    res_node_3 = graph.edit.type_to_subtype(name_of_entity="node_3", new_type="MachineFault_Event")
    results.append(res_node_3)
    # Check results
    for result in results:
        assert result is True


def test_change_type_to_subtype_mult_inheritance(pizza_graph: Graph):
    """Test that changing types works for inherited types as well"""
    # Init pizza graph
    pizza_graph.add.individual_of_type("Margherita", "my_marga")
    pizza_graph.add.individual_of_type("Mushroom", "my_mush")
    # Edge makes the pizzas from type CausalNode as well
    pizza_graph.add.causal_edge("my_marga", "my_mush", "pizza_edge")
    # Change type of pizzas from CausalNode to something else
    assert pizza_graph.edit.type_to_subtype(name_of_entity="my_marga", new_type="State") is True
    assert pizza_graph.edit.type_to_subtype(name_of_entity="my_mush", new_type="Event") is True
    # Check if pizzas are still from type Pizza but now also "State" or "Event"
    my_marga = pizza_graph.get_entity("my_marga", True)
    assert str(my_marga.is_a) == "[pizza.Margherita, causalgraph.State]"
    my_mush = pizza_graph.get_entity("my_mush", True)
    assert str(my_mush.is_a) == "[pizza.Mushroom, causalgraph.Event]"


def test_change_type_to_subtype_type_not_allowed(graph: Graph):
    """Test that changing the type is not allowed if the new type
    is not a subtype of the old type"""
    graph.add.causal_node("node_1")
    # Try to change its type to something that is not allowed
    type_to_subtype_successful = graph.edit.type_to_subtype("node_1", "Creator")
    assert type_to_subtype_successful is False
    assert owlutils.is_instance_of_class("node_1", 'CausalNode', graph.store) is True
    assert owlutils.is_instance_of_class("node_1", 'Creator', graph.store) is False


def test_change_type_to_subtype_type_non_existing(graph: Graph):
    """Test that changing the type to a non-existing one does not work"""
    graph.add.causal_node("node_1")
    # Try to change its type to something that is not existing
    type_to_subtype_successful = graph.edit.type_to_subtype("node_1", "Some_Type")
    assert type_to_subtype_successful is False
    assert owlutils.is_instance_of_class("node_1", 'CausalNode', graph.store) is True


### Tests for Properties changes
"""Test that an individuals' properties can be edited"""
def test_properties_change_multiple_properties(graph: Graph):
    # Assert properties of edge 1
    edge_1 = get_entity_by_name('Edge 1', graph.store)
    assert edge_1.name == 'Edge 1'
    assert edge_1.hasCause[0] == get_entity_by_name('Node 1', graph.store)
    assert edge_1.hasEffect[0] == get_entity_by_name('Node 3', graph.store)
    assert edge_1.hasConfidence == 0.6
    assert edge_1.hasTimeLag == 3
    assert edge_1.comment == []
    # Change properties of edge 1
    prop_dict = {'hasConfidence': 0.3, 'hasTimeLag': 2, 'comment': 'This is edge 1!'}
    succ = graph.edit.properties('Edge 1', prop_dict)
    # Assert that properties have been changed
    edge_1 = get_entity_by_name('Edge 1', graph.store)
    assert succ is True
    assert edge_1.name == 'Edge 1'
    assert edge_1.hasCause[0] == get_entity_by_name('Node 1', graph.store)
    assert edge_1.hasEffect[0] == get_entity_by_name('Node 3', graph.store)
    assert edge_1.hasConfidence == 0.3
    assert edge_1.hasTimeLag == 2
    assert edge_1.comment[0] == 'This is edge 1!'


def test_properties_change_single_property(graph: Graph):
    """Test that a single property of an individual can be edited"""
    # Assert properties of edge 2
    edge_2 = get_entity_by_name('Edge 2', graph.store)
    assert len(edge_2.hasCreator) == 1
    assert edge_2.hasCreator[0] == get_entity_by_name('Creator1', graph.store)
    # Change property
    prop_dict = {'hasCreator': ['Creator2']}
    succ = graph.edit.properties('Edge 2', prop_dict)
    # Assert that property has changed
    edge_2 = get_entity_by_name('Edge 2', graph.store)
    assert succ is True
    assert len(edge_2.hasCreator) == 1
    assert edge_2.hasCreator[0] == get_entity_by_name('Creator2', graph.store)


def test_properties_delete_properties(graph: Graph):
    """Test that properties of an individual can be deleted"""
    # Assert properties of edge 3
    edge_3 = get_entity_by_name('Edge 3', graph.store)
    assert edge_3.hasConfidence == 0.6
    assert edge_3.hasTimeLag == 3
    assert edge_3.comment == []
    # Delete properties
    prop_dict = {'hasConfidence': None, 'hasTimeLag': None, 'comment': None}
    succ = graph.edit.properties('Edge 3', prop_dict)
    # Assert that properties have been deleted
    edge_3 = get_entity_by_name('Edge 3', graph.store)
    assert succ is True
    assert edge_3.hasConfidence is None
    assert edge_3.hasTimeLag is None
    assert edge_3.comment == []


def test_properties_wrong_data_type():
    # TODO Implement owlutils.validate_data_type_for_property and test
    pass


def test_properties_property_not_allowed(graph:Graph):
    """Test that only allowed properties can edited"""
    # Assert node_1 properties
    node_1 = get_entity_by_name('Node 1', graph.store)
    assert node_1.comment == []
    # Try to update properties
    prop_dict = {'comment': 'This is node 1!', 'hasConfidence': 0.4}
    succ = graph.edit.properties('Node 1', prop_dict)
    # Assert that update was not succesful because nodes
    # don't have a confidence value
    node_1 = get_entity_by_name('Node 1', graph.store)
    assert succ is False
    assert node_1.comment == []
    assert node_1.hasConfidence is None


def test_properties_individual_not_existing(graph: Graph):
    """Test that a property can bonly be updated if the individuals'
    name is completely correct"""
    # Assert property of edge 2
    edge_2 = get_entity_by_name('Edge 2', graph.store)
    assert edge_2.hasTimeLag == 3
    # Try to update edge 2 with wrong name
    prop_dict = {'hasTimeLag': 1}
    succ = graph.edit.properties('Edge2', prop_dict)
    # Assert that update not successful and value unchanged
    edge_2 = get_entity_by_name('Edge 2', graph.store)
    assert succ is False
    assert edge_2.hasTimeLag == 3


def test_property_change_single_property(graph: Graph):
    """Test that a single property can be edited"""
    # Assert edge 2 properties
    edge_2 = get_entity_by_name('Edge 2', graph.store)
    assert len(edge_2.hasCreator) == 1
    assert edge_2.hasCreator[0] == get_entity_by_name('Creator1', graph.store)
    # Change property
    succ = graph.edit.property('Edge 2', 'hasCreator', ['Creator2'])
    # Assert that change was successful
    edge_2 = get_entity_by_name('Edge 2', graph.store)
    assert succ is True
    assert len(edge_2.hasCreator) == 1
    assert edge_2.hasCreator[0] == get_entity_by_name('Creator2', graph.store)


def test_delete_property(graph: Graph):
    """Test that a single property can be deleted"""
    # Assert properties of edge 3
    edge_3 = get_entity_by_name('Edge 3', graph.store)
    assert edge_3.hasConfidence == 0.6
    assert edge_3.hasTimeLag == 3
    assert edge_3.comment == []
    # Delete hasConfidence
    succ_1 = graph.edit.property('Edge 3', 'hasConfidence', None)
    edge_3 = get_entity_by_name('Edge 3', graph.store)
    assert succ_1 is True
    assert edge_3.hasConfidence is None
    assert edge_3.hasTimeLag == 3
    assert edge_3.comment == []
    graph_dict = graph.map.all_individuals_to_dict()
    with pytest.raises(KeyError):
        graph_dict['edge_3.name']['confidence']


def test_description_change_description(graph: Graph):
    """Test that the comment of an individual can be edited"""
    # Create description for node 3
    node_3 = get_entity_by_name('Node 3', graph.store)
    assert node_3.comment == []
    succ = graph.edit.description('Node 3', 'This is node 3!')
    assert node_3.comment[0] == 'This is node 3!'
    # Change description and assert that change successful
    graph.edit.description('Node 3', 'New description!')
    node_3 = get_entity_by_name('Node 3', graph.store)
    assert succ is True
    assert node_3.comment[0] == 'New description!'
