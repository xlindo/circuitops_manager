import os
import pandas as pd
from collections import defaultdict


class CircuitOpsDir:
    def __init__(self, CircuitOps_dir, design, tech, odb=""):
        ### SET DESIGN ###
        self.DESIGN_NAME = design

        ### SET PLATFORM ###
        self.PLATFORM = tech

        ### INTERNAL DEFINTIONS: DO NOT MODIFY BELOW ####
        self.CIRCUIT_OPS_DIR = CircuitOps_dir
        self.DESIGN_DIR = (
            self.CIRCUIT_OPS_DIR
            + "/designs/"
            + self.PLATFORM
            + "/"
            + self.DESIGN_NAME
            + "/base/"
        )
        self.PLATFORM_DIR = self.CIRCUIT_OPS_DIR + "/platforms/" + self.PLATFORM
        self.RCX_RULE = (
            self.CIRCUIT_OPS_DIR + "/platforms/" + self.PLATFORM + "/rcx_patterns.rules"
        )
        self.SETRC_FILE = (
            self.CIRCUIT_OPS_DIR + "/platforms/" + self.PLATFORM + "/setRC.tcl"
        )
        self.LIB_FILES = [
            os.path.join(root, file)
            for root, _, files in os.walk(self.PLATFORM_DIR + "/lib/")
            for file in files
            if file.endswith(".lib")
        ]

        if odb:
            self.ODB_FILE = odb
            self.SDC_FILE = f"{self.DESIGN_DIR}/2_floorplan.sdc"
        else:
            self.DEF_FILE = self.DESIGN_DIR + "/6_final.def.gz"
            self.TECH_LEF_FILE = [
                os.path.join(root, file)
                for root, _, files in os.walk(self.PLATFORM_DIR + "/lef/")
                for file in files
                if file.endswith("tech.lef")
            ]
            self.LEF_FILES = [
                os.path.join(root, file)
                for root, _, files in os.walk(self.PLATFORM_DIR + "/lef/")
                for file in files
                if file.endswith(".lef")
            ]
            self.SPEF_FILE = self.DESIGN_DIR + "/6_final.spef.gz"
            self.NETLIST_FILE = self.DESIGN_DIR + "/6_final.v.gz"
            self.SDC_FILE = self.DESIGN_DIR + "/6_final.sdc.gz"

        ### SET OUTPUT DIRECTORY ###
        self.OUTPUT_DIR = (
            self.CIRCUIT_OPS_DIR
            + "/IRs/"
            + self.PLATFORM
            + "/"
            + self.DESIGN_NAME
            + "/"
            + self.ODB_FILE.split(r"/")[-1].split(".")[0]
        )
        self.create_path()

        self.cell_file = self.OUTPUT_DIR + "/cell_properties.csv"
        self.design_file = self.OUTPUT_DIR + "/design_properties.csv"
        self.libcell_file = self.OUTPUT_DIR + "/libcell_properties.csv"
        self.pin_file = self.OUTPUT_DIR + "/pin_properties.csv"
        self.net_file = self.OUTPUT_DIR + "/net_properties.csv"
        self.cell_pin_file = self.OUTPUT_DIR + "/cell_pin_edge.csv"
        self.net_pin_file = self.OUTPUT_DIR + "/net_pin_edge.csv"
        self.pin_pin_file = self.OUTPUT_DIR + "/pin_pin_edge.csv"
        self.cell_net_file = self.OUTPUT_DIR + "/cell_net_edge.csv"
        self.cell_cell_file = self.OUTPUT_DIR + "/cell_cell_edge.csv"

    def create_path(self):
        if not (os.path.exists(self.OUTPUT_DIR)):
            os.makedirs(self.OUTPUT_DIR)


