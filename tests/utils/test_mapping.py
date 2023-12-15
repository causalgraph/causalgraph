#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/utils/mapping.py
"""

# general imports
from pathlib import Path
import pytest
# causalgraph imports
from causalgraph import Graph
import causalgraph.utils.owlready2_utils as owl2utils


########################################
###         Fixtures                 ###
########################################
@pytest.fixture(name="testdata_dir")
def fixture_testdata_dir() -> Path:
    testdata_dir = Path(__file__).absolute().parent.parent / 'testdata'
    return testdata_dir

@pytest.fixture(name="empty_graph")
def fixture_empty_graph() -> Graph:
    graph = Graph(sql_db_filename=None)
    return graph

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
def test_update_third_party_props(empty_graph: Graph, testdata_dir: str):
    """Testing updating the third party prop lists after importing new ontologies. The function 
    mapping.update_third_party_properties() will be tested via the G.import_ontology() function"""
    data_props_cg_old = [x for x in empty_graph.map.causalgraph_data_properties]
    obje_props_cg_old = [x for x in empty_graph.map.causalgraph_object_properties]
    data_props_tp_old = [x for x in empty_graph.map.third_party_data_properties]
    obje_props_tp_old = [x for x in empty_graph.map.third_party_object_properties]

    empty_graph.import_ontology(f"{testdata_dir}/faults.owl")

    data_props_cg_new = empty_graph.map.causalgraph_data_properties
    obje_props_cg_new = empty_graph.map.causalgraph_object_properties
    data_props_tp_new = empty_graph.map.third_party_data_properties
    obje_props_tp_new = empty_graph.map.third_party_object_properties

    assert data_props_cg_old == data_props_cg_new
    assert obje_props_cg_old == obje_props_cg_new
    assert data_props_tp_old != data_props_tp_new
    assert obje_props_tp_old != obje_props_tp_new

def test_generate_props_dict_whole_graph(test_graph_simple: Graph):
    graph_dict_generated = test_graph_simple.map.all_individuals_to_dict()
    graph_dict_true = {
        "node_1":{"type":['CausalNode'],"iri":"cg_store#node_1","isCausing":["edge_1"]},
        "node_2":{"type":['CausalNode'],"iri":"cg_store#node_2","isCausing":["edge_2_c","edge_3_c"],"comment":["node_2 comment"],"isAffectedBy":["edge_1"]},
        "node_3_c":{"type":['CausalNode'],"iri":"cg_store#node_3_c","hasCreator":["master_creator"],"isAffectedBy":["edge_2_c","edge_3_c"]},
        "edge_1":{"type":['CausalEdge'],"iri":"cg_store#edge_1","hasEffect":"node_2","hasCause":"node_1"},
        "edge_2_c":{"type":['CausalEdge'],"iri":"cg_store#edge_2_c","hasConfidence":1.0,"hasTimeLag":5.0,"hasCause":"node_2","comment":["edge_2c_comment"],"hasCreator":["master_creator"],"hasEffect":"node_3_c"},
        "edge_3_c":{"type":['CausalEdge'],"iri":"cg_store#edge_3_c","hasConfidence":0.5,"hasTimeLag":10.0,"hasCause":"node_2","comment":["edge_3c_comment"],"hasCreator":["master_creator"],"hasEffect":"node_3_c"}
    }
    assert graph_dict_generated == graph_dict_true


def test_generate_props_dict_whole_graph_third_party(test_graph_third: Graph):
    graph_dict_generated = test_graph_third.map.all_individuals_to_dict()
    graph_dict_true = {
        'Mushroom_1':{"type":['Mushroom', 'CausalNode'],"iri":"cg_store#Mushroom_1","isCausing":["Mushroom_Edge"],"hasCreator":["Creator_1"]},
        "Mushroom_2":{"type":['Mushroom', 'CausalNode'],"iri":"cg_store#Mushroom_2","isAffectedBy":["Mushroom_Edge","Mushroom_2_9801_Edge"]},
        "9801":{"type":['Error'],"iri":"cg_store#9801","apiUrl":"http://localhost:8080/db/Errors/9801","errorCode":'9801',"message":"Fehlertext asdf asdf","hasCreator":["Creator_1"],"isCausing":["Error_Edge","Mushroom_2_9801_Edge"],"hasEnvironment":"environment_1"},
        "5800":{"type":['Error'],"iri":"cg_store#5800","apiUrl":"http://localhost:8080/db/Errors/5800","errorCode":'5800',"comment":["test comment"],"isAffectedBy":["Error_Edge"],"message":"asdf"},
        "Error_Edge":{"type":['CausalEdge'],"iri":"cg_store#Error_Edge","hasConfidence":0.9,"hasEffect":"5800","hasCreator":["Creator_1"],"hasCause":"9801"},
        "Mushroom_Edge":{"type":['CausalEdge'],"iri":"cg_store#Mushroom_Edge","hasTimeLag":2.2,"comment":["test"],"hasEffect":"Mushroom_2","hasCause":"Mushroom_1"},
        "Mushroom_2_9801_Edge":{"type":['CausalEdge'],"iri":"cg_store#Mushroom_2_9801_Edge","hasTimeLag":2,"hasEffect":"Mushroom_2","hasCause":"9801"}
    }
    assert graph_dict_generated == graph_dict_true

def test_generate_props_dict_wrong_prop(test_graph_simple: Graph, test_graph_third: Graph):
    individual = owl2utils.get_entity_by_name(name_of_entity='9801', store=test_graph_third.store)
    with pytest.raises(ValueError):
        prop_dict = test_graph_simple.map._Mapping__create_prop_dict_from_individual(individual=individual)

def test_generate_props_dict_from_nx(test_graph_simple: Graph):
    G_nx = test_graph_simple.export.nx()
    graph_dict_generated = test_graph_simple.map.graph_dict_from_nx(G_nx)
    graph_dict_true = {
        "node_1":{"type":['CausalNode'],"iri":"cg_store#node_1","isCausing":["edge_1"]},
        "node_2":{"type":['CausalNode'],"iri":"cg_store#node_2","isAffectedBy":["edge_1"],"isCausing":["edge_2_c","edge_3_c"],"comment":["node_2 comment"]},
        "node_3_c":{"type":['CausalNode'],"iri":"cg_store#node_3_c","hasCreator":["master_creator"],"isAffectedBy":["edge_2_c","edge_3_c"]},
        "edge_1":{"type":['CausalEdge'],"iri":"cg_store#edge_1","hasCause":"node_1","hasEffect":"node_2"},
        "edge_2_c":{"type":['CausalEdge'],"iri":"cg_store#edge_2_c","hasCreator":["master_creator"],"hasEffect":"node_3_c","hasConfidence":1.0,"comment":["edge_2c_comment"],"hasTimeLag":5,"hasCause":"node_2"},
        "edge_3_c":{"type":['CausalEdge'],"iri":"cg_store#edge_3_c","hasCreator":["master_creator"],"hasEffect":"node_3_c","hasConfidence":0.5,"comment":["edge_3c_comment"],"hasTimeLag":10,"hasCause":"node_2"}
    }
    assert graph_dict_true == graph_dict_generated

def test_generate_props_dict_from_tigra(test_graph_simple: Graph):
    # iri, creator and comments won't appear in dict
    node_names, edge_names, link_matrix, q_matrix, timestep_len_s = test_graph_simple.export.tigra()
    graph_dict_generated = test_graph_simple.map.graph_dict_from_tigra(node_names, edge_names, link_matrix, q_matrix, timestep_len_s)
    graph_dict_true= {
        "node_1":{"type":['CausalNode'],"isCausing":["edge_1"]},
        "node_2":{"type":['CausalNode'],"isAffectedBy":["edge_1"],"isCausing":["edge_2_c","edge_3_c"]},
        "node_3_c":{"type":['CausalNode'],"isAffectedBy":["edge_2_c","edge_3_c"]},
        "edge_1":{"hasCause":"node_1","hasEffect":"node_2","type":['CausalEdge']},
        "edge_2_c":{"hasCause":"node_2","hasConfidence":1.0,"hasEffect":"node_3_c","hasTimeLag":5.0,"type":['CausalEdge']},
        "edge_3_c":{"hasCause":"node_2","hasConfidence":0.5,"hasEffect":"node_3_c","hasTimeLag":10.0,"type":['CausalEdge']}
    }
    assert graph_dict_true == graph_dict_generated

def test_fill_empty_graph_from_dict(empty_graph: Graph, test_graph_simple: Graph):
    graph_dict_prefilled_graph = test_graph_simple.map.all_individuals_to_dict()
    print(list(test_graph_simple.store.individuals()))
    empty_graph = empty_graph.map.fill_empty_graph_from_dict(graph_dict_prefilled_graph)
    print(list(empty_graph.store.individuals()))
    graph_dict_empty_graph_filled = empty_graph.map.all_individuals_to_dict()
    assert graph_dict_prefilled_graph == graph_dict_empty_graph_filled
