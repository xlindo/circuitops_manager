# SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import re
import pandas as pd
import numpy as np
from numpy.random import *

# import graph_tool as gt


### generate pandas dataframes by reading csv files
def read_tables(data_root, design, mcmm):
    cell_edge_path = data_root + design + "_cell_edge.csv"
    cell_path = data_root + design + "_cell.csv"
    net_edge_path = data_root + design + "_net_edge.csv"
    net_path = data_root + design + "_net.csv"
    pin_edge_path = data_root + design + "_pin_edge.csv"
    pin_path = data_root + design + "_pin.csv"
    net_cell_edge_path = data_root + design + "_net_cell_edge.csv"
    cell2cell_edge_path = data_root + design + "_cell2cell_edge.csv"

    mcmm_cell_path = data_root + design + "_" + mcmm + "_cell.csv"
    mcmm_net_path = data_root + design + "_" + mcmm + "_net.csv"
    mcmm_pin_path = data_root + design + "_" + mcmm + "_pin.csv"

    all_fo4_delay_path = data_root + "all_fo4_delay_new.txt"
    median_delay_path = data_root + "median_delay_new.txt"

    ### load tables
    fo4_df = pd.read_table(all_fo4_delay_path, sep=",")
    median_delay_df = pd.read_table(median_delay_path, sep=",")

    pin_df = pd.read_csv(pin_path)
    cell_df = pd.read_csv(cell_path)
    net_df = pd.read_csv(net_path)

    pin_edge_df = pd.read_csv(pin_edge_path)
    cell_edge_df = pd.read_csv(cell_edge_path)
    net_edge_df = pd.read_csv(net_edge_path)
    net_cell_edge_df = pd.read_csv(net_cell_edge_path)
    cell2cell_edge_df = pd.read_csv(cell2cell_edge_path)

    ### load mcmm table
    mcmm_pin_df = pd.read_csv(mcmm_pin_path)
    mcmm_cell_df = pd.read_csv(mcmm_cell_path)
    mcmm_net_df = pd.read_csv(mcmm_net_path)

    ### merge mcmm-independent features and mcmm-depedent features
    pin_df = pin_df.merge(mcmm_pin_df, on="name", how="left")
    cell_df = cell_df.merge(mcmm_cell_df, on="name", how="left")
    net_df = net_df.merge(mcmm_net_df, on="name", how="left")

    ### merge fo4_df and median_delay_df
    fo4_df = fo4_df.merge(
        median_delay_df.loc[:, ["cell_id", "num_refs", "mdelay"]],
        on="cell_id",
        how="left",
    )
    fo4_df = fo4_df.reset_index()

    return (
        pin_df,
        cell_df,
        net_df,
        pin_edge_df,
        cell_edge_df,
        net_edge_df,
        net_cell_edge_df,
        cell2cell_edge_df,
        fo4_df,
    )


