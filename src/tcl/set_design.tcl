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

# Please config CUSTOM PART 1 / CUSTOM PART 2

################## CUSTOM PART 1 START ##################
### SET OpenROAD-flow-scripts FLOW DIRECTORY ###
set ORFS_FLOW_DIR "/home/xldu/repos/OpenROAD-flow-scripts/flow"

### SET DESIGN ###
set DESIGN_NAME gcd

### SET PLATFORM ###
set PLATFORM asap7
### FIXED LOAD CELL
set fixed_load_cell "INVx1_ASAP7_75t_R"
# set fixed_load_cell "INV_X1"

### SET OUTPUT DIRECTORY ###
set OUTPUT_DIR "output/IRs/${PLATFORM}/${DESIGN_NAME}"
################### CUSTOM PART 1 END ###################

####### INTERNAL DEFINTIONS: DO NOT MODIFY BELOW ########
### TARGET TABLES ###
file mkdir "${OUTPUT_DIR}"

set cell_file "${OUTPUT_DIR}/cell_properties.csv"
set libcell_file "${OUTPUT_DIR}/libcell_properties.csv"
set pin_file "${OUTPUT_DIR}/pin_properties.csv"
set net_file "${OUTPUT_DIR}/net_properties.csv"
set cell_pin_file "${OUTPUT_DIR}/cell_pin_edge.csv"
set net_pin_file "${OUTPUT_DIR}/net_pin_edge.csv"
set pin_pin_file "${OUTPUT_DIR}/pin_pin_edge.csv"
set cell_net_file "${OUTPUT_DIR}/cell_net_edge.csv"
set cell_cell_file "${OUTPUT_DIR}/cell_cell_edge.csv"

### ORFS SOURCES ###
set ORFS_DESIGN_DIR "${ORFS_FLOW_DIR}/designs/${PLATFORM}/${DESIGN_NAME}/base"
set ORFS_LOG_DIR "${ORFS_FLOW_DIR}/logs/${PLATFORM}/${DESIGN_NAME}/base"
set ORFS_OBJECT_DIR "${ORFS_FLOW_DIR}/objects/${PLATFORM}/${DESIGN_NAME}/base"
set ORFS_PLATFORM_DIR "${ORFS_FLOW_DIR}/platforms/${PLATFORM}"
set ORFS_REPORT_DIR "${ORFS_FLOW_DIR}/reports/${PLATFORM}/${DESIGN_NAME}/base"
set ORFS_RESULT_DIR "${ORFS_FLOW_DIR}/results/${PLATFORM}/${DESIGN_NAME}/base"

set ORFS_2_FLOORPLAN_SDC "${ORFS_RESULT_DIR}/2_floorplan.sdc"
set ORFS_3_3_PLACE_GP_ODB "${ORFS_RESULT_DIR}/3_3_place_gp.odb"
set ORFS_3_4_PLACE_RESIZED_ODB "${ORFS_RESULT_DIR}/3_4_place_resized.odb"
### `estimate_parasitics -placement`
### `estimate_parasitics -global_routing`, after `global_route`
### No net_coupling,net_res in net_prop
set ORFS_3_PLACE_ODB "${ORFS_RESULT_DIR}/3_place.odb"
set ORFS_4_BEFORE_RSZ_ODB "${ORFS_RESULT_DIR}/4_before_rsz.odb"
set ORFS_4_AFTER_RSZ_ODB "${ORFS_RESULT_DIR}/4_after_rsz.odb"
set ORFS_4_CTS_ODB "${ORFS_RESULT_DIR}/4_cts.odb"
### `extract_parasitics -ext_model_file $RCX_FILE` after detailed_route for SPEF
set ORFS_5_ROUTE_ODB "${ORFS_RESULT_DIR}/5_route.odb"
set ORFS_6_FINAL_ODB "${ORFS_RESULT_DIR}/6_final.odb"
set ORFS_6_FINAL_SDC "${ORFS_RESULT_DIR}/6_final.sdc"
set ORFS_6_FINAL_SPEF "${ORFS_RESULT_DIR}/6_final.spef"
###### INTERNAL DEFINTIONS: DO NOT MODIFY ABOVE #######

### CHOOSE ONE SETTING BELOW AND COMMENT THE OTHER ###

##### CUSTOM PART 2.1: FOR FINAL RESULTS PARSING END #####
### PROBLEM WITH ASAP7
# # set LIB_FILES [glob ${ORFS_OBJECT_DIR}/lib/*.lib]
# set LIB_FILES [glob ./design_resource/${PLATFORM}/lib/*.lib]
# set TECH_LEF_FILE [glob ${ORFS_PLATFORM_DIR}/lef/*tech*lef]
# set LEF_FILES [glob ${ORFS_PLATFORM_DIR}/lef/*.lef]
# set RCX_FILE "${ORFS_PLATFORM_DIR}/rcx_patterns.rules"
# set DEF_FILE "${ORFS_RESULT_DIR}/6_final.def"
# set SDC_FILE "${ORFS_RESULT_DIR}/6_final.sdc"
# set NETLIST_FILE "${ORFS_RESULT_DIR}/6_final.v"
# set SPEF_FILE "${ORFS_RESULT_DIR}/6_final.spef"
# set SETRC_FILE "${ORFS_PLATFORM_DIR}/setRC.tcl"
##### CUSTOM PART 2.1: FOR FINAL RESULTS PARSING END #####

######### CUSTOM PART 2.2: FOR .odb PARSING START #########
# set rcx rules means extract_parasitics, otherwise estimate
# set RCX_FILE "${ORFS_PLATFORM_DIR}/rcx_patterns.rules"
# set SPEF_FILE "${ORFS_RESULT_DIR}/6_final.spef"
set LIB_FILES [glob ./design_resource/${PLATFORM}/lib/*.lib]
set SETRC_FILE "${ORFS_PLATFORM_DIR}/setRC.tcl"
# set ODB_FILE ${ORFS_6_FINAL_ODB}
set ODB_FILE ${ORFS_3_3_PLACE_GP_ODB}
# set ODB_FILE ${ORFS_4_CTS_ODB}
set SDC_FILE ${ORFS_2_FLOORPLAN_SDC}
########## CUSTOM PART 2.2: FOR .odb PARSING END ##########