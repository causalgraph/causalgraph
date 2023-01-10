#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

"""Testing causalgraph/utils/draw.py
"""

# general imports
import os
import pytest
# causalgraph imports
from causalgraph import Graph


########################################
###         Fixtures                 ###
########################################
# Temporary sql_db for every test
@pytest.fixture(name= "sql_test_db_path")
def fixture_sql_test_db_path(tmpdir) -> str:
    test_db_relative_path = os.path.join(tmpdir, "test_draw.sqlite3")
    yield test_db_relative_path
    os.remove(test_db_relative_path)


@pytest.fixture(name= "graph")
def ficture_graph(sql_test_db_path) -> Graph:
    graph = Graph(sql_db_filename=sql_test_db_path)
    yield graph
    graph.store.close()


########################################
###              Tests               ###
########################################
def test_draw_html_and_save_file(graph: Graph):
    """Test that plotting a cg graph in html and
    saving it works as intended"""
    # Add nodes and edges
    graph.add.causal_node("node_1")
    graph.add.causal_node("node_2")
    graph.add.causal_node("node_3")
    graph.add.causal_node("node_4")
    graph.add.causal_node("node_5")
    graph.add.causal_edge(cause_node_name= "node_1",
                          effect_node_name= "node_2",
                          name_for_edge= "edge_1")
    graph.add.causal_edge(cause_node_name= "node_2",
                          effect_node_name= "node_3",
                          name_for_edge= "edge_2",
                          confidence=0.2)
    graph.add.causal_edge(cause_node_name= "node_3",
                          effect_node_name= "node_4",
                          name_for_edge= "edge_3",
                          time_lag_s=1.5)
    graph.add.causal_edge(cause_node_name= "node_4",
                          effect_node_name= "node_5",
                          name_for_edge= "edge_4",
                          confidence=0.2,
                          time_lag_s=1.5)
    # Plot and save html file
    graph.draw.html(directory='.', filename='vis')
    # Check if plot image exists
    assert os.path.exists("vis.html")
    # Clean up by deleting plot image
    os.remove("vis.html")


def test_draw_nx_and_save_image(graph: Graph):
    """Test that plotting a cg graph in nx and
    exporting it as a png works as intended"""
    # Add nodes and edges
    graph.add.causal_node("node_1")
    graph.add.causal_node("node_2")
    graph.add.causal_node("node_3")
    graph.add.causal_node("node_4")
    graph.add.causal_node("node_5")
    graph.add.causal_edge(cause_node_name= "node_1",
                          effect_node_name= "node_2",
                          name_for_edge= "edge_1")
    graph.add.causal_edge(cause_node_name= "node_2",
                          effect_node_name= "node_3",
                          name_for_edge= "edge_2",
                          confidence= 0.2)
    graph.add.causal_edge(cause_node_name= "node_3",
                          effect_node_name= "node_4",
                          name_for_edge= "edge_3",
                          time_lag_s= 1.5)
    graph.add.causal_edge(cause_node_name= "node_4",
                          effect_node_name= "node_5",
                          name_for_edge= "edge_4",
                          confidence= 0.2,
                          time_lag_s= 1.5)
    # Plot and save image
    graph.draw.nx(directory='./', filename="nx")
    # Check if plot image exists
    assert os.path.isfile("nx.png")
    # Clean up by deleting plot image
    os.remove("nx.png")