def update_vertices(pin_df, cell_df, net_df, fo4_df):
    #### rename dfs
    pin_df = pin_df.rename(
        columns={
            "pin_name": "name",
            "cell_name": "cellname",
            "net_name": "netname",
            "pin_tran": "tran",
            "pin_slack": "slack",
            "pin_rise_arr": "risearr",
            "pin_fall_arr": "fallarr",
            "input_pin_cap": "cap",
            "is_startpoint": "is_start",
            "is_endpoint": "is_end",
        }
    )
    cell_df = cell_df.rename(
        columns={
            "cell_name": "name",
            "libcell_name": "ref",
            "cell_static_power": "staticpower",
            "cell_dynamic_power": "dynamicpower",
        }
    )
    net_df = net_df.rename(columns={"net_name": "name"})

    fo4_df = fo4_df.rename(columns={"libcell_name": "ref"})

    ### add is_macro, is_seq to pin_df, change pin_dir to bool
    cell_type_df = cell_df.loc[:, ["name", "is_macro", "is_seq"]]
    cell_type_df = cell_type_df.rename(columns={"name": "cellname"})
    pin_df = pin_df.merge(cell_type_df, on="cellname", how="left")
    pin_df["is_macro"] = pin_df["is_macro"].fillna(False)
    pin_df["is_seq"] = pin_df["is_seq"].fillna(False)
    pin_df["dir"] = pin_df["dir"] == 0

    fo4_df["libcell_id"] = range(fo4_df.shape[0])

    ### get cell center loc
    cell_df["x"] = 0.5 * (cell_df.x0 + cell_df.x1)
    cell_df["y"] = 0.5 * (cell_df.y0 + cell_df.y1)

    ### add is_buf is_inv to pin_df
    cell_type_df = cell_df.loc[:, ["name", "is_buf", "is_inv"]]
    cell_type_df = cell_type_df.rename(columns={"name": "cellname"})
    pin_df = pin_df.merge(cell_type_df, on="cellname", how="left")
    pin_df["is_buf"] = pin_df["is_buf"].fillna(False)
    pin_df["is_inv"] = pin_df["is_inv"].fillna(False)

    ### rename cells and nets
    cell_df, pin_df = rename_cells(cell_df, pin_df)
    net_df, pin_df = rename_nets(net_df, pin_df)

    ### get dimensions
    N_pin, _ = pin_df.shape
    N_cell, _ = cell_df.shape
    N_net, _ = net_df.shape
    total_v_cnt = N_pin + N_cell + N_net
    pin_df["id"] = range(N_pin)
    cell_df["id"] = range(N_pin, N_pin + N_cell)
    net_df["id"] = range(N_pin + N_cell, total_v_cnt)

    return pin_df, cell_df, net_df, fo4_df


### generate pandas dataframes by reading csv files
def read_tables_OpenROAD(data_root, design=None):

    cell_cell_path = data_root + "cell_cell_edge.csv"
    cell_pin_path = data_root + "cell_pin_edge.csv"
    cell_path = data_root + "cell_properties.csv"
    net_pin_path = data_root + "net_pin_edge.csv"
    net_path = data_root + "net_properties.csv"
    pin_pin_path = data_root + "pin_pin_edge.csv"
    pin_path = data_root + "pin_properties.csv"
    net_cell_path = data_root + "cell_net_edge.csv"

    all_fo4_delay_path = data_root + "libcell_properties.csv"

    ### load tables
    fo4_df = pd.read_csv(all_fo4_delay_path)

    pin_df = pd.read_csv(pin_path)
    cell_df = pd.read_csv(cell_path)
    net_df = pd.read_csv(net_path)
    cell_cell_df = pd.read_csv(cell_cell_path)
    pin_pin_df = pd.read_csv(pin_pin_path)
    cell_pin_df = pd.read_csv(cell_pin_path)
    net_pin_df = pd.read_csv(net_pin_path)
    net_cell_df = pd.read_csv(net_cell_path)

    return (
        pin_df,
        cell_df,
        net_df,
        pin_pin_df,
        cell_pin_df,
        net_pin_df,
        net_cell_df,
        cell_cell_df,
        fo4_df,
    )


