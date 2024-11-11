"""
 # @ Author: xlindo
 # @ Create Time: 2024-11-11 08:00:00
 # @ Modified by: hi@xlindo.com
 # @ Modified time: 2024-11-12 00:20:15
 # @ Description: use networkx instead of graph-tool since the latter one is hard to
 be installed

	Copyright © [xlindo.com](https://www.xlindo.com).
 # @ License under Apache-2.0 license
 """

import pandas as pd
import networkx as nx
import numpy as np


class CircuitOpsManager:
    def __init__(self, pin_df, cell_df, net_df, edge_df, fo4_df):
        if (
            not isinstance(pin_df, pd.DataFrame)
            or not isinstance(cell_df, pd.DataFrame)
            or not isinstance(net_df, pd.DataFrame)
            or not isinstance(edge_df, pd.DataFrame)
            or not isinstance(fo4_df, pd.DataFrame)
        ):
            raise ValueError("Input must be pandas DataFrames")

        self._pin_df = pin_df
        self._cell_df = cell_df
        self._net_df = net_df
        self._edge_df = edge_df
        self._fo4_df = fo4_df

        self.N_pin = len(pin_df["id"])
        self.N_cell = len(cell_df["id"])
        self.N_net = len(net_df["id"])
        self.total_v_cnt = self.N_pin + self.N_cell + self.N_net

        self._co = nx.DiGraph()
        # Add nodes
        for i in range(self.N_pin):
            self._co.add_node(i, type=0)  # pin
        for i in range(self.N_pin, self.N_pin + self.N_cell):
            self._co.add_node(i, type=1)  # cell
        for i in range(self.N_pin + self.N_cell, self.total_v_cnt):
            self._co.add_node(i, type=2)  # net

        # Add edges
        for edge in self._edge_df.values.tolist():
            self._co.add_edge(int(edge[0]), int(edge[1]), type=int(edge[2]))

        self.update_fo4()
        self.update_pin_props()
        self.update_cell_props()
        self.update_net_props()

        self.add_rel_ids()

    @property
    def fo4_df(self):
        return self._fo4_df

    @fo4_df.setter
    def fo4_df(self, value):
        if not isinstance(value, pd.DataFrame):
            raise ValueError("fo4_df must be a pandas DataFrame")
        self._fo4_df = value

    @property
    def pin_df(self):
        return self._pin_df

    @pin_df.setter
    def pin_df(self, value):
        if not isinstance(value, pd.DataFrame):
            raise ValueError("pin_df must be a pandas DataFrame")
        self._pin_df = value

    @property
    def cell_df(self):
        return self._cell_df

    @cell_df.setter
    def cell_df(self, value):
        if not isinstance(value, pd.DataFrame):
            raise ValueError("cell_df must be a pandas DataFrame")
        self._cell_df = value

    @property
    def net_df(self):
        return self._net_df

    @net_df.setter
    def net_df(self, value):
        if not isinstance(value, pd.DataFrame):
            raise ValueError("net_df must be a pandas DataFrame")
        self._net_df = value

    @property
    def edge_df(self):
        return self._edge_df

    @edge_df.setter
    def edge_df(self, value):
        if not isinstance(value, pd.DataFrame):
            raise ValueError("edge_df must be a pandas DataFrame")
        self._edge_df = value

    def get_largest_idx(self, hist):
        largest_idx = -1
        largest_cnt = 0
        labels = []
        for i, count in enumerate(hist):
            if count > largest_cnt:
                largest_cnt = count
                largest_idx = i
            if count > 2000:
                labels.append(i)
        return largest_idx

    def get_large_components(self, hist, th=2000):
        return [i for i, count in enumerate(hist) if count > th]

    @staticmethod
    def get_subgraph(g, v_filt, e_filt):
        sub_g = g.subgraph(v_filt)
        print(
            f"Get Sub-Graph: vertices:{sub_g.number_of_nodes()}, edges:{sub_g.number_of_edges()}"
        )
        is_dag = nx.is_directed_acyclic_graph(sub_g)
        print(f"DAG: {is_dag}")

        return sub_g

    def get_pin_pin_subgraph(self, cell_cnt_th=200):
        g_pp = self._co.subgraph(
            [n for n, d in self._co.nodes(data=True) if d["type"] == 0]
        )
        comp = list(nx.connected_components(g_pp.to_undirected()))
        hist = [len(c) for c in comp]
        labels = self.get_large_components(hist, th=cell_cnt_th)
        v_valid_pins = {n for l in labels for n in comp[l]}

        nx.set_node_attributes(self._co, v_valid_pins, "valid_pins")
        print(f"Valid pins: {len(v_valid_pins)}")

        e_label = [
            (u, v)
            for u, v, d in g_pp.edges(data=True)
            if u in v_valid_pins and v in v_valid_pins
        ]

        return self.get_subgraph(g_pp, v_valid_pins, e_label)

    def add_rel_ids(self):
        cell_temp = self._cell_df.loc[:, ["name", "id"]]
        cell_temp = cell_temp.rename(columns={"name": "cellname", "id": "cell_id"})
        self._pin_df = self._pin_df.merge(cell_temp, on="cellname", how="left")
        idx = self._pin_df[pd.isna(self._pin_df.cell_id)].index
        self._pin_df.loc[idx, ["cell_id"]] = self._pin_df.loc[idx, ["id"]].to_numpy()

        pin_cellid = self._pin_df.cell_id.to_numpy()
        pin_ismacro = self._pin_df["is_macro"].to_numpy()
        mask = pin_ismacro == True
        pin_cellid[mask] = self._pin_df[mask].id

        net_temp = self._net_df.loc[:, ["name", "id"]]
        net_temp = net_temp.rename(columns={"name": "netname", "id": "net_id"})
        self._pin_df = self._pin_df.merge(net_temp, on="netname", how="left")

    def update_pin_props(self):
        properties = {
            "x": "float",
            "y": "float",
            "is_in_clk": "bool",
            "is_port": "bool",
            "is_start": "bool",
            "is_end": "bool",
            "dir": "bool",
            "maxcap": "float",
            "maxtran": "float",
            "num_reachable_endpoint": "int",
            "tran": "float",
            "slack": "float",
            "risearr": "float",
            "fallarr": "float",
            "cap": "float",
            "is_macro": "bool",
            "is_seq": "bool",
            "is_buf": "bool",
            "is_inv": "bool",
        }

        for prop_name, prop_type in properties.items():
            for i in range(self.N_pin):
                self._co.nodes[i][prop_name] = self._pin_df[prop_name].iloc[i]

    def update_cell_props(self):
        properties = {
            "x0": "float",
            "y0": "float",
            "x1": "float",
            "y1": "float",
            "staticpower": "float",
            "dynamicpower": "float",
            "fo4_delay": "float",
            "fix_load_delay": "float",
            "group_id": "int",
            "libcell_id": "int",
            "size_class": "int",
            "size_class2": "int",
            "size_cnt": "int",
        }

        for prop_name, prop_type in properties.items():
            for i in range(self.N_pin, self.N_pin + self.N_cell):
                self._co.nodes[i][prop_name] = self._cell_df[prop_name].iloc[
                    i - self.N_pin
                ]

        existing_props = {
            "x": "float",
            "y": "float",
            "is_seq": "bool",
            "is_macro": "bool",
            "is_in_clk": "bool",
            "is_buf": "bool",
            "is_inv": "bool",
        }

        for prop_name, prop_type in existing_props.items():
            for i in range(self.N_pin, self.N_pin + self.N_cell):
                self._co.nodes[i][prop_name] = self._cell_df[prop_name].iloc[
                    i - self.N_pin
                ]

    def update_net_props(self):
        properties = {
            "net_route_length": "float",
            "net_steiner_length": "float",
            "fanout": "int",
            "total_cap": "float",
            "net_cap": "float",
            "net_coupling": "float",
            "net_res": "float",
        }

        for prop_name, prop_type in properties.items():
            for i in range(self.N_pin + self.N_cell, self.total_v_cnt):
                self._co.nodes[i][prop_name] = self._net_df[prop_name].iloc[
                    i - self.N_pin - self.N_cell
                ]

    def update_fo4(self):
        self._fo4_df["group_id"] = pd.factorize(self._fo4_df.func_id)[0] + 1
        self._fo4_df["libcell_id"] = range(self._fo4_df.shape[0])
        libcell_np = self._fo4_df.to_numpy()

        self._fo4_df["size_class"] = 0
        self._fo4_df["size_class2"] = 0
        self._fo4_df["size_cnt"] = 0
        class_cnt = 50
        for i in range(self._fo4_df.group_id.min(), self._fo4_df.group_id.max() + 1):
            temp = self._fo4_df.loc[
                self._fo4_df.group_id == i, ["group_id", "fix_load_delay"]
            ]
            temp = temp.sort_values(by=["fix_load_delay"], ascending=False)
            self._fo4_df.loc[temp.index, ["size_class"]] = range(len(temp))
            self._fo4_df.loc[temp.index, ["size_cnt"]] = len(temp)

            temp["size_cnt"] = 0
            MIN = temp.fix_load_delay.min()
            MAX = temp.fix_load_delay.max()
            interval = (MAX - MIN) / class_cnt
            for j in range(1, class_cnt):
                delay_h = MAX - j * interval
                delay_l = MAX - (j + 1) * interval
                if j == (class_cnt - 1):
                    delay_l = MIN
                temp.loc[
                    (temp.fix_load_delay < delay_h) & (temp.fix_load_delay >= delay_l),
                    ["size_cnt"],
                ] = j
            self._fo4_df.loc[temp.index, ["size_class2"]] = temp["size_cnt"]

        cell_fo4 = self._fo4_df.loc[
            :,
            [
                "ref",
                "fo4_delay",
                "fix_load_delay",
                "group_id",
                "libcell_id",
                "size_class",
                "size_class2",
                "size_cnt",
            ],
        ]
        self._cell_df = self._cell_df.merge(cell_fo4, on="ref", how="left")
        self._cell_df["libcell_id"] = self._cell_df["libcell_id"].fillna(-1)

    def generate_buffer_tree(self):
        sub_g_pp = self.get_pin_pin_subgraph()

        self._pin_df["selected"] = self._pin_df.index.isin(
            [n for n, d in self._co.nodes(data=True) if d.get("valid_pins", False)]
        )

        # Get buffer tree start and end points
        v_bt_s = {n: False for n in self._co.nodes}
        v_bt_e = {n: False for n in self._co.nodes}

        e_ar = list(sub_g_pp.edges)
        v_ar = {
            n: (d.get("is_buf", False), d.get("is_inv", False))
            for n, d in self._co.nodes(data=True)
        }
        src = [e[0] for e in e_ar]
        tar = [e[1] for e in e_ar]
        src_isbuf = [v_ar[s][0] for s in src]
        src_isinv = [v_ar[s][1] for s in src]
        tar_isbuf = [v_ar[t][0] for t in tar]
        tar_isinv = [v_ar[t][1] for t in tar]

        is_s = [
            (tb or ti) and not (sb or si)
            for sb, si, tb, ti in zip(src_isbuf, src_isinv, tar_isbuf, tar_isinv)
        ]
        for s in [src[i] for i, val in enumerate(is_s) if val]:
            v_bt_s[s] = True

        src_iss = [v_bt_s[s] for s in src]
        is_e = [
            (sb or si or ss) and not (tb or ti)
            for sb, si, ss, tb, ti in zip(
                src_isbuf, src_isinv, src_iss, tar_isbuf, tar_isinv
            )
        ]
        for t in [tar[i] for i, val in enumerate(is_e) if val]:
            v_bt_e[t] = True

        print(
            "buf tree start cnt: ",
            sum(v_bt_s.values()),
            "buf tree end cnt: ",
            sum(v_bt_e.values()),
        )

        # Get buf tree start pin id
        v_net_id = {n: 0 for n in self._co.nodes}
        for i in range(self.N_pin):
            v_net_id[i] = self._pin_df.net_id.iloc[i]
        for n in [n for n, val in v_bt_s.items() if not val]:
            v_net_id[n] = 0

        # Mark buffer trees
        v_tree_id = {n: 0 for n in self._co.nodes}
        v_polarity = {n: True for n in self._co.nodes}
        e_tree_id = {e: 0 for e in self._co.edges}

        tree_end_list = []
        buf_list = []

        l = list(range(1, sum(v_bt_s.values()) + 1))
        for i, n in enumerate([n for n, val in v_bt_s.items() if val]):
            v_tree_id[n] = l[i]

        out_v_list = []
        for n in [n for n, val in v_bt_s.items() if val]:
            out_e = list(sub_g_pp.out_edges(n))
            out_v = [e[1] for e in out_e]
            v_tree_cnt = v_tree_id[n]
            net_id = v_net_id[n]
            for e in out_e:
                e_tree_id[e] = v_tree_cnt
            for v in out_v:
                v_tree_id[v] = v_tree_cnt
                v_net_id[v] = net_id
            tree_end_list.append(
                [
                    v
                    for v in out_v
                    if not (
                        self._co.nodes[v].get("is_buf", False)
                        or self._co.nodes[v].get("is_inv", False)
                    )
                ]
            )
            out_v = [
                v
                for v in out_v
                if self._co.nodes[v].get("is_buf", False)
                or self._co.nodes[v].get("is_inv", False)
            ]
            buf_list.append(out_v)
            out_v_list.append(out_v)

        new_v = [v for sublist in out_v_list for v in sublist]
        N = len(new_v)
        print("num of buffer tree out pins: ", N)

        while N > 0:
            out_v_list = []
            for n in new_v:
                out_e = list(sub_g_pp.out_edges(n))
                out_v = [e[1] for e in out_e]
                v_tree_cnt = v_tree_id[n]
                net_id = v_net_id[n]
                v_p = v_polarity[n]
                for e in out_e:
                    e_tree_id[e] = v_tree_cnt
                for v in out_v:
                    v_tree_id[v] = v_tree_cnt
                    v_net_id[v] = net_id
                    v_polarity[v] = (
                        v_p if not self._co.nodes[n].get("dir", False) else not v_p
                    )
                tree_end_list.append(
                    [
                        v
                        for v in out_v
                        if not (
                            self._co.nodes[v].get("is_buf", False)
                            or self._co.nodes[v].get("is_inv", False)
                        )
                    ]
                )
                out_v = [
                    v
                    for v in out_v
                    if self._co.nodes[v].get("is_buf", False)
                    or self._co.nodes[v].get("is_inv", False)
                ]
                buf_list.append(out_v)
                out_v_list.append(out_v)

            new_v = [v for sublist in out_v_list for v in sublist]
            N = len(new_v)
            print("num of buffer tree out pins: ", N)

        # Get actual number of BT end pin cnt
        tree_end_list_new = [v for sublist in tree_end_list for v in sublist]
        N_bt_e = len(tree_end_list_new)
        v_bt_e = {n: False for n in self._co.nodes}
        for n in tree_end_list_new:
            v_bt_e[n] = True
        print(f"Buffer tree ends: {sum(v_bt_e.values())}")

        self._pin_df["net_id_rm_bt"] = self._pin_df["net_id"]
        self._pin_df.loc[tree_end_list_new, ["net_id_rm_bt"]] = [
            v_net_id[n] for n in tree_end_list_new
        ]

        nx.set_node_attributes(self._co, v_bt_s, "bt_s")
        nx.set_node_attributes(self._co, v_bt_e, "bt_e")
        nx.set_node_attributes(self._co, v_net_id, "net_id")
        nx.set_node_attributes(self._co, v_tree_id, "tree_id")
        nx.set_node_attributes(self._co, v_polarity, "polarity")

        nx.set_edge_attributes(self._co, e_tree_id, "tree_id")

    def get_cell_graph(self, pin_g, pin_cellid, g, e_type, e_id):
        # New mask cell graph: pre-opt
        u_pins = list(pin_g.nodes)
        u_cells = np.unique([pin_cellid[pin] for pin in u_pins]).astype(int)

        # Add cell2cell edge
        v_mask_cell = {n: False for n in g.nodes}
        e_mask_cell = {e: False for e in g.edges}
        for cell in u_cells:
            v_mask_cell[cell] = True

        e_ar = [
            (u, v, d) for u, v, d in g.edges(data=True) if d[e_type] == 4
        ]  # edge type == 4: cell2cell
        for u, v, d in e_ar:
            if v_mask_cell[u] and v_mask_cell[v]:
                e_mask_cell[(u, v)] = True

        # Construct and check u_cell_g
        u_cell_g = self.get_subgraph(g, v_mask_cell, e_mask_cell)

        return u_cells, u_cell_g

    def get_cell_graph_from_cells(self, u_cells, e_type, e_id):
        u_cells = np.unique(u_cells).astype(int)

        # Add cell2cell edge
        v_mask_cell = {n: False for n in self._co.nodes}
        e_mask_cell = {e: False for e in self._co.edges}
        for cell in u_cells:
            v_mask_cell[cell] = True

        e_ar = [
            (u, v, d) for u, v, d in self._co.edges(data=True) if d[e_type] == 4
        ]  # edge type == 4: cell2cell
        for u, v, d in e_ar:
            if v_mask_cell[u] and v_mask_cell[v]:
                e_mask_cell[(u, v)] = True

        # Construct and check u_cell_g
        u_cell_g = self.get_subgraph(self._co, v_mask_cell, e_mask_cell)

        return u_cell_g

    def get_selected_pins(self):
        self.get_pin_pin_subgraph()
        self._pin_df["selected"] = self._pin_df.index.isin(
            [n for n, d in self._co.nodes(data=True) if d.get("valid_pins", False)]
        )
        return self._pin_df[
            (self._pin_df.selected == True)
            & (self._pin_df.is_buf == False)
            & (self._pin_df.is_inv == False)
        ]

    def get_driver_sink_info(self, pin_pin_df, selected_pin_df):
        # Get driver pins and related properties
        driver_pin = selected_pin_df[selected_pin_df.dir == 0]
        driver_pin_info = driver_pin.loc[
            :, ["id", "net_id", "x", "y", "cell_id", "risearr", "fallarr"]
        ]
        driver_pin_info = driver_pin_info.rename(
            columns={
                "id": "driver_pin_id",
                "x": "driver_x",
                "y": "driver_y",
                "cell_id": "driver_id",
                "risearr": "driver_risearr",
                "fallarr": "driver_fallarr",
            }
        )
        cell_info = self._cell_df.loc[
            :, ["id", "libcell_id", "fo4_delay", "fix_load_delay"]
        ]
        cell_info = cell_info.rename(columns={"id": "driver_id"})
        driver_pin_info = driver_pin_info.merge(cell_info, on="driver_id", how="left")

        # Get sink pins and related properties
        sink_pin = selected_pin_df[selected_pin_df.dir == 1]
        sink_pin_info = sink_pin.loc[
            :, ["id", "x", "y", "cap", "net_id", "cell_id", "risearr", "fallarr"]
        ]
        sink_pin_info = sink_pin_info.merge(driver_pin_info, on="net_id", how="left")

        sink_pin_info["x"] = sink_pin_info["x"] - sink_pin_info["driver_x"]
        sink_pin_info["y"] = sink_pin_info["y"] - sink_pin_info["driver_y"]
        idx = sink_pin_info[pd.isna(sink_pin_info.driver_x)].index
        sink_pin_info = sink_pin_info.drop(idx)

        # Get context sink locations
        sink_loc = sink_pin_info.groupby("net_id", as_index=False).agg(
            {
                "x": ["mean", "min", "max", "std"],
                "y": ["mean", "min", "max", "std"],
                "cap": ["sum"],
            }
        )
        sink_loc.columns = [
            "_".join(col).rstrip("_") for col in sink_loc.columns.values
        ]
        sink_loc["x_std"] = sink_loc["x_std"].fillna(0)
        sink_loc["y_std"] = sink_loc["y_std"].fillna(0)

        # Merge information and rename
        sink_pin_info = sink_pin_info.merge(sink_loc, on="net_id", how="left")
        sink_pin_info = sink_pin_info.rename(
            columns={
                "libcell_id": "driver_libcell_id",
                "fo4_delay": "driver_fo4_delay",
                "fix_load_delay": "driver_fix_load_delay",
                "x_mean": "context_x_mean",
                "x_min": "context_x_min",
                "x_max": "context_x_max",
                "x_std": "context_x_std",
                "y_mean": "context_y_mean",
                "y_min": "context_y_min",
                "y_max": "context_y_max",
                "y_std": "context_y_std",
                "risearr": "sink_risearr",
                "fallarr": "sink_fallarr",
            }
        )
        sink_pin_info["sink_arr"] = sink_pin_info[["sink_risearr", "sink_fallarr"]].min(
            axis=1
        )
        sink_pin_info["driver_arr"] = sink_pin_info[
            ["driver_risearr", "driver_fallarr"]
        ].min(axis=1)

        # Get cell arc delays
        cell_arc = pin_pin_df.groupby("tar_id", as_index=False).agg(
            {"arc_delay": ["mean", "min", "max"]}
        )
        cell_arc.columns = [
            "_".join(col).rstrip("_") for col in cell_arc.columns.values
        ]
        cell_arc = cell_arc.rename(columns={"tar_id": "driver_pin_id"})
        sink_pin_info = sink_pin_info.astype({"driver_pin_id": "int"})
        sink_pin_info = sink_pin_info.merge(cell_arc, on="driver_pin_id", how="left")
        idx = sink_pin_info[pd.isna(sink_pin_info.arc_delay_mean)].index
        sink_pin_info = sink_pin_info.drop(idx)

        # Get net delay
        cell_arc = cell_arc.rename(
            columns={
                "driver_pin_id": "id",
                "arc_delay_mean": "net_delay_mean",
                "arc_delay_min": "net_delay_min",
                "arc_delay_max": "net_delay_max",
            }
        )
        sink_pin_info = sink_pin_info.merge(cell_arc, on="id", how="left")

        # Stage delay = driver cell arc delay + net delay
        sink_pin_info["stage_delay"] = (
            sink_pin_info["arc_delay_max"] + sink_pin_info["net_delay_max"]
        )
        sink_pin_info["arc_delay"] = sink_pin_info["arc_delay_max"]
        sink_pin_info["net_delay"] = sink_pin_info["net_delay_max"]

        return driver_pin_info, sink_pin_info
