# CircuitOps tables generator through Tcl API

> xlindo

A slightly modified CircuitOps tables generator based on [NVlabs/CircuitOps](https://github.com/NVlabs/CircuitOps), which can be used for [The-OpenROAD-Project/OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts), especially for `.odb`.

## Usage

1. `cd` to root dir, i.e. `circuitops_manager`
2. `openroad src/tcl/generate_tables.tcl`
    * `ORFS_FLOW_DIR`, the path to `OpenROAD-flow-scripts/flowOpenROAD-flow-scripts/flow`
    * `DESIGN_NAME`, e.g. `gcd`, `ibex`
    * CUSTOM PART 2.1 **OR** 2.2
      * 2.1, from final results
      * 2.2, for intermediate results from `.odb`
3. Check the output circuitops tables at `output/IRs`

## Author

* [https://github.com/NVlabs/CircuitOps](https://github.com/NVlabs/CircuitOps)
* [https://xlindo.com](https://xlindo.com) from 2024.11

## License

Apache-2.0 license