### remove pins and cell with arrival time > 1000 or infinite slack
def rm_invalid_pins_cells(pin_df, cell_df):
    invalid_mask = (np.isinf(pin_df.slack)) | (pin_df.arr > 1000)
    pin_df["invalid"] = False
    pin_df.loc[invalid_mask, ["invalid"]] = True

    cell_invalid = pin_df.groupby("cellname", as_index=False).agg({"invalid": ["sum"]})
    cell_invalid.columns = [
        "_".join(col).rstrip("_") for col in cell_invalid.columns.values
    ]
    cell_invalid["invalid_sum"] = cell_invalid["invalid_sum"] > 0

    pin_df = pin_df.merge(cell_invalid, on="cellname", how="left")
    cell_df = cell_df.merge(
        cell_invalid.rename(columns={"cellname": "name"}), on="name", how="left"
    )
    cell_df["invalid_sum"] = cell_df["invalid_sum"].fillna(True)

    special_mask = (
        (pin_df["is_port"] == True)
        | (pin_df["is_macro"] == True)
        | (pin_df["is_seq"] == True)
    )
    valid_mask = ((special_mask) & (~pin_df["invalid"])) | (
        (~special_mask) & (~pin_df["invalid_sum"])
    )
    pin_df["cell_invalid"] = ~valid_mask

    pin_df = pin_df.loc[(pin_df["cell_invalid"] == False)]
    special_mask = (cell_df["is_macro"]) | (cell_df["is_seq"])
    valid_mask = (special_mask) | ((~special_mask) & (~cell_df["invalid_sum"]))
    cell_df = cell_df.loc[valid_mask]

    pin_df = pin_df.reset_index()
    pin_df = pin_df.drop(columns=["index"])

    cell_df = cell_df.reset_index()
    cell_df = cell_df.drop(columns=["index"])
    return pin_df, cell_df


### remove pins and cell with arrival time > 1000 or infinite slack
def rm_invalid_pins_cells_OpenROAD(pin_df, cell_df):
    invalid_mask = np.isinf(pin_df.slack)
    pin_df["invalid"] = False
    pin_df.loc[invalid_mask, ["invalid"]] = True

    cell_invalid = pin_df.groupby("cellname", as_index=False).agg({"invalid": ["sum"]})
    cell_invalid.columns = [
        "_".join(col).rstrip("_") for col in cell_invalid.columns.values
    ]
    cell_invalid["invalid_sum"] = cell_invalid["invalid_sum"] > 0

    pin_df = pin_df.merge(cell_invalid, on="cellname", how="left")
    cell_df = cell_df.merge(
        cell_invalid.rename(columns={"cellname": "name"}), on="name", how="left"
    )
    cell_df["invalid_sum"] = cell_df["invalid_sum"].fillna(True)

    special_mask = pin_df["is_port"] == True
    valid_mask = ((special_mask) & (~pin_df["invalid"])) | (
        (~special_mask) & (~pin_df["invalid_sum"])
    )
    pin_df["cell_invalid"] = ~valid_mask

    pin_df = pin_df.loc[(pin_df["cell_invalid"] == False)]
    special_mask = (cell_df["is_macro"]) | (cell_df["is_seq"])
    valid_mask = (special_mask) | ((~special_mask) & (~cell_df["invalid_sum"]))
    cell_df = cell_df.loc[valid_mask]

    pin_df = pin_df.reset_index()
    pin_df = pin_df.drop(columns=["index"])

    cell_df = cell_df.reset_index()
    cell_df = cell_df.drop(columns=["index"])
    return pin_df, cell_df


### assign cell size class and get minimum size libcellname
def assign_gate_size_class(fo4_df):
    ### assign cell size class and min size libcellname
    fo4_df["size_class"] = 0
    fo4_df["size_class2"] = 0
    fo4_df["size_cnt"] = 0
    class_cnt = 50
    for i in range(fo4_df.group_id.min(), fo4_df.group_id.max() + 1):
        temp = fo4_df.loc[
            fo4_df.group_id == i, ["group_id", "cell", "cell_delay_fixed_load"]
        ]
        temp = temp.sort_values(by=["cell_delay_fixed_load"], ascending=False)
        fo4_df.loc[temp.index, ["size_class"]] = range(len(temp))
        fo4_df.loc[temp.index, ["size_cnt"]] = len(temp)

        temp["size_cnt"] = 0
        MIN = temp.cell_delay_fixed_load.min()
        MAX = temp.cell_delay_fixed_load.max()
        interval = (MAX - MIN) / class_cnt
        for j in range(1, class_cnt):
            delay_h = MAX - j * interval
            delay_l = MAX - (j + 1) * interval
            if j == (class_cnt - 1):
                delay_l = MIN
            temp.loc[
                (temp.cell_delay_fixed_load < delay_h)
                & (temp.cell_delay_fixed_load >= delay_l),
                ["size_cnt"],
            ] = j
        fo4_df.loc[temp.index, ["size_class2"]] = temp["size_cnt"]

        ### add min size libcellname
        fo4_df.loc[temp.index, ["min_size_cell"]] = temp.cell.to_list()[0]
    return fo4_df


### rename cells with cell0, cell1, ... and update the cell names in pin_df
def rename_cells(cell_df, pin_df):
    ### rename cells ###
    cell_name = cell_df[["name"]]
    cell_name.loc[:, ["new_cellname"]] = [
        "cell" + str(i) for i in range(cell_name.shape[0])
    ]
    pin_df = pin_df.merge(
        cell_name.rename(columns={"name": "cellname"}), on="cellname", how="left"
    )
    idx = pin_df[pd.isna(pin_df.new_cellname)].index

    port_names = ["port" + str(i) for i in range(len(idx))]
    pin_df.loc[idx, "new_cellname"] = port_names
    cell_df["new_cellname"] = cell_name.new_cellname.values
    return cell_df, pin_df


### rename nets with net0, net1, ... and update the net names in pin_df
def rename_nets(net_df, pin_df):
    ### rename nets ###
    net_name = net_df[["name"]]
    net_name.loc[:, ["new_netname"]] = [
        "net" + str(i) for i in range(net_name.shape[0])
    ]
    pin_df = pin_df.merge(
        net_name.rename(columns={"name": "netname"}), on="netname", how="left"
    )
    return net_df, pin_df


### 1) get edge src and tar ids and 2) generate edge_df by merging all edges
def generate_edge_df(
    pin_df,
    cell_df,
    net_df,
    pin_edge_df,
    cell_edge_df,
    net_edge_df,
    net_cell_edge_df,
    cell2cell_edge_df,
):
    edge_id = pd.concat(
        [
            pin_df.loc[:, ["id", "name"]],
            cell_df.loc[:, ["id", "name"]],
            net_df.loc[:, ["id", "name"]],
        ],
        ignore_index=True,
    )
    src = edge_id.copy()
    src = src.rename(columns={"id": "src_id", "name": "src"})
    tar = edge_id.copy()
    tar = tar.rename(columns={"id": "tar_id", "name": "tar"})

    pin_edge_df = pin_edge_df.merge(src, on="src", how="left")
    pin_edge_df = pin_edge_df.merge(tar, on="tar", how="left")

    cell_edge_df = cell_edge_df.merge(src, on="src", how="left")
    cell_edge_df = cell_edge_df.merge(tar, on="tar", how="left")

    net_edge_df = net_edge_df.merge(src, on="src", how="left")
    net_edge_df = net_edge_df.merge(tar, on="tar", how="left")

    net_cell_edge_df = net_cell_edge_df.merge(src, on="src", how="left")
    net_cell_edge_df = net_cell_edge_df.merge(tar, on="tar", how="left")

    cell2cell_edge_df = cell2cell_edge_df.merge(src, on="src", how="left")
    cell2cell_edge_df = cell2cell_edge_df.merge(tar, on="tar", how="left")

    # drop illegal edges
    idx = pin_edge_df[pd.isna(pin_edge_df.src_id)].index
    pin_edge_df = pin_edge_df.drop(idx)
    idx = pin_edge_df[pd.isna(pin_edge_df.tar_id)].index
    pin_edge_df = pin_edge_df.drop(idx)

    idx = cell_edge_df[pd.isna(cell_edge_df.src_id)].index
    cell_edge_df = cell_edge_df.drop(idx)
    idx = cell_edge_df[pd.isna(cell_edge_df.tar_id)].index
    cell_edge_df = cell_edge_df.drop(idx)

    idx = net_edge_df[pd.isna(net_edge_df.src_id)].index
    net_edge_df = net_edge_df.drop(idx)
    idx = net_edge_df[pd.isna(net_edge_df.tar_id)].index
    net_edge_df = net_edge_df.drop(idx)

    idx = net_cell_edge_df[pd.isna(net_cell_edge_df.src_id)].index
    net_cell_edge_df = net_cell_edge_df.drop(idx)
    idx = net_cell_edge_df[pd.isna(net_cell_edge_df.tar_id)].index
    net_cell_edge_df = net_cell_edge_df.drop(idx)

    idx = cell2cell_edge_df[pd.isna(cell2cell_edge_df.src_id)].index
    cell2cell_edge_df = cell2cell_edge_df.drop(idx)
    idx = cell2cell_edge_df[pd.isna(cell2cell_edge_df.tar_id)].index
    cell2cell_edge_df = cell2cell_edge_df.drop(idx)

    edge_df = pd.concat(
        [
            pin_edge_df.loc[:, ["src_id", "tar_id"]],
            cell_edge_df.loc[:, ["src_id", "tar_id"]],
            net_edge_df.loc[:, ["src_id", "tar_id"]],
            net_cell_edge_df.loc[:, ["src_id", "tar_id"]],
            cell2cell_edge_df.loc[:, ["src_id", "tar_id"]],
        ],
        ignore_index=True,
    )

    return (
        pin_edge_df,
        cell_edge_df,
        net_edge_df,
        net_cell_edge_df,
        cell2cell_edge_df,
        edge_df,
    )


### 1) get edge src and tar ids and 2) generate edge_df by merging all edges
def generate_edge_df_OpenROAD(
    pin_df,
    cell_df,
    net_df,
    pin_pin_df,
    cell_pin_df,
    net_pin_df,
    net_cell_df,
    cell_cell_df,
):
    edge_id = pd.concat(
        [
            pin_df.loc[:, ["id", "name"]],
            cell_df.loc[:, ["id", "name"]],
            net_df.loc[:, ["id", "name"]],
        ],
        ignore_index=True,
    )
    src = edge_id.copy()
    src = src.rename(columns={"id": "src_id", "name": "src"})
    tar = edge_id.copy()
    tar = tar.rename(columns={"id": "tar_id", "name": "tar"})

    pin_pin_df = pin_pin_df.merge(src, on="src", how="left")
    pin_pin_df = pin_pin_df.merge(tar, on="tar", how="left")

    cell_pin_df = cell_pin_df.merge(src, on="src", how="left")
    cell_pin_df = cell_pin_df.merge(tar, on="tar", how="left")

    net_pin_df = net_pin_df.merge(src, on="src", how="left")
    net_pin_df = net_pin_df.merge(tar, on="tar", how="left")

    net_cell_df = net_cell_df.merge(src, on="src", how="left")
    net_cell_df = net_cell_df.merge(tar, on="tar", how="left")

    cell_cell_df = cell_cell_df.merge(src, on="src", how="left")
    cell_cell_df = cell_cell_df.merge(tar, on="tar", how="left")

    # drop illegal edges
    idx = pin_pin_df[pd.isna(pin_pin_df.src_id)].index
    pin_pin_df = pin_pin_df.drop(idx)
    idx = pin_pin_df[pd.isna(pin_pin_df.tar_id)].index
    pin_pin_df = pin_pin_df.drop(idx)
    print(f"pin_pin shape: {pin_pin_df.shape}")

    idx = cell_pin_df[pd.isna(cell_pin_df.src_id)].index
    cell_pin_df = cell_pin_df.drop(idx)
    idx = cell_pin_df[pd.isna(cell_pin_df.tar_id)].index
    cell_pin_df = cell_pin_df.drop(idx)
    print(f"cell_pin shape: {cell_pin_df.shape}")

    idx = net_pin_df[pd.isna(net_pin_df.src_id)].index
    net_pin_df = net_pin_df.drop(idx)
    idx = net_pin_df[pd.isna(net_pin_df.tar_id)].index
    net_pin_df = net_pin_df.drop(idx)
    print(f"net_pin shape: {net_pin_df.shape}")

    idx = net_cell_df[pd.isna(net_cell_df.src_id)].index
    net_cell_df = net_cell_df.drop(idx)
    idx = net_cell_df[pd.isna(net_cell_df.tar_id)].index
    net_cell_df = net_cell_df.drop(idx)
    print(f"net_cell shape: {net_cell_df.shape}")

    idx = cell_cell_df[pd.isna(cell_cell_df.src_id)].index
    cell_cell_df = cell_cell_df.drop(idx)
    idx = cell_cell_df[pd.isna(cell_cell_df.tar_id)].index
    cell_cell_df = cell_cell_df.drop(idx)
    print(f"cell_cell shape: {cell_cell_df.shape}")

    edge_df = pd.concat(
        [
            pin_pin_df.loc[:, ["src_id", "tar_id"]],
            cell_pin_df.loc[:, ["src_id", "tar_id"]],
            net_pin_df.loc[:, ["src_id", "tar_id"]],
            net_cell_df.loc[:, ["src_id", "tar_id"]],
            cell_cell_df.loc[:, ["src_id", "tar_id"]],
        ],
        ignore_index=True,
    )

    return pin_pin_df, cell_pin_df, net_pin_df, net_cell_df, cell_cell_df, edge_df


