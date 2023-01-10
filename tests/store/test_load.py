#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/store/load.py
"""

# general imports
from pathlib import Path
import pytest
# causalgraph imports
from causalgraph import Graph
import causalgraph.utils.owlready2_utils as owl2utils
from deepdiff import DeepDiff

########################################
###         Fixtures                 ###
########################################
@pytest.fixture(name="testdata_dir")
def fixture_testdata_dir() -> Path:
    testdata_dir = Path(__file__).absolute().parent.parent / 'testdata'
    return testdata_dir

@pytest.fixture(name="test_graph_simple")
def fixture_test_graph_simple(tmpdir) -> Graph:
    graph = Graph(sql_db_filename=f'{tmpdir}/simple.sqlite3')
    # Init creators
    creator_name = graph.add.individual_of_type(class_of_individual="Creator",
                                                name_for_individual="master_creator",
                                                comment=["Creates everything"])
    creator_node = owl2utils.get_entity_by_name(creator_name, graph.store)
    # Add nodes
    graph.add.causal_node("node_1")
    graph.add.causal_node("node_2", comment=["node_2 comment"])
    graph.add.causal_node("node_3_c", hasCreator=[creator_node])
    # Add edges
    graph.add.causal_edge(cause_node_name="node_1",
                          effect_node_name="node_2",
                          name_for_edge="edge_1")
    graph.add.causal_edge(cause_node_name="node_2",
                          effect_node_name="node_3_c",
                          name_for_edge="edge_2_c",
                          confidence=1.0,
                          time_lag_s=5.0,
                          hasCreator=[creator_node],
                          comment=["edge_2c_comment"])
    graph.add.causal_edge(cause_node_name= "node_2",
                          effect_node_name= "node_3_c",
                          name_for_edge= "edge_3_c",
                          confidence=0.5,
                          time_lag_s=10.0,
                          hasCreator=[creator_node],
                          comment=["edge_3c_comment"])
    return graph

@pytest.fixture(name="test_graph_third")
def fixture_test_graph_third(tmpdir, testdata_dir) -> Graph:
    external_ontos = [f"{testdata_dir}/faults.owl", f"{testdata_dir}/error-db.owl", f"{testdata_dir}/pizza.owl"]
    graph = Graph(sql_db_filename=f'{tmpdir}/third.sqlite3', external_ontos=external_ontos)
    owl2utils.create_individual_of_type("Creator", store=graph.store, name_for_individual='Creator_1')
    creator_1 = owl2utils.get_entity_by_name('Creator_1', graph.store)
    owl2utils.create_individual_of_type("Environment", store=graph.store, name_for_individual='environment_1')
    environment_1 = owl2utils.get_entity_by_name('environment_1', graph.store)
    owl2utils.create_individual_of_type("Mushroom", store=graph.store, name_for_individual='Mushroom_1', hasCreator=[creator_1])
    owl2utils.create_individual_of_type("Mushroom", store=graph.store, name_for_individual='Mushroom_2')
    owl2utils.create_individual_of_type("Error", store=graph.store, name_for_individual='9801', hasEnvironment=environment_1, hasCreator=[creator_1], errorCode=9801, apiUrl='http://localhost:8080/db/Errors/9801', message='Fehlertext asdf asdf')
    owl2utils.create_individual_of_type("Error", store=graph.store, name_for_individual='5800', errorCode=5800, apiUrl='http://localhost:8080/db/Errors/5800', message='asdf', comment=['test comment'])
    graph.add.causal_edge(9801, 5800, "Error_Edge", hasCreator=[creator_1], confidence=0.9)
    graph.add.causal_edge('Mushroom_1', 'Mushroom_2', "Mushroom_Edge", time_lag_s=4.0, comment=['test'])
    graph.add.causal_edge(9801, 'Mushroom_2', "Mushroom_2_9801_Edge", time_lag_s=2.0)
    return graph


########################################
###              Tests               ###
########################################
def test_load_simple_nx_to_cg(test_graph_simple: Graph, tmpdir: str):
    """Testing creating new Graph() by importing nx graph with standard props"""
    nx_graph = test_graph_simple.export.nx()
    G_new = test_graph_simple.load.nx(nx_graph=nx_graph, sql_db_filename=f'{tmpdir}/G_new_nx_s.sqlite3')
    old_graph_dict = test_graph_simple.map.all_individuals_to_dict()
    new_graph_dict = G_new.map.all_individuals_to_dict()
    diff = DeepDiff(old_graph_dict, new_graph_dict, ignore_order=True)
    assert diff == {}

def test_load_third_nx_to_cg_right_ontos(test_graph_third: Graph, tmpdir: str, testdata_dir: str):
    """Testing creating new Graph() by importing nx graph with third party props"""
    nx_graph = test_graph_third.export.nx()
    external_ontos = [f"{testdata_dir}/faults.owl", f"{testdata_dir}/error-db.owl", f"{testdata_dir}/pizza.owl"]
    G_new = test_graph_third.load.nx(nx_graph=nx_graph, sql_db_filename=f'{tmpdir}/G_new_nx_t_r.sqlite3', external_ontos=external_ontos)
    old_graph_dict = test_graph_third.map.all_individuals_to_dict()
    new_graph_dict = G_new.map.all_individuals_to_dict()
    diff = DeepDiff(old_graph_dict, new_graph_dict, ignore_order=True)
    assert diff == {}

def test_load_third_nx_to_cg_missing_ontos(test_graph_third: Graph, tmpdir: str):
    """Testing creating new Graph() by importing nx graph with third party props"""
    nx_graph = test_graph_third.export.nx()
    G_new = test_graph_third.load.nx(nx_graph=nx_graph, sql_db_filename=f'{tmpdir}/G_new_nx_t_w.sqlite3', external_ontos=[])
    old_graph_dict = test_graph_third.map.all_individuals_to_dict()
    new_graph_dict = G_new.map.all_individuals_to_dict()
    # Should not be equal, because load.nx() skipped unknown/missing properties
    diff = DeepDiff(old_graph_dict, new_graph_dict, ignore_order=True)
    assert diff != {}
    # Remove third party props from old_graph_dict
    third_party_props = test_graph_third.map.third_party_data_properties + test_graph_third.map.third_party_object_properties
    for individual in old_graph_dict:
        for prop in list(old_graph_dict[individual]):
            if prop in third_party_props:
                old_graph_dict[individual].pop(prop)
    # Should be equal by now
    diff = DeepDiff(old_graph_dict, new_graph_dict, ignore_order=True)
    assert diff == {}

def test_load_tigra_to_cg(test_graph_simple: Graph, tmpdir: str):
    """Testing creating new Graph() by importing tigramite graph with standard props"""
    node_names, edge_names, link_matrix, q_matrix, timestep_len_s = test_graph_simple.export.tigra()
    G_new = test_graph_simple.load.tigra(node_names, edge_names, link_matrix, q_matrix, timestep_len_s, sql_db_filename=f'{tmpdir}/G_new_tigra_s.sqlite3')
    old_graph_dict = test_graph_simple.map.all_individuals_to_dict()
    new_graph_dict = G_new.map.all_individuals_to_dict()
    # Remove properties tigramite cannot handle
    for individual in old_graph_dict:
        for prop in list(old_graph_dict[individual]):
            if prop in ['comment', 'hasCreator']:
                old_graph_dict[individual].pop(prop)
    # Should be equal by now
    diff = DeepDiff(old_graph_dict, new_graph_dict, ignore_order=True)
    assert diff == {}

def test_load_tigra_to_cg_third_party_props(test_graph_third: Graph, tmpdir: str):
    """"""
    node_names, edge_names, link_matrix, q_matrix, timestep_len_s = test_graph_third.export.tigra()
    G_new = test_graph_third.load.tigra(node_names, edge_names, link_matrix, q_matrix, timestep_len_s, sql_db_filename=f'{tmpdir}/G_new_tigra_t.sqlite3')
    old_graph_dict = test_graph_third.map.all_individuals_to_dict()
    new_graph_dict = G_new.map.all_individuals_to_dict()
    diff = DeepDiff(old_graph_dict, new_graph_dict, ignore_order=True)
    assert diff != {}
    third_party_props = test_graph_third.map.third_party_data_properties + test_graph_third.map.third_party_object_properties
    # Remove properties tigramite cannot handle
    for individual in old_graph_dict:
        for prop in list(old_graph_dict[individual]):
            if prop in (['comment', 'hasCreator'] + third_party_props):
                old_graph_dict[individual].pop(prop)
    # Should be equal by now
    diff = DeepDiff(old_graph_dict, new_graph_dict, ignore_order=True)
    assert diff == {}