import graph_tool.all as gt
import numpy as np
import pandas as pd


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

        self._co = gt.Graph()
        self._co.add_vertex(self.total_v_cnt)

        self._co.vp.type = self._co.new_vp("int")
        self._co.vp.type.a[0 : self.N_pin] = 0  # pin
        self._co.vp.type.a[self.N_pin : self.N_pin + self.N_cell] = 1  # cell
        self._co.vp.type.a[self.N_pin + self.N_cell : self.total_v_cnt] = 2  # net

        self._co.ep.type = self._co.new_ep("int")
        self._co.add_edge_list(self._edge_df.values.tolist(), eprops=[self._co.ep.type])

        self._co.vp.id = self._co.new_vp("int")
        self._co.vp.id.a = range(self._co.vp.id.a.shape[0])

        self._co.ep.id = self._co.new_ep("int")
        self._co.ep.id.a = range(self._co.ep.id.a.shape[0])

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

    ### generate subgraph
    @staticmethod
    def get_subgraph(g, v_filt, e_filt):
        sub_g = gt.GraphView(g, vfilt=v_filt, efilt=e_filt)
        print(
            f"Get Sub-GraphView: vertices:{sub_g.num_vertices()}, edges:{sub_g.num_edges()}"
        )
        ### check whether subgraph is connected and is DAG
        _, hist2 = gt.label_components(sub_g, directed=False)
        print(f"DAG: {gt.is_DAG(sub_g)}")

        return sub_g

    ### get the largest component's id
    def get_largest_idx(self, hist):
        largest_idx = -1
        largest_cnt = 0
        labels = []
        for i in range(len(hist)):
            if hist[i] > largest_cnt:
                largest_cnt = hist[i]
                largest_idx = i
            if hist[i] > 2000:
                labels.append(i)
        return largest_idx

    ### get large components' ids
    def get_large_components(self, hist, th=2000):
        labels = []
        for i in range(len(hist)):
            if hist[i] > th:
                labels.append(i)
        return labels

    def get_pin_pin_subgraph(self, cell_cnt_th=200):
        g_pp = CircuitOpsManager.get_subgraph(
            self._co, self._co.vp.type.a == 0, self._co.ep.type.a == 0
        )
        comp, hist = gt.label_components(g_pp, directed=False)
        comp.a[self.N_pin :] = -1
        labels = self.get_large_components(hist, th=cell_cnt_th)
        v_valid_pins = g_pp.new_vp("bool")
        for l in labels:
            v_valid_pins.a[comp.a == l] = True

        setattr(self._co.vp, "valid_pins", v_valid_pins)
        print(f"Valid pins: {v_valid_pins.a.sum()}")

        ### get subgraphs
        e_label = g_pp.new_ep("bool")
        e_label.a = False
        e_ar = g_pp.get_edges(eprops=[self._co.ep.id])
        v_ar = self._co.get_vertices(
            vprops=[self._co.vp.is_buf, self._co.vp.is_inv, self._co.vp.valid_pins]
        )
        src = e_ar[:, 0]
        tar = e_ar[:, 1]
        idx = e_ar[:, 2]

        mask = (v_ar[src, -1] == True) & (v_ar[tar, -1] == True)
        e_label.a[idx[mask]] = True

        return CircuitOpsManager.get_subgraph(g_pp, v_valid_pins, e_label)

    def add_rel_ids(self):
        ### add cell id to pin_df
        cell_temp = self._cell_df.loc[:, ["name", "id"]]
        cell_temp = cell_temp.rename(columns={"name": "cellname", "id": "cell_id"})
        self._pin_df = self._pin_df.merge(cell_temp, on="cellname", how="left")
        idx = self._pin_df[pd.isna(self._pin_df.cell_id)].index
        self._pin_df.loc[idx, ["cell_id"]] = self._pin_df.loc[idx, ["id"]].to_numpy()

        pin_cellid = self._pin_df.cell_id.to_numpy()
        # pin_isseq = v_is_seq.a[0:N_pin]
        pin_ismacro = self._pin_df["is_macro"].to_numpy()
        # mask = (pin_isseq==True)| (pin_ismacro==True)
        mask = pin_ismacro == True
        ### for pins in macro and seq, pin_cellid = pin id
        pin_cellid[mask] = self._pin_df[mask].id

        ### add net id to pin_df
        net_temp = self._net_df.loc[:, ["name", "id"]]
        net_temp = net_temp.rename(columns={"name": "netname", "id": "net_id"})
        self._pin_df = self._pin_df.merge(net_temp, on="netname", how="left")

    def generate_buffer_tree(self):
        sub_g_pp = self.get_pin_pin_subgraph()

        self._pin_df["selected"] = self._co.vp.valid_pins.a[0 : self.N_pin]

        ### get buffer tree start and end points
        v_bt_s = self._co.new_vp("bool")
        v_bt_e = self._co.new_vp("bool")
        v_bt_s.a = False
        v_bt_e.a = False

        e_ar = sub_g_pp.get_edges()
        v_ar = self._co.get_vertices(vprops=[self._co.vp.is_buf, self._co.vp.is_inv])
        src = e_ar[:, 0]
        tar = e_ar[:, 1]
        src_isbuf = v_ar[src, 1]
        src_isinv = v_ar[src, 2]
        tar_isbuf = v_ar[tar, 1]
        tar_isinv = v_ar[tar, 2]
        is_s = (
            (tar_isbuf | tar_isinv)
            & np.logical_not(src_isbuf)
            & np.logical_not(src_isinv)
        )
        v_bt_s.a[src[is_s == 1]] = True

        src_iss = v_bt_s.a[src] == True
        is_e = (
            (src_isbuf | src_isinv | src_iss)
            & np.logical_not(tar_isbuf)
            & np.logical_not(tar_isinv)
        )
        v_bt_e.a[tar[is_e == 1]] = True
        print(
            "buf tree start cnt: ",
            v_bt_s.a.sum(),
            "buf tree end cnt: ",
            v_bt_e.a.sum(),
        )

        ### get buf tree start pin id ###
        v_net_id = self._co.new_vp("int")
        v_net_id.a[0 : self.N_pin] = self._pin_df.net_id.to_numpy()
        mask = v_bt_s.a < 1
        v_net_id.a[mask] = 0

        ### mark buffer trees
        v_tree_id = self._co.new_vp("int")
        v_tree_id.a = 0
        v_polarity = self._co.new_vp("bool")
        v_polarity.a = True
        e_tree_id = self._co.new_ep("int")
        e_tree_id.a = 0

        tree_end_list = []
        buf_list = []

        v_all = self._co.get_vertices()
        l = np.array(list(range(1, int(v_bt_s.a.sum()) + 1)))
        v_tree_id.a[v_bt_s.a > 0] = l
        loc = v_all[v_bt_s.a > 0]
        out_v_list = []
        for i in loc:
            out_e = sub_g_pp.get_out_edges(i, eprops=[self._co.ep.id])
            out_v = out_e[:, 1]
            v_tree_cnt = v_tree_id[i]
            net_id = v_net_id[i]
            e_tree_id.a[out_e[:, -1]] = v_tree_cnt
            v_tree_id.a[out_v] = v_tree_cnt
            v_net_id.a[out_v] = net_id
            tree_end_list.append(
                out_v[
                    (self._co.vp.is_buf.a[out_v] == False)
                    & (self._co.vp.is_inv.a[out_v] == False)
                ]
            )
            out_v = out_v[
                (self._co.vp.is_buf.a[out_v] == True)
                | (self._co.vp.is_inv.a[out_v] == True)
            ]
            buf_list.append(out_v)
            out_v_list.append(out_v)

        new_v = np.concatenate(out_v_list, axis=0)
        (N,) = new_v.shape
        print("num of buffer tree out pins: ", N)

        while N > 0:
            out_v_list = []
            for i in new_v:
                if self._co.vp.is_buf[i]:
                    out_e = sub_g_pp.get_out_edges(i, eprops=[self._co.ep.id])
                    out_v = out_e[:, 1]
                    v_tree_cnt = v_tree_id[i]
                    net_id = v_net_id[i]
                    v_p = v_polarity.a[i]
                    e_tree_id.a[out_e[:, -1]] = v_tree_cnt
                    v_tree_id.a[out_v] = v_tree_cnt
                    v_net_id.a[out_v] = net_id
                    v_polarity.a[out_v] = v_p
                    tree_end_list.append(
                        out_v[
                            (self._co.vp.is_buf.a[out_v] == False)
                            & (self._co.vp.is_inv.a[out_v] == False)
                        ]
                    )
                    out_v = out_v[
                        (self._co.vp.is_buf.a[out_v] == True)
                        | (self._co.vp.is_inv.a[out_v] == True)
                    ]
                    buf_list.append(out_v)
                    out_v_list.append(out_v)
                else:
                    out_e = sub_g_pp.get_out_edges(i, eprops=[self._co.ep.id])
                    out_v = out_e[:, 1]
                    v_tree_cnt = v_tree_id[i]
                    net_id = v_net_id[i]
                    v_p = v_polarity.a[i]
                    e_tree_id.a[out_e[:, -1]] = v_tree_cnt
                    v_tree_id.a[out_v] = v_tree_cnt
                    v_net_id.a[out_v] = net_id
                    if self._co.vp.dir[i]:
                        v_polarity.a[out_v] = not v_p
                    else:
                        v_polarity.a[out_v] = v_p
                    ###
                    tree_end_list.append(
                        out_v[
                            (self._co.vp.is_buf.a[out_v] == False)
                            & (self._co.vp.is_inv.a[out_v] == False)
                        ]
                    )
                    ###
                    out_v = out_v[
                        (self._co.vp.is_buf.a[out_v] == True)
                        | (self._co.vp.is_inv.a[out_v] == True)
                    ]
                    ###
                    buf_list.append(out_v)
                    ###
                    out_v_list.append(out_v)

            new_v = np.concatenate(out_v_list, axis=0)
            (N,) = new_v.shape
            print("num of buffer tree out pins: ", N)

        ### get actual number of BT end pin cnt
        tree_end_list_new = np.concatenate(tree_end_list, axis=0)
        # print(tree_end_list_new.shape[0], v_bt_e.a.sum())

        N_bt_e = tree_end_list_new.shape[0]
        v_bt_e = self._co.new_vp("bool")
        v_bt_e.a = False
        v_bt_e.a[tree_end_list_new] = True
        print(f"Buffer tree ends: {v_bt_e.a.sum()}")

        self._pin_df["net_id_rm_bt"] = self._pin_df["net_id"]
        self._pin_df.loc[tree_end_list_new, ["net_id_rm_bt"]] = v_net_id.a[
            tree_end_list_new
        ]

        setattr(self._co.vp, "bt_s", v_bt_s)
        setattr(self._co.vp, "bt_e", v_bt_e)
        setattr(self._co.vp, "net_id", v_net_id)
        setattr(self._co.vp, "tree_id", v_tree_id)
        setattr(self._co.vp, "polarity", v_polarity)
        setattr(self._co.ep, "tree_id", e_tree_id)

    ### generate cell graph from pin graph
    def get_cell_graph(self, pin_g, pin_cellid, g, e_type, e_id):
        ### new mask cell graph: pre-opt
        u_pins = pin_g.get_vertices()
        u_cells = pin_cellid[u_pins]
        u_cells = np.unique(u_cells).astype(int)

        # add cell2cell edge
        v_mask_cell = g.new_vp("bool")
        e_mask_cell = g.new_ep("bool")
        v_mask_cell.a[u_cells] = True

        e_ar = g.get_edges(eprops=[e_type, e_id])
        mask = e_ar[:, 2] == 4  # edge type == 4: cell2cell
        e_ar = e_ar[mask]
        e_src = e_ar[:, 0]
        e_tar = e_ar[:, 1]
        e_mask = (v_mask_cell.a[e_src] == True) & (v_mask_cell.a[e_tar] == True)
        e_mask_cell.a[e_ar[:, -1][e_mask]] = True

        ### construct and check u_cell_g
        u_cell_g = self.get_subgraph(v_mask_cell, e_mask_cell)

        return u_cells, u_cell_g

    ### generate cell graph from cell ids
    def get_cell_graph_from_cells(self, u_cells, e_type, e_id):
        u_cells = np.unique(u_cells).astype(int)

        # add cell2cell edge
        v_mask_cell = self._co.new_vp("bool")
        e_mask_cell = self._co.new_ep("bool")
        v_mask_cell.a[u_cells] = True

        e_ar = self._co.get_edges(eprops=[e_type, e_id])
        mask = e_ar[:, 2] == 4  # edge type == 4: cell2cell
        e_ar = e_ar[mask]
        e_src = e_ar[:, 0]
        e_tar = e_ar[:, 1]
        e_mask = (v_mask_cell.a[e_src] == True) & (v_mask_cell.a[e_tar] == True)
        e_mask_cell.a[e_ar[:, -1][e_mask]] = True

        ### construct and check u_cell_g
        u_cell_g = self.get_subgraph(self._co, v_mask_cell, e_mask_cell)

        return u_cell_g

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
            prop = self._co.new_vp(prop_type)
            prop.a[: self.N_pin] = self._pin_df[prop_name].to_numpy()
            setattr(self._co.vp, prop_name, prop)

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
            prop = self._co.new_vp(prop_type)
            prop.a[self.N_pin : self.N_pin + self.N_cell] = self._cell_df[
                prop_name
            ].to_numpy()
            setattr(self._co.vp, prop_name, prop)

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
            self._co.vp[prop_name].a[self.N_pin : self.N_pin + self.N_cell] = (
                self._cell_df[prop_name].to_numpy()
            )

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
            prop = self._co.new_vp(prop_type)
            prop.a[self.N_pin + self.N_cell : self.total_v_cnt] = self._net_df[
                prop_name
            ].to_numpy()
            setattr(self._co.vp, prop_name, prop)

    def update_fo4(self):
        ### processing fo4 table
        self._fo4_df["group_id"] = pd.factorize(self._fo4_df.func_id)[0] + 1
        self._fo4_df["libcell_id"] = range(self._fo4_df.shape[0])
        libcell_np = self._fo4_df.to_numpy()

        ### assign cell size class
        # size_class：根据 fix_load_delay 降序排序后的索引位置。
        # size_class2：根据 fix_load_delay 值划分的更细的分类，每个分类区间内分配一个值
        # size_cnt：记录每个组的单元数。
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

    def get_selected_pins(self):
        return self._pin_df[
            (self._pin_df.selected == True)
            & (self._pin_df.is_buf == False)
            & (self._pin_df.is_inv == False)
        ]

    def get_driver_sink_info(self, pin_pin_df, selected_pin_df):
        ### get driver pins and related properties ###
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
        cell_info = cell_info.rename(columns={"id": "driver_id", "y": "driver_y"})
        driver_pin_info = driver_pin_info.merge(cell_info, on="driver_id", how="left")

        ### get sink pins and related properties ###
        sink_pin = selected_pin_df[selected_pin_df.dir == 1]
        sink_pin_info = sink_pin.loc[
            :, ["id", "x", "y", "cap", "net_id", "cell_id", "risearr", "fallarr"]
        ]
        sink_pin_info = sink_pin_info.merge(driver_pin_info, on="net_id", how="left")

        sink_pin_info.x = sink_pin_info.x - sink_pin_info.driver_x
        sink_pin_info.y = sink_pin_info.y - sink_pin_info.driver_y
        idx = sink_pin_info[pd.isna(sink_pin_info.driver_x)].index
        sink_pin_info = sink_pin_info.drop(idx)

        ### get context sink locations ###
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

        ### merge information and rename ###
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

        # def get_delays(self, pin_pin_df, sink_pin_info):
        ### get cell arc delays ###
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

        ### get net delay ###
        cell_arc = cell_arc.rename(
            columns={
                "driver_pin_id": "id",
                "arc_delay_mean": "net_delay_mean",
                "arc_delay_min": "net_delay_min",
                "arc_delay_max": "net_delay_max",
            }
        )
        sink_pin_info = sink_pin_info.merge(cell_arc, on="id", how="left")

        ### stage delay = driver cell arc delay + net delay ###
        sink_pin_info["stage_delay"] = (
            sink_pin_info.arc_delay_max + sink_pin_info.net_delay_max
        )
        sink_pin_info["arc_delay"] = sink_pin_info.arc_delay_max
        sink_pin_info["net_delay"] = sink_pin_info.net_delay_max

        return driver_pin_info, sink_pin_info
