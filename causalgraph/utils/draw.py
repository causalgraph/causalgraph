#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains Draw class to visualize graphs.
"""

# general imports
import networkx as nx
import matplotlib.pyplot as plt


class Draw():
    """ This Class contains all methods for drawing graphs. There are multiple methods
    to draw a graph e.g. with nx or neo4j.
    """

    def __init__(self, graph) -> None:
        """Instantiates the Draw() class.

        :param graph: A causalgraph.Graph object
        :type graph: causalgraph.Graph
        """
        self.graph = graph

    def nx(self, directory: str=None, filename: str=None) -> None:
        """Plots the graph with NetworkX methods. Parse a directory to save
        the plot as an image with a specific filename. By default, a plot of the whole graph will be generated, unless
        you parse another graph_dict explicitly.

        :param directory: Directory where the plot should be saved, defaults to None
        :type directory: str, optional
        :param filename: Filename of the .png to be created, defaults to None
        :type filename: str, optional
        :param graph_dict: A properties dict that describes a graph with its nodes, edges and creators, defaults to None
        :type graph_dict: dict, optional
        """
        graph_dict = self.graph.map.all_individuals_to_dict()
        G_nx = self.graph.export.nx()
        edge_labels = {}
        # Get edge labels and fill dict edge_labels with them
        for individual in graph_dict:
            individual_type = graph_dict[individual]["type"]
            if individual_type == "CausalEdge":
                cause = graph_dict[individual].get("hasCause", [None])[0]
                effect = graph_dict[individual].get("hasEffect", [None])[0]
                timelag = graph_dict[individual].get("hasTimeLag", None)
                confidence = graph_dict[individual].get("hasConfidence", None)
                # Append to edge_labels dict
                if confidence is None and timelag is not None:
                    edge_labels[(cause, effect)] = f"Timelag: {timelag}"
                if confidence is not None and timelag is None:
                    edge_labels[(cause, effect)] = f"Confidence: {confidence}"
                if confidence is not None and timelag is not None:
                    edge_labels[(cause, effect)] = f"Timelag: {timelag}\nConfidence: {confidence}"
        # Create plot
        pos = nx.spring_layout(G_nx, k=2, seed=5)
        plt.figure()
        nx.draw(G= G_nx, pos= pos, with_labels= True, node_size= 2000, node_color= '#6fd0a7',font_size= 9)
        nx.draw_networkx_edge_labels(G=G_nx, pos=pos, edge_labels=edge_labels, font_color='#121212', font_size=7)
        plt.axis('off')
        axis = plt.gca()
        axis.set_xlim([1.1*x for x in axis.get_xlim()])
        axis.set_ylim([1.1*y for y in axis.get_ylim()])
        # Show figure or save plot as file
        if directory is not None and filename is not None:
            plt.savefig(f'{directory}/{filename}.png', dpi=200)
            print(f"Plot '{filename}.png' saved at {directory}.")
            plt.close()
            return
        plt.show()


    def html(self, directory: str, filename: str, directed: bool=True, graph_dict: dict=None) -> None:
        """Generates a .html-file which shows all nodes and edges incl. their properties
        as an interactive graph. This file can be openend by every browser with JS. By
        default, a plot of the whole graph will be generated, unless you parse another
        graph_dict explicitly.

        :param directory: Directory where the .html-file will be saved.
        :type directory: str
        :param filename: Filename of the .html-file to be created.
        :type filename: str
        :param graph_dict: Properties dict that describes a graph with its nodes, edges
        and creators, defaults to None
        :type graph_dict: dict, optional
        """

        # If graph_dict hasn't been parsed, just create it for the whole graph.
        if graph_dict is None:
            #graph_dict = all_individuals_to_dict(self.graph.store)
            graph_dict = self.graph.map.all_individuals_to_dict()

        nodes_html = []
        edges_html = []
        for individual in graph_dict:
            individual_name = individual
            individual_type = graph_dict[individual]["type"]
            if "CausalNode" in individual_type:
                # Generate node dict for visjs
                node = {'id': individual_name, 'label': individual_name, 'type': 'node', 'color': '#6fd0a7'}
                try:
                    message = graph_dict[individual]['message']
                    errorCode = graph_dict[individual]['errorCode']
                    node['title']=f"{message}|{errorCode}"
                except KeyError:
                    pass
                # Append to html nodes list
                nodes_html.append(node)
            if individual_type == "CausalEdge":
                edge = None
                cause = graph_dict[individual].get("hasCause", [None])[0]
                effect = graph_dict[individual].get("hasEffect", [None])[0]
                timelag = graph_dict[individual].get("hasTimeLag", None)
                confidence = graph_dict[individual].get("hasConfidence", None)
                if ((cause and effect) is not None) and ((confidence and timelag) is None):
                    edge  = {'from': cause,'to': effect}
                if ((cause and effect and confidence) is not None) and (timelag is None):
                    edge  = {'from': cause,'to': effect,'label':f"Confidence: {confidence}"}
                if ((cause and effect and timelag) is not None) and (confidence is None):
                    edge  = {'from': cause,'to': effect,'label':f"Timelag: {timelag}"}
                if (cause and effect and timelag and confidence) is not None:
                    edge  = {'from': cause,'to': effect,'label':f"Timelag: {timelag}\nConfidence: {confidence}"}
                edges_html.append(edge)
            #if individual_type == "Creator":
            #    creator = {'id': individual_name, 'label': individual_name, 'type': 'creator', 'color': '#f9cbb6'}
            #    created_by_node = []
            #    for node in graph_dict[individual].get("created", [None]):
            #        if node is not None:
            #            edge = {'from': individual_name,'to': node,'label':f"created"}
            #            edges_html.append(edge)
            #    nodes_html.append(creator)

        html  = f"""
            <html lang="en">
            <head>
                <title>Network</title>
                <script
                type="text/javascript"
                src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"
                ></script>
                <style type="text/css">
                #mynetwork {{
                    width: 100%;
                    height: 100vh;
                }}
                </style>
            </head>
            <body>
                <div id="mynetwork"></div>
                <script type="text/javascript">
                // create an array with nodes
                var nodes_data = new vis.DataSet(
                    {nodes_html}
                );
                // create an array with edges
                var edges_data = new vis.DataSet(
                    {edges_html}
                );
                // create a network
                var container = document.getElementById("mynetwork");
                var data = {{
                    nodes: nodes_data,
                    edges: edges_data,
                }};
                var options = {{
                    nodes: {{
                        font: {{ color: 'black',size: 14 }},
                        size: 25,
                        shape: 'circle',
                        widthConstraint: 60
                        }},
                    edges: {{
                        arrows: {{
                            to: {{enabled: true, scaleFactor: 0.5}}
                        }},
                        color: {{
                            color:'grey',
                            highlight:'red',
                            hover: '#d3d2cd',
                            inherit: false,
                            opacity:1.0
                        }},
                        font: {{size: 14, align: 'middle'}},
                        "length": 250,
                        "width": 1,
                        }},
                    layout: {{
                        hierarchical: {{
                            enabled: {str.lower(str(directed))},
                            direction: 'UD',
                            sortMethod: 'directed'
                            }},
                    }},
                }};
                var network = new vis.Network(container, data, options);
                </script>
            </body>
            </html>
        """
        file = open(f"{directory}/{filename}.html", "w")
        print(f"HTML-file '{filename}.html' saved at {directory}.")
        file.write(html)
        file.close()
