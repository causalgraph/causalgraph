

<!-- PROJECT SHIELDS -->
[![IWU][iwu-shield]](https://www.iwu.fraunhofer.de/)
[![Tests][pytest-shield]](https://github.com/svenpieper/causalgraph_t/actions)
[![License][mit-licence]](https://opensource.org/licenses/MIT)
[![PyPi][pypi-version]](https://pypi.org/project/causalgraph)
[![Python][python-version]](https://pypi.org/project/causalgraph)
[![Downloads][download-counter]](https://pypi.org/project/causalgraph)


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <img src="causalgraph_logo.png" alt="Logo" width="80" height="80">
  <h3 align="center">causalgraph</h3>
  <p align="center">
    A python package for modeling, persisting and visualizing causal graphs embedded in knowledge graphs.
    <br />
    <!--<a href="https://github.com/othneildrew/Best-README-Template"><strong>Explore the docs »</strong></a>
    <br />-->
    <br />
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Request Feature</a>
    ·
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Report Bug</a>
    ·
    <a href="mailto:causalgraph@iwu.fraunhofer.de">Contact us</a>
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

causalgraph - modeling and saving causal graphs embedded in knowledge graphs. The package has been designed to provide an interface between causal disciplines such as causal discovery and causal inference. With this package, users can create and save causal graphs and export the generated graphs for use in other graph-based packages. The main advantage of the proposed package is its ability to facilitate the linking of additional information and metadata to causal structures. In addition, the package offers a variety of functions for graph modeling and plotting, such as editing, adding, and deleting nodes and edges. It is also compatible with widely used graph data science libraries such as [NetworkX](https://github.com/networkx/networkx) and [Tigramite](https://github.com/jakobrunge/tigramite) and incorporates a specially developed causalgraph ontology in the background. 

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

You can either use the causalgraph source code directly, or install the python package using pip.

### Using pip
Just install causalgraph via pip running the following command:

```sh
pip install causalgraph
```

### Local source code

1. Clone the repo
    ```sh
    git clone https://github.com/causalgraph/causalgraph.git
    ```
2. Create conda environment
    ```sh
    conda env create -f environment.yml
    conda activate causalgraph
    ```
3. Ready to use causalgraph
    ```python
    import causalgraph
    ```



## Similar Projects

- [owlready2](https://owlready2.readthedocs.io/en/v0.35/) -> Makes Ontologies and Knowledge Graphs workable in python. Is used for storing information
- [networkX](https://networkx.org/) -> Represent graphs in python; is used as inspiration for the Calls and structure of the project
- [Causal Graphical Models Python Package](https://github.com/ijmbarr/causalgraphicalmodels) -> Major inspiration for this package, but we want to do these things differently:
  - Represent Nodes and Edges as individual objects, establishing the connection to datasources / models
  - usage of [networkX MultiDiGraph](https://networkx.org/documentation/stable/reference/classes/multidigraph.html) as base for the SCMs to support multiple connections (at different times) between nodes   
- [Causal Inference in Statistics](https://github.com/DataForScience/Causality/blob/master/CausalModel.py) -> Python Code accompanying a book, which also implements SCMs (without Time-Series)




<!-- MARKDOWN LINKS & IMAGES -->
[iwu-shield]: https://img.shields.io/badge/Fraunhofer-IWU-179C7D?style=flat-square
[pytest-shield]: https://img.shields.io/github/actions/workflow/status/svenpieper/causalgraph_t/python-app.yml?style=flat-square
[mit-licence]: https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square
[pypi-version]: https://img.shields.io/pypi/v/causalgraph?style=flat-square
[python-version]: https://img.shields.io/pypi/pyversions/causalgraph?style=flat-square
[download-counter]: https://img.shields.io/pypi/dm/causalgraph?style=flat-square
