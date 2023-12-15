#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/graph.py
"""

# general imports
import os
from pathlib import Path
import pytest
# causalgraph imports
from causalgraph import Graph
from causalgraph.utils import owlready2_utils as owl2utils
from deepdiff import DeepDiff
import numpy as np


########################################
###         Fixtures                 ###
########################################
@pytest.fixture(name= "testdata_dir")
def fixture_testdata_dir() -> Path:
    testdata_dir = Path(__file__).absolute().parent / 'testdata'
    return testdata_dir


@pytest.fixture(name= "sql_test_db")
def fixture_sql_test_db(tmpdir) -> str:
    test_db_relative_path = os.path.join(tmpdir, "test_db.sqlite3")
    return test_db_relative_path


@pytest.fixture(name= "test_graph")
def fixture_test_graph() -> Graph:
    test_graph = Graph(sql_db_filename=None, sql_exclusive=False)
    yield test_graph

@pytest.fixture(name="test_graph_simple")
def fixture_test_graph_simple() -> Graph:
    graph = Graph(sql_db_filename=None)
    # Init creators
    creator_node = graph.add.individual_of_type(class_of_individual="Creator",
                                                name_for_individual="master_creator",
                                                comment=["Creates everything"])
    # Add nodes
    graph.add.causal_node("node_1")
    graph.add.causal_node("node_2", comment=["node_2 comment"])
    graph.add.causal_node("node_3_c", hasCreator=[creator_node])
    # Add edges
    graph.add.causal_edge(cause_node="node_1",
                          effect_node="node_2",
                          name_for_edge="edge_1")
    graph.add.causal_edge(cause_node="node_2",
                          effect_node="node_3_c",
                          name_for_edge="edge_2_c",
                          confidence=1.0,
                          time_lag_s=5.0,
                          hasCreator=[creator_node],
                          comment=["edge_2c_comment"])
    graph.add.causal_edge(cause_node= "node_2",
                          effect_node= "node_3_c",
                          name_for_edge= "edge_3_c",
                          confidence=0.5,
                          time_lag_s=10.0,
                          hasCreator=[creator_node],
                          comment=["edge_3c_comment"])
    return graph

########################################
###              Tests               ###
########################################
## Test for constructors
def test_graph_constructor_empty():
    """Test graph constructor"""
    _ = Graph()


def test_graph_constructor_with_backend(sql_test_db):
    """Test graph constructor with database path"""
    _ = Graph(sql_db_filename=sql_test_db)


def test_graph_lock(sql_test_db):
    """Test that individuals are stored in the store"""
    graph_one = Graph(sql_db_filename=sql_test_db, sql_exclusive=False)
    # Add test node, save to disk, store number of individuals
    graph_one.add.causal_node("cause_test_node")
    individuals_count_g_one = len(list(graph_one.store.individuals()))
    graph_one.store.save()
    # Create new graph from same database and count individuals
    graph_two = Graph(sql_db_filename=sql_test_db, sql_exclusive=False)
    individuals_count_g_two = len(list(graph_two.store.individuals()))
    assert individuals_count_g_two > 0
    assert individuals_count_g_one == individuals_count_g_two


def test_graph_preserved_prefix_after_reload(sql_test_db):
    """Test that individuals still exist and have the same name (including
    prefix) when creating a new graph"""
    graph_one = Graph(sql_db_filename=sql_test_db, sql_exclusive=False)
    # Add test node, save to disk, copy individuals
    graph_one.add.causal_node("test_node")
    graph_one.add.causal_node("test_node2")
    individuals = str(list(graph_one.store.individuals()))
    graph_one.store.save()
    # Create new graph with same database path
    graph_two = Graph(sql_db_filename=sql_test_db, sql_exclusive=False)
    reloaded_individuals = str(list(graph_two.store.individuals()))
    assert individuals == reloaded_individuals


def test_graph_add_after_reload(sql_test_db):
    """Test that adding individuals after reloading the store works"""
    graph_one = Graph(sql_db_filename=sql_test_db, sql_exclusive=False)
    # Add test node, save to disk
    graph_one.add.causal_node("test_node")
    graph_one.store.save()
    # Create new graph and add another node
    graph_two = Graph(sql_db_filename=None, sql_exclusive=False)
    graph_two.add.causal_node("mayCauseError")


### Test for import of Ontologies
def test_import_ontology_from_file(test_graph: Graph, testdata_dir):
    """Test that an ontology can be imported from a file path"""
    pizza_onto_file = str(Path.joinpath(testdata_dir, 'pizza.owl'))
    test_graph.import_ontology(pizza_onto_file)
    assert "http://www.co-ode.org/ontologies/pizza/" in test_graph.store.ontologies.keys()


def test_import_ontology_from_file_error_caught(test_graph: Graph, testdata_dir):
    # Setup and test
    ttl_test_ontology_path = str(Path.joinpath(testdata_dir, 'causalgraph.ttl'))
    assert test_graph.import_ontology(ttl_test_ontology_path) is None


def test_import_ontology_from_url(test_graph: Graph):
    """Test that an ontology can be imported from a url"""
    pizza_onto_url = "https://protege.stanford.edu/ontologies/pizza/pizza.owl"
    test_graph.import_ontology(pizza_onto_url)
    assert "http://www.co-ode.org/ontologies/pizza/" in test_graph.store.ontologies.keys()


def test_import_ontology_from_wrong_url(test_graph: Graph):
    """Test that importing an ontology from a wrong url doesn't work"""
    random_url= "https://www.google.de"
    assert test_graph.import_ontology(random_url) is None


