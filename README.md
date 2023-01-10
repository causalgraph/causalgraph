
<!-- PROJECT SHIELDS -->
[![IWU][iwu-shield]](https://www.iwu.fraunhofer.de/)
[![Tests][pytest-shield]](https://github.com/causalgraph/causalgraph/actions)
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
    <a href="https://github.com/causalgraph/causalgraph/issues">Request Feature</a>
    ·
    <a href="https://github.com/causalgraph/causalgraph/issues">Report Bug</a>
    ·
    <a href="mailto:causalgraph@iwu.fraunhofer.de">Contact us</a>
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About the Project</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
    <li><a href="#similar-projects">Similar Projects</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About the Project

causalgraph - modeling and saving causal graphs embedded in knowledge graphs. The package has been designed to provide an interface between causal disciplines such as causal discovery and causal inference. With this package, users can create and save causal graphs and export the generated graphs for use in other graph-based packages. The main advantage of the proposed package is its ability to facilitate the linking of additional information and metadata to causal structures. In addition, the package offers a variety of functions for graph modeling and plotting, such as editing, adding, and deleting nodes and edges. It is also compatible with widely used graph data science libraries such as [NetworkX](https://github.com/networkx/networkx) and [Tigramite](https://github.com/jakobrunge/tigramite) and incorporates a specially developed causalgraph ontology in the background. 


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


<!-- USAGE EXAMPLES -->
## Usage

Please have a look at the examples folder at [/examples](./examples). Here you can find some Jupter notebooks in which the most important functions are presented. You can also take a look at the causalgraph paper. It is referenced in the end of this README.


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.


<!-- CONTACT -->
## Contact

- Mail: causalgraph@iwu.fraunhofer.de
- Blog: [https://www.kognitive-produktion.de/?p=3154](https://www.kognitive-produktion.de/?p=3154)
- Project Link: [https://github.com/causalgraph](https://github.com/causalgraph)


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

The development of causalgraph is part of the research project KausaLAssist. It is funded by the German Federal Ministry of Education and Research (BMBF) within the "Future of Value Creation - Research on Production, Services and Work" program (funding number 02P20A150) and managed by the Project Management Agency Karlsruhe (PTKA). The authors are responsible for the content of this publication.


## Similar Projects

- [owlready2](https://owlready2.readthedocs.io/en/v0.35/) - Makes Ontologies and Knowledge Graphs workable in python. Is used for storing information
- [networkX](https://networkx.org/) - Represent graphs in python; is used as inspiration for the Calls and structure of the project
- [Causal Graphical Models Python Package](https://github.com/ijmbarr/causalgraphicalmodels) - Major inspiration for this package, but we want to do these things differently:
  - Represent Nodes and Edges as individual objects, establishing the connection to datasources / models
  - usage of [networkX MultiDiGraph](https://networkx.org/documentation/stable/reference/classes/multidigraph.html) as base for the SCMs to support multiple connections (at different times) between nodes   
- [Causal Inference in Statistics](https://github.com/DataForScience/Causality/blob/master/CausalModel.py) - Python Code accompanying a book, which also implements SCMs (without Time-Series)


<!-- MARKDOWN LINKS & IMAGES -->
[iwu-shield]: https://img.shields.io/badge/Fraunhofer-IWU-179C7D?style=flat-square
[pytest-shield]: https://img.shields.io/github/actions/workflow/status/causalgraph/causalgraph/python-app.yml?style=flat-square
[mit-licence]: https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square
[pypi-version]: https://img.shields.io/pypi/v/causalgraph?style=flat-square
[python-version]: https://img.shields.io/pypi/pyversions/causalgraph?style=flat-square
[download-counter]: https://img.shields.io/pypi/dm/causalgraph?style=flat-square