def update_edges(
    pin_pin_df, cell_pin_df, net_pin_df, net_cell_df, cell_cell_df, edge_df
):
    ### get edge dimensions
    N_pin_pin, _ = pin_pin_df.shape
    N_cell_pin, _ = cell_pin_df.shape
    N_net_pin, _ = net_pin_df.shape
    N_net_cell, _ = net_cell_df.shape
    N_cell_cell, _ = cell_cell_df.shape
    # total_e_cnt = N_pin_pin + N_cell_pin + N_net_pin + N_net_cell + N_cell_cell

    edge_df["type"] = 0  # pin_pin
    # edge_df.loc[0:N_pin_edge,["is_net"]] = pin_edge_df.loc[:, "is_net"]
    edge_df.loc[N_pin_pin : N_pin_pin + N_cell_pin, ["type"]] = 1  # cell_pin
    edge_df.loc[
        N_pin_pin + N_cell_pin : N_pin_pin + N_cell_pin + N_net_pin, ["type"]
    ] = 2  # net_pin
    edge_df.loc[
        N_pin_pin
        + N_cell_pin
        + N_net_pin : N_pin_pin
        + N_cell_pin
        + N_net_pin
        + N_net_cell,
        ["type"],
    ] = 3  # net_cell
    edge_df.loc[
        N_pin_pin
        + N_cell_pin
        + N_net_pin
        + N_net_cell : N_pin_pin
        + N_cell_pin
        + N_net_pin
        + N_net_cell
        + N_cell_cell,
        ["type"],
    ] = 4  # cell_cell

    print(
        f" {pin_pin_df.shape=}, {cell_pin_df.shape=}, {net_pin_df.shape=}, {net_cell_df.shape=}, {cell_cell_df.shape=}, {edge_df.shape=}"
    )
    return pin_pin_df, cell_pin_df, net_pin_df, net_cell_df, cell_cell_df, edge_df


if __name__ == "__main__":
    ### read tables ###
    (
        pin_df,
        cell_df,
        net_df,
        pin_pin_df,
        cell_pin_df,
        net_pin_df,
        net_cell_df,
        cell_cell_df,
        fo4_df,
    ) = read_tables_OpenROAD(
        "/mnt/d/shared/for_vdi/mltp/CircuitOps/IRs/asap7/aes/3_4_place_resized/"
    )

    pin_pin_df, cell_pin_df, net_pin_df, net_cell_df, cell_cell_df, edge_df = (
        generate_edge_df_OpenROAD(
            pin_df,
            cell_df,
            net_df,
            pin_pin_df,
            cell_pin_df,
            net_pin_df,
            net_cell_df,
            cell_cell_df,
        )
    )

    pass