class CircuitOpsTables:
    def __init__(self):
        self.cell_properties = {
            "cell_name": [],
            "is_seq": [],
            "is_macro": [],
            "is_in_clk": [],
            "x0": [],
            "y0": [],
            "x1": [],
            "y1": [],
            "is_buf": [],
            "is_inv": [],
            "libcell_name": [],
            "cell_static_power": [],
            "cell_dynamic_power": [],
        }
        self.cell_properties = pd.DataFrame(self.cell_properties)

        self.libcell_properties = {
            "libcell_name": [],
            "func_id": [],
            "libcell_area": [],
            "worst_input_cap": [],
            "libcell_leakage": [],
            "fo4_delay": [],
            "libcell_delay_fixed_load": [],
        }
        self.libcell_properties = pd.DataFrame(self.libcell_properties)

        self.pin_properties = {
            "pin_name": [],
            "x": [],
            "y": [],
            "is_in_clk": [],
            "is_port": [],
            "is_startpoint": [],
            "is_endpoint": [],
            "dir": [],
            "maxcap": [],
            "maxtran": [],
            "num_reachable_endpoint": [],
            "cell_name": [],
            "net_name": [],
            "pin_tran": [],
            "pin_slack": [],
            "pin_rise_arr": [],
            "pin_fall_arr": [],
            "input_pin_cap": [],
        }
        self.pin_properties = pd.DataFrame(self.pin_properties)

        self.net_properties = {
            "net_name": [],
            "net_route_length": [],
            # "net_steiner_length": [],
            "fanout": [],
            "total_cap": [],
            "net_cap": [],
            "net_coupling": [],
            "net_res": [],
        }
        self.net_properties = pd.DataFrame(self.net_properties)

        self.cell_pin_edge = {"src": [], "tar": [], "src_type": [], "tar_type": []}
        self.cell_pin_edge = pd.DataFrame(self.cell_pin_edge)

        self.net_pin_edge = {"src": [], "tar": [], "src_type": [], "tar_type": []}
        self.net_pin_edge = pd.DataFrame(self.net_pin_edge)

        self.pin_pin_edge = {
            "src": [],
            "tar": [],
            "src_type": [],
            "tar_type": [],
            "is_net": [],
            "arc_delay": [],
        }
        self.pin_pin_edge = pd.DataFrame(self.pin_pin_edge)

        self.cell_net_edge = {"src": [], "tar": [], "src_type": [], "tar_type": []}
        self.cell_net_edge = pd.DataFrame(self.cell_net_edge)

        self.cell_cell_edge = {"src": [], "tar": [], "src_type": [], "tar_type": []}
        self.cell_cell_edge = pd.DataFrame(self.cell_cell_edge)

    def append_cell_property_entry(self, cell_props):
        cell_entry = {
            "cell_name": [cell_props["cell_name"]],
            "is_seq": [cell_props["is_seq"]],
            "is_macro": [cell_props["is_macro"]],
            "is_in_clk": [cell_props["is_in_clk"]],
            "x0": [cell_props["x0"]],
            "y0": [cell_props["y0"]],
            "x1": [cell_props["x1"]],
            "y1": [cell_props["y1"]],
            "is_buf": [cell_props["is_buf"]],
            "is_inv": [cell_props["is_inv"]],
            "libcell_name": [cell_props["libcell_name"]],
            "cell_static_power": [cell_props["cell_static_power"]],
            "cell_dynamic_power": [cell_props["cell_dynamic_power"]],
        }
        cell_entry = pd.DataFrame(cell_entry)
        self.cell_properties = pd.concat(
            [self.cell_properties, cell_entry], ignore_index=True
        )

    def append_pin_property_entry(self, pin_props):
        pin_entry = {
            "pin_name": [pin_props["pin_name"]],
            "x": [pin_props["x"]],
            "y": [pin_props["y"]],
            "is_in_clk": [pin_props["is_in_clk"]],
            "is_port": [-1],
            "is_startpoint": [-1],
            "is_endpoint": [pin_props["is_endpoint"]],
            "dir": [pin_props["dir"]],
            "maxcap": [-1],
            "maxtran": [-1],
            "num_reachable_endpoint": [pin_props["num_reachable_endpoint"]],
            "cell_name": [pin_props["cell_name"]],
            "net_name": [pin_props["net_name"]],
            "pin_tran": [pin_props["pin_tran"]],
            "pin_slack": [pin_props["pin_slack"]],
            "pin_rise_arr": [pin_props["pin_rise_arr"]],
            "pin_fall_arr": [pin_props["pin_fall_arr"]],
            "input_pin_cap": [pin_props["input_pin_cap"]],
        }
        pin_entry = pd.DataFrame(pin_entry)
        self.pin_properties = pd.concat(
            [self.pin_properties, pin_entry], ignore_index=True
        )

    def append_net_property_entry(self, net_props):
        net_entry = {
            "net_name": [net_props["net_name"]],
            "net_route_length": [net_props["net_route_length"]],
            "net_steiner_length": [-1],
            "fanout": [net_props["fanout"]],
            "total_cap": [net_props["total_cap"]],
            "net_cap": [net_props["net_cap"]],
            "net_coupling": [net_props["net_coupling"]],
            "net_res": [net_props["net_res"]],
        }
        net_entry = pd.DataFrame(net_entry)
        self.net_properties = pd.concat(
            [self.net_properties, net_entry], ignore_index=True
        )

    def append_libcell_property_entry(self, libcell_props):
        libcell_entry = {
            "libcell_name": [libcell_props["libcell_name"]],
            "func_id": [-1],
            "libcell_area": [libcell_props["libcell_area"]],
            "worst_input_cap": [-1],
            "libcell_leakage": [-1],
            "fo4_delay": [-1],
            "libcell_delay_fixed_load": [-1],
        }
        libcell_entry = pd.DataFrame(libcell_entry)
        self.libcell_properties = pd.concat(
            [self.libcell_properties, libcell_entry], ignore_index=True
        )

    def append_ip_op_cell_pairs(self, inputs, outputs):
        for input in inputs:
            for output in outputs:
                ip_op_cell_pairs = {
                    "src": [input],
                    "tar": [output],
                    "src_type": ["cell"],
                    "tar_type": ["cell"],
                }
                ip_op_cell_pairs = pd.DataFrame(ip_op_cell_pairs)
                self.cell_cell_edge = pd.concat(
                    [self.cell_cell_edge, ip_op_cell_pairs], ignore_index=True
                )

    def append_ip_op_pairs(self, input_pins, output_pins, is_net):
        count = 0
        for i_p_ in input_pins:
            for o_p_ in output_pins:
                ip_op_pairs = {
                    "src": [i_p_],
                    "tar": [o_p_],
                    "src_type": ["pin"],
                    "tar_type": ["pin"],
                    "is_net": [is_net],
                    "arc_delay": [-1],
                }
                ip_op_pairs = pd.DataFrame(ip_op_pairs)
                self.pin_pin_edge = pd.concat(
                    [self.pin_pin_edge, ip_op_pairs], ignore_index=True
                )
                count += 1

    def append_cell_net_edge(self, first_name, second_name, cell_net):
        if cell_net:
            new_edge = {
                "src": [first_name],
                "tar": [second_name],
                "src_type": ["net"],
                "tar_type": ["cell"],
            }
        else:
            new_edge = {
                "src": [first_name],
                "tar": [second_name],
                "src_type": ["cell"],
                "tar_type": ["net"],
            }
        new_edge = pd.DataFrame(new_edge)
        self.cell_net_edge = pd.concat(
            [self.cell_net_edge, new_edge], ignore_index=True
        )

    def append_cell_pin_edge(self, first_name, second_name, cell_pin):
        if cell_pin:
            new_edge = {
                "src": [first_name],
                "tar": [second_name],
                "src_type": ["pin"],
                "tar_type": ["cell"],
            }
        else:
            new_edge = {
                "src": [first_name],
                "tar": [second_name],
                "src_type": ["cell"],
                "tar_type": ["pin"],
            }
        new_edge = pd.DataFrame(new_edge)
        self.cell_pin_edge = pd.concat(
            [self.cell_pin_edge, new_edge], ignore_index=True
        )

    def append_net_pin_edge(self, first_name, second_name, net_pin):
        if net_pin:
            new_edge = {
                "src": [first_name],
                "tar": [second_name],
                "src_type": ["net"],
                "tar_type": ["pin"],
            }
        else:
            new_edge = {
                "src": [first_name],
                "tar": [second_name],
                "src_type": ["pin"],
                "tar_type": ["net"],
            }
        new_edge = pd.DataFrame(new_edge)
        self.net_pin_edge = pd.concat([self.net_pin_edge, new_edge], ignore_index=True)

    def get_IR_tables(self):
        IR_tables = defaultdict()
        IR_tables["cell_properties"] = self.cell_properties
        IR_tables["libcell_properties"] = self.libcell_properties
        IR_tables["pin_properties"] = self.pin_properties
        IR_tables["net_properties"] = self.net_properties
        IR_tables["cell_pin_edge"] = self.cell_pin_edge
        IR_tables["net_pin_edge"] = self.net_pin_edge
        IR_tables["pin_pin_edge"] = self.pin_pin_edge
        IR_tables["cell_net_edge"] = self.cell_net_edge
        IR_tables["cell_cell_edge"] = self.cell_cell_edge

        return IR_tables