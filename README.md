# CircuitOps Manager

> xlindo

Out-of-the-box python package for [CircuitOps](https://github.com/NVlabs/CircuitOps) and [The-OpenROAD-Project/OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts).

## Prerequistes

* Results from `OpenROAD-flow-scripts`
* Python packages
    * `graph_tool`
    * `pandas`
    * `numpy`

## Usage

1. Generate CircuitOps tables using revised Tcl scripts at [src/tcl/README.md](src/tcl/README.md)
2. See the example at [Random forest for net delay estimation use CircuitOps Manager](examples/RF_for_net_delay_estimation.ipynb)
    * Use `circuitops_helper` to parse tabels and generate nodes/edges
    * Use `circuitops_manager` to manage the graph

Tips, you may need platform resources, e.g. ASAP7, which you can clone by `git submodule update --init` to [design_resource/asap7](design_resource/asap7/).

## Authors

* [https://github.com/NVlabs/CircuitOps](https://github.com/NVlabs/CircuitOps)
* [https://xlindo.com](https://xlindo.com) from 2024.11

## License

Apache-2.0 license
