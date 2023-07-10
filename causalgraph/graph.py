#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Module to store knowledge graphs and causal models.
    In the near future, this functionality will be extended with
    learning and inference on the Graph.

    graph.py contains the Graph base class and serves as the main class.
"""

# general imports
import os
import logging
from pathlib import Path
from typing import Tuple
import owlready2
# causalgraph imports
from causalgraph.store.add import Add
from causalgraph.store.edit import Edit
from causalgraph.utils.draw import Draw
from causalgraph.store.remove import Remove
from causalgraph.utils.mapping import Mapping
import causalgraph.utils.owlready2_utils as owlutils
from causalgraph.utils.logging_utils import init_logger
from causalgraph.utils.misc_utils import get_project_root
CAUSALGRAPH_ONTO_PATH: Path = Path.joinpath(get_project_root(), "data", 'causalgraph.owl')

from causalgraph.store.load import Load
from causalgraph.store.export import Export
from typing import Union
import networkx

class Graph():
    """ Graph with causal information embedded in knowledge graph.
    """
    def __init__(self, 
                sql_db_filename: str = None,
                sql_exclusive: bool = False,
                log_file_dir: str = None,
                logger_level: int = logging.WARNING,
                external_ontos: list[str] = None,
                external_graph: Union[networkx.MultiDiGraph, tuple] = None,
                validate_domain_range: bool = True
    ) -> None:
        """Instantiates a Graph as the central object of causalgraph.

        :param sql_db_filename: Optional path to a sqlite3-DB (path ending with .sqlite3) for storing the graph in a db. Set None for storing on memory, defaults to None
        :type sql_db_filename: str, optional
        :param sql_exclusive: if sql-db should be closed for parallel requests, defaults to False
        :type sql_exclusive: bool, optional
        :param log_file_dir: path to the log-file directory, defaults to '{project_root}/data/logs/cg.json'
        :type log_file_dir: str, optional
        :param logger_level: Verbosity level of logger
        :type logger_level: int
        :param external_ontos: List of local Paths to file or URL to ontology in web.
        :type external_ontos: list[str], optional
        :param external_graph: NetworkX.MultiDiGraph or Tigramite Graph representation.
        :type external_graph: Union[networkx.MultiDiGraph, Tuple(list, dict, ndarray, ndarray, int)], optional
        :param validate_domain_range: If True, all properties will be evaluated with domain and range before creating new individuals, defaults to True
        :type validate_domain_range: bool, optional
        """
        # Store attributes if necessary
        self.sql_db_filename = sql_db_filename
        self.core_onto_path = CAUSALGRAPH_ONTO_PATH.absolute()
        self.validate_domain_range = validate_domain_range
        # Check if necessary onto_file is present:
        if self.core_onto_path.is_file() is False:
            raise FileNotFoundError("The necessary base ontology 'causalgraph' was not found at " +
                                    f"expected location {self.core_onto_path}.")
        ## Initialize
        self.logger = init_logger(logger_name= "cg",
                                  file_handler_level=logging.DEBUG,
                                  console_handler_level=logger_level,
                                  file_handler=True,
                                  elastic_style_json=True,
                                  log_file_dir=log_file_dir)
        self.store = self._init_store_backend_sqldb(self.sql_db_filename, sql_exclusive)
        self.individuals_onto, self.classes_onto = self._init_namespaces(self.core_onto_path, self.store)
        # Include functionalities wrapped in singleton objects
        self.add = Add(store=self.store, logger=self.logger, validate_domain_range=self.validate_domain_range)
        self.edit = Edit(store=self.store, logger=self.logger, validate_domain_range=self.validate_domain_range)
        self.remove = Remove(store=self.store, logger=self.logger)
        self.map = Mapping(graph=self, logger=self.logger)
        self.export = Export(graph=self, logger=self.logger)
        self.load = Load(graph=self, logger=self.logger)
        self.draw = Draw(graph=self)
        # Check if there are third party ontos to be loaded directly at start
        if external_ontos is not None:
            for onto_path in external_ontos:
                self.import_ontology(onto_path)
        ### Check if external graph (nx or tigra) was passed
        if external_graph is not None:
            self._init_external_graph(external_graph)
        self.logger.info("Initialized the Causal Knowledge Graph.")

        
    def _init_external_graph(self, external_graph: Union[networkx.MultiDiGraph, tuple]):
        if type(external_graph) is networkx.MultiDiGraph:
            graph_dict = self.map.graph_dict_from_nx(external_graph)
            _ = self.map.fill_empty_graph_from_dict(graph_dict)
            graph_dict = self.map.all_individuals_to_dict()
            if graph_dict != {}:
                self.logger.info("Init by importing a MultiDiGraph has been successful.")
            else:
                self.logger.error("Importing the MultiDiGraph did not result in any instantiation of individuals in the new graph.")
        elif type(external_graph) in [tuple, Tuple]:
            if len(external_graph) == 5:
                graph_dict = self.map.graph_dict_from_tigra(
                    node_names=external_graph[0],
                    edge_names=external_graph[1],
                    link_matrix=external_graph[2],
                    q_matrix=external_graph[3],
                    timestep_len_s=external_graph[4])
                _ = self.map.fill_empty_graph_from_dict(graph_dict)
                graph_dict = self.map.all_individuals_to_dict()
                if graph_dict != {}:
                    self.logger.info("Init by importing a Tigramite Tuple has been successful.")
                else:
                    self.logger.error("Importing the Tigramite Tuple did not result in any instantiation of individuals in the new graph.")
            else:
                self.logger.error("Passed Tigramite Tuple has the wrong format. Please pass a Tuple with the Format " + 
                "(node_names, edge_names, link_matrix, q_matrix, timestep_len_s).")
        else:
            self.logger.error("Wrong external graph format. Please pass a MultiDiGraph or Tigramite Tuple. " + 
            "A empty causalgraph has been initialized.")


    def _init_store_backend_sqldb(self, sql_db_path: str, sql_exclusive: bool) -> owlready2.World:
        """Initializes the Graph store as an owlready2.World which stores data in a SQL-DB.

        Per default, the Store is persisted in a SQLite3 file, specified by sql_db_filepath.
        For multi-user_access to the SQL-DB, choose sql_exclusive= False.

        :param sql_db_path: Path to SQLite3 file for storing the graph
        :type sql_db_path: str
        :param sql_exclusive: Protect SQL from other users= exclusive, disable for multi-access
        :type sql_exclusive: bool
        :return: Graphstore Backend
        :rtype: owlready2.World
        """
        store = owlready2.World()
        if sql_db_path is None:
            self.logger.info(f"Using in memory ontology store. Graph will not be saved after stopping the program.")
            return store
        elif Path(sql_db_path).is_file():
            store.set_backend(filename=sql_db_path, exclusive=sql_exclusive)
            self.logger.warning(f"Using existing ontology store at {Path(sql_db_path).absolute()}")
        else:
            store.set_backend(filename=sql_db_path, exclusive=sql_exclusive)
            self.logger.info(f"Created empty ontology storage at {Path(sql_db_path).absolute()}")
        return store


    def _init_namespaces(self, core_onto_path: str, store: owlready2.World) -> Tuple[owlready2.Ontology, owlready2.Ontology]:
        """Initializes the two default namespaces in 'store':

        Namespace 'causalgraph_store'/'individuals_onto': for storing all individuals
        created during runtime
        Namespace '<core_onto_path>'/'classes_onto': for class definitions imported
        from 'core_onto_path'

        :param core_onto_path: Path to file, which is to be included in store.
        :type core_onto_path: str
        :param store: Selects the owlready2.World into which the ontology is loaded
        :type store: owlready2.World
        :raises ParsingError: Raises exception if Ontology can not be parsed. Only owl/xml can be parsed.
        :return: (individuals_onto: owlready2.Ontology, classes_onto: owlready2.Ontology)
        :rtype: Tuple[owlready2.Ontology, owlready2.Ontology]
        """
        # Load classes_onto from the core_onto_path
        store.classes_onto = self.import_ontology(core_onto_path)
        if store.classes_onto is None:
            raise LookupError("Could not load necessary ontology at '{core_onto_path}'.")
        # Attaches classes and individuals_onto to store and return
        store_namespace_uri = "cg_store"
        store.individuals_onto = store.get_ontology(store_namespace_uri)
        return store.individuals_onto, store.classes_onto


    def import_ontology(self, onto_file_path: str) -> owlready2.Ontology:
        """Imports the ontology from 'onto_file_path', can be a local path or an URL to an ontology.

        :param onto_file_path: Local Path to file or URL to ontology in web.
        :type onto_file_path: str
        :raises ParsingError: Raised, if ontology file is in an unexpected format
        :return: Pointer to Ontology (optional)
        :rtype: owlready2.Ontology
        """
        num_ontos_before_load = len(self.store.ontologies)
        # Check if 'onto_file_path' exists as file  and load ontology
        if Path(onto_file_path).is_file():
            try:
                onto = self.store.get_ontology(f"file://{onto_file_path}").load()
                success_log_text = f"Loaded Ontology '{onto.base_iri}' from file system. Path: '{onto_file_path}'"
            except owlready2.OwlReadyOntologyParsingError as _:
                self.logger.exception(f"Could not add Ontology by path '{onto_file_path}'. " +
                                       "Ontology could not be parsed. File needs to be in " +
                                       "owl/xml format. NO .ttl files allowed.")
                return None
        # Try to load from URL -> should raise default error?
        else:
            try:
                onto = self.store.get_ontology(str(onto_file_path)).load()
                success_log_text = f"Loaded Ontology '{onto.base_iri}' from URL: '{onto_file_path}'"
            except owlready2.OwlReadyOntologyParsingError as _:
                self.logger.exception(f"Couldn't add Ontology by URL {onto_file_path}. Ontology " +
                                      f"not found at URL {onto_file_path}. Returning none")
                return None
        # Logging based on additon of new onto or overwriting of existing ontology
        num_ontos_after_load = len(self.store.ontologies)
        if num_ontos_after_load == num_ontos_before_load:
            self.logger.warning("Overwrote ontology {onto.base_iri} with data from URL/file at " +
                                f"{onto_file_path}. Ontology already existed.")
        else:
            self.logger.info(success_log_text)
        try:
            self.map.update_third_party_properties()
        except AttributeError:
            pass
        return onto


    def get_entity(self, name_of_entity: str, suppress_warn=False) -> owlready2.EntityClass:
        """Returns an entity (class/property/individual) found under the given name.
        Returns none if no entity is found.

        :param name_of_entity: name of entity to search for
        :type name_of_entity: str
        :param suppress_warn: Define whether to suppress logging, defaults to False
        :type suppress_warn: bool, optional
        :raises ValueError: if unexpectedly found more than one possible entity.
        :return: Entity Object (class/property/individual)
        :rtype: owlready2.EntityClass
        """
        return owlutils.get_entity_by_name(name_of_entity, self.store, self.logger, suppress_warn)


    def delete(self):
        """ Deletes ressources created by the Graph """
        os.remove(self.sql_db_filename)