def test_import_same_ontology_twice(test_graph: Graph, testdata_dir):
    """Test that an ontology is imported only once"""
    pizza_onto_file = str(Path.joinpath(testdata_dir, 'pizza.owl'))
    num_ontos_start = len(test_graph.store.ontologies)
    # Test with import once -> check that 2 ontologies (URI and filepath)
    test_graph.import_ontology(pizza_onto_file)
    num_ontos_after_first_load = len(test_graph.store.ontologies)
    assert num_ontos_after_first_load == num_ontos_start + 2
    # Test with import twice -> check that no more ontologies were added
    test_graph.import_ontology(pizza_onto_file)
    num_ontos_after_second_load = len(test_graph.store.ontologies)
    assert num_ontos_after_first_load == num_ontos_after_second_load

def test_import_ontology_at_startup(testdata_dir: str):
    """Tests the import of ontologies when initializing a new Graph() object"""
    external_ontos = [f"{testdata_dir}/faults.owl", f"{testdata_dir}/error-db.owl", f"{testdata_dir}/pizza.owl"]
    G_new = Graph(
        sql_db_filename=None,
        external_ontos=external_ontos
    )
    assert G_new.map.third_party_data_properties != []
    assert G_new.map.third_party_object_properties != []

def test_init_graph_from_nx(test_graph_simple: Graph):
    """Tests the initialization of a new Graph() object from a passed NetworkX MultiDiGraph() object"""
    nx_graph = test_graph_simple.export.nx()
    G_new = Graph(
        sql_db_filename=None,
        external_graph=nx_graph
    )
    nx_graph_dict = G_new.map.graph_dict_from_nx(nx_graph)
    new_graph_dict = G_new.map.all_individuals_to_dict()
    diff = DeepDiff(nx_graph_dict, new_graph_dict, ignore_order=True)
    assert diff == {}

def test_init_graph_from_tigra(test_graph_simple: Graph):
    """Tests the initialization of a new Graph() object from a passed Tigramite graph representation"""
    node_names, edge_names, link_matrix, q_matrix, timestep_len_s = test_graph_simple.export.tigra()
    graph_simple_dict = test_graph_simple.map.all_individuals_to_dict()
    G_nx = Graph(
        sql_db_filename=None,
        external_graph=(node_names, edge_names, link_matrix, q_matrix, timestep_len_s)
    )
    tigra_graph_dict = G_nx.map.all_individuals_to_dict()
    for individual in graph_simple_dict:
        for prop in list(graph_simple_dict[individual]):
            if prop in (['comment', 'hasCreator']):
                graph_simple_dict[individual].pop(prop)
    diff = DeepDiff(tigra_graph_dict, graph_simple_dict, ignore_order=True)
    assert diff == {}

def test_init_graph_from_failed_tigra():
    """Tests the initialization of a new Graph() object from a passed Tigramite graph representation.
    This Tigramite Tuple should result in a empty Graph()."""
    node_names, edge_names, link_matrix, q_matrix, timestep_len_s = [], [], np.ndarray([1, 2, 3, 4]), np.ndarray([1, 2, 3, 4]), 1
    G_nx = Graph(
        sql_db_filename=None,
        external_graph=(node_names, edge_names, link_matrix, q_matrix, timestep_len_s)
    )
    tigra_graph_dict = G_nx.map.all_individuals_to_dict()
    assert tigra_graph_dict == {}

def test_init_graph_from_wrong_tigra_format():
    """Tests the initialization of a new Graph() object from a passed Tigramite graph representation.
    This Tigramite Tuple should result in a empty Graph()."""
    node_names, edge_names = [], []
    G_nx = Graph(
        sql_db_filename=None,
        external_graph=(node_names, edge_names)
    )
    tigra_graph_dict = G_nx.map.all_individuals_to_dict()
    assert tigra_graph_dict == {}

def test_init_graph_from_graph_format():
    """Tests the initialization of a new Graph() object from a wrong graph representation.
    This should result in a empty Graph()."""
    G_nx = Graph(
        sql_db_filename=None,
        external_graph=[1,2,3]
    )
    tigra_graph_dict = G_nx.map.all_individuals_to_dict()
    assert tigra_graph_dict == {}