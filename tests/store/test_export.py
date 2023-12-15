#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/store/export.py
"""

# general imports
from pathlib import Path
import pytest
import os
import numpy as np
from dowhy import CausalModel
import pandas as pd
from deepdiff import DeepDiff

# causalgraph imports
from causalgraph import Graph
import causalgraph.utils.owlready2_utils as owl2utils
from causalgraph.utils.owlready2_utils import is_subclass_of


########################################
###         Fixtures                 ###
########################################
@pytest.fixture(name="testdata_dir")
def fixture_testdata_dir() -> Path:
    testdata_dir = Path(__file__).absolute().parent.parent / 'testdata'
    return testdata_dir

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

@pytest.fixture(name="test_graph_third")
def fixture_test_graph_third(testdata_dir) -> Graph:
    external_ontos = [f"{testdata_dir}/faults.owl", f"{testdata_dir}/pizza.owl"]
    graph = Graph(sql_db_filename=None, external_ontos=external_ontos)
    graph.add.individual_of_type("Creator", name_for_individual='Creator_1')
    creator_1 = owl2utils.get_entity_by_name('Creator_1', graph.store)
    graph.add.individual_of_type("Mushroom", name_for_individual='Mushroom_1', hasCreator=[creator_1])
    graph.add.individual_of_type("Mushroom", name_for_individual='Mushroom_2')
    graph.add.causal_edge('Mushroom_1', 'Mushroom_2', "Mushroom_Edge", time_lag_s=2.2, comment=['test'])
    return graph


########################################
###              Tests               ###
########################################
def test__export_cg_simple_to_nx(test_graph_simple: Graph):
    """Testing exporting simple props cg graph to NetworkX"""
    G_nx = test_graph_simple.export.nx()
    graph_simple_dict = test_graph_simple.map.all_individuals_to_dict()
    nx_simple_dict = test_graph_simple.map.graph_dict_from_nx(G_nx)
    assert graph_simple_dict == nx_simple_dict

def test__export_cg_third_party_to_nx(test_graph_third: Graph):
    """Testing exporting third party props cg graph to NetworkX"""
    G_nx = test_graph_third.export.nx()
    graph_simple_dict = test_graph_third.map.all_individuals_to_dict()
    nx_simple_dict = test_graph_third.map.graph_dict_from_nx(G_nx)
    assert graph_simple_dict == nx_simple_dict

def test_export_cg_simple_to_tigra(test_graph_simple: Graph):
    """Testing exporting simple props cg graph to Tigramite"""
    node_names, edge_names, link_matrix, q_matrix, timestep_len_s = test_graph_simple.export.tigra()
    graph_simple_dict = test_graph_simple.map.all_individuals_to_dict()
    tigra_simple_dict = test_graph_simple.map.graph_dict_from_tigra(node_names, edge_names, link_matrix, q_matrix, timestep_len_s)
    # pop creator, iri and comment
    # because tigramite export cannot handle those
    for individual in graph_simple_dict:
        graph_simple_dict[individual].pop('iri')
        try:
            graph_simple_dict[individual].pop('hasCreator')
        except KeyError:
            pass
        try:
            graph_simple_dict[individual].pop('comment')
        except KeyError:
            pass
    diff = DeepDiff(graph_simple_dict, tigra_simple_dict, ignore_order=True)
    print(diff)
    assert graph_simple_dict == tigra_simple_dict

def test_export_cg_third_simple_to_tigra(test_graph_third: Graph):
    """Testing exporting third party props cg graph to Tigramite"""
    node_names, edge_names, link_matrix, q_matrix, timestep_len_s = test_graph_third.export.tigra()
    graph_simple_dict = test_graph_third.map.all_individuals_to_dict()
    tigra_simple_dict = test_graph_third.map.graph_dict_from_tigra(node_names, edge_names, link_matrix, q_matrix, timestep_len_s)
    # Adapt the original dict to only include the functionalites the tigra export can handle:
    for individual in list(graph_simple_dict):
        # Change all CausalNode / CausalEdge Subclasses to "CausalNode" / "CausalEdge"
        if any(is_subclass_of(type_, "CausalNode", test_graph_third.store) for type_ in graph_simple_dict[individual]["type"]):
            graph_simple_dict[individual]["type"] = ["CausalNode"]
        if any(is_subclass_of(type_, "CausalEdge", test_graph_third.store) for type_ in graph_simple_dict[individual]["type"]):
            graph_simple_dict[individual]["type"] = ["CausalEdge"]
        # pop creator, iri, comment and third party properties, because tigramite can export these
        for prop in list(graph_simple_dict[individual].keys()):
            if prop in (test_graph_third.map.third_party_data_properties + test_graph_third.map.third_party_object_properties + ['iri', 'hasCreator', 'comment']):
                graph_simple_dict[individual].pop(prop)
            if prop == 'hasTimeLag':
                # Fix time conversion losses
                graph_simple_dict[individual][prop] = float(round((graph_simple_dict[individual][prop])/timestep_len_s))
    diff = DeepDiff(graph_simple_dict, tigra_simple_dict, ignore_order=True)
    print(diff)
    assert diff == {}

def test_export_cg_simple_to_graphml(test_graph_simple: Graph, tmpdir: str):
    """Test that a cg graph can be exported as a graphml file"""
    test_graph_simple.export.graphml(tmpdir, 'graphml')
    exists = os.path.exists(f'{tmpdir}/graphml.graphml')
    os.remove(f'{tmpdir}/graphml.graphml')
    assert exists is True

def test_export_cg_gml(test_graph_simple: Graph, tmpdir: str):
    """Test that a cg graph can be exported as a gml file"""
    test_graph_simple.export.gml(tmpdir, 'gml')
    exists = os.path.exists(f'{tmpdir}/gml.gml')
    os.remove(f'{tmpdir}/gml.gml')
    assert exists is True

def test_export_cg_gml_input_working_dowhy(test_graph_simple: Graph, tmpdir: str):
    test_graph_simple.export.gml(tmpdir, 'gml')
    # Create artificial time series
    var_names = ['time_series1', 'time_series2', 'time_series3', 'time_series4']
    data = np.ones((100, 4)).T
    dataframe = pd.DataFrame(data, var_names)
    # Read graph from gml and create Causal model
    graph_str = open(f'{tmpdir}/gml.gml', 'r').read()
    os.remove(f'{tmpdir}/gml.gml')
    model = CausalModel(data= dataframe,
                        graph=graph_str,
                        treatment=['thorns_on_road'],
                        outcome=['bumpy_feeling'])
    msg = "Model to find the causal effect of treatment ['thorns_on_road'] on outcome ['bumpy_feeling']"
    print(model.summary())
    assert model.summary() == msg
