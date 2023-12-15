
# Change Log

All notable changes to this project will be documented in this file.

## [0.1.1] - 2023-12-15

### Added
- utility function to get edge by cause and effect (get_edge_by_cause_and_effect())
- CausalPresenceIndex as part of causalgraph.owl Ontology -> successor of "hasConfidence"

### Changed
- Removed unnecessary packages in requirements.txt and created seperate tests/requirements.txt
- Improved Performance and stability of get_name_and_object
- validation of properties now "False" as default 
- Made usage of log_file_handler optional (default: False) = No log file will be created
- Move Status messageges for init to debug

 
## [0.1.0] - 2023-07-10
 
### Added

- In-Memory storage as default, eliminating SQL requirement:
    - Previously, all causalgraph users were required to store data in a .sqlite database, which made fast (re-)creation of causalgraphs cumbersome.
    - he underlying package, owlready2, does not have this storage requirement and can now be initialized to store everything in memory.
    - Causalgraph users now have the option to choose "in-memory" storage as the default, with the storage in a SQL file being an alternative option.
- Improved Validation and Enhanced Clarity:
    - Identified and addressed flaws in the general validation of properties, resulting in failing tests.
    - Rewrote the function in `owlready2_utils.py` and incorporated the same functions for validation during the updating and creation of individuals.
    - Validation now includes checking the domain and range for known properties, excluding max and minimum boundaries. Unknown properties will not be checked and will not raise exceptions.

### Changed

- Enhanced usability py passing/returning entity objects:
    - Revised certain functions in the causalgraph packag e to return the actual object (e.g. node, edge) instead just its name
    - Improved usability by retrieving the object directly by default and allowing access to its name via `object.name`
- Bumped owlready2 version to 0.43

### Fixed


