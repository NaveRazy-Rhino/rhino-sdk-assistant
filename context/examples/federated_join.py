"""
Federated Join Tutorial
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/federated_join/

Demonstrates: SQL-like joins across distributed datasets without centralizing data.
Two modes: INTERSECTION (inner join) and UNION (full outer join).
"""

import pandas as pd
import numpy as np
from getpass import getpass
import rhino_health
from rhino_health.lib.endpoints.project.project_dataclass import ProjectCreateInput
from rhino_health.lib.endpoints.data_schema.data_schema_dataclass import DataSchemaCreateInput
from rhino_health.lib.endpoints.dataset.dataset_dataclass import DatasetCreateInput
from rhino_health.lib.metrics import Count, Mean, StandardDeviation
from rhino_health.lib.metrics.base_metric import JoinMode

# --- Login ---
session = rhino_health.login(username="my_email@example.com", password=getpass())

WORKGROUP_UID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

# --- Create Project ---
new_project = ProjectCreateInput(
    name="Federated Join Metrics",
    description="Example Project for Federated Join",
    type="Validation",
    primary_workgroup_uid=WORKGROUP_UID,
)
project = session.project.add_project(new_project)

# --- Create Data Schema ---
dataschema_input = DataSchemaCreateInput(
    name="Federated Join Input Schema",
    description="Federated Join Input Schema",
    primary_workgroup_uid=WORKGROUP_UID,
    projects=[project.uid],
    file_path="./FederatedDataSchema.csv",
)
dataschema = session.data_schema.create_data_schema(dataschema_input)

# --- Import Datasets ---
DATA_LOCATION = "/rhino_data"

filter_dataset = session.dataset.add_dataset(DatasetCreateInput(
    name="Blood Test Results",
    description="Identifiers with Blood Type",
    project_uid=project.uid,
    workgroup_uid=WORKGROUP_UID,
    data_schema_uid=dataschema.uid,
    csv_filesystem_location=f"{DATA_LOCATION}/FederatedJoinFilterDataset.csv",
    method="filesystem",
    is_data_deidentified=True,
))

query_dataset = session.dataset.add_dataset(DatasetCreateInput(
    name="SpO2 Values on 1/1",
    description="Identifiers with SPO2 and Gender",
    project_uid=project.uid,
    workgroup_uid=WORKGROUP_UID,
    data_schema_uid=dataschema.uid,
    csv_filesystem_location=f"{DATA_LOCATION}/FederatedJoinDataset.csv",
    method="filesystem",
    is_data_deidentified=True,
))


# =============================================
# INTERSECTION MODE (Left Inner Join)
# =============================================

# --- Basic Join: Mean SpO2 where Age > 35 (from filter dataset) ---
configuration = Mean(
    variable="SpO2",
    join_field={"data_column": "UID", "filter_column": "Age", "filter_value": 35, "filter_type": ">"},
)
federated_results = session.project.joined_dataset_metric(
    filter_datasets=[filter_dataset.uid],
    query_datasets=[query_dataset.uid],
    configuration=configuration
)
print(f"Federated Mean: {federated_results.output}")

# --- Join + Variable Filter: Mean SpO2 for Males, Age > 35 ---
configuration = Mean(
    variable={"data_column": "SpO2", "filter_column": "Gender", "filter_value": "m", "filter_type": "="},
    join_field={"data_column": "UID", "filter_column": "Age", "filter_value": 35, "filter_type": ">"},
)
federated_results = session.project.joined_dataset_metric(
    filter_datasets=[filter_dataset.uid],
    query_datasets=[query_dataset.uid],
    configuration=configuration
)

# --- Join + Group By ---
configuration = Mean(
    variable="SpO2",
    join_field={"data_column": "UID", "filter_column": "Age", "filter_value": 35, "filter_type": ">"},
    group_by={"groupings": ["Gender"]},
)
federated_results = session.project.joined_dataset_metric(
    filter_datasets=[filter_dataset.uid],
    query_datasets=[query_dataset.uid],
    configuration=configuration
)

# --- Multi-Filter: filters from different datasets ---
configuration = Mean(
    variable="SpO2",
    join_field="UID",
    data_filters=[
        {"filter_column": "Age", "filter_value": 35, "filter_type": ">"},
        {"filter_column": "BloodType", "filter_value": "a", "filter_type": "=",
         "filter_dataset": filter_dataset.uid},
        {"filter_column": "Gender", "filter_value": "m", "filter_type": "=",
         "filter_dataset": query_dataset.uid},
    ],
)
federated_results = session.project.joined_dataset_metric(
    filter_datasets=[filter_dataset.uid],
    query_datasets=[query_dataset.uid],
    configuration=configuration
)


# =============================================
# UNION MODE (Full Outer Join)
# =============================================

# Import additional datasets for union
dataset2 = session.dataset.add_dataset(DatasetCreateInput(
    name="SpO2 Values (Old)", description="Old SpO2 data",
    project_uid=project.uid, workgroup_uid=WORKGROUP_UID,
    data_schema_uid=dataschema.uid,
    csv_filesystem_location=f"{DATA_LOCATION}/FederatedJoinUnionDataset1.csv",
    method="filesystem", is_data_deidentified=True,
))
dataset3 = session.dataset.add_dataset(DatasetCreateInput(
    name="SpO2 at Lab", description="Lab SpO2 data",
    project_uid=project.uid, workgroup_uid=WORKGROUP_UID,
    data_schema_uid=dataschema.uid,
    csv_filesystem_location=f"{DATA_LOCATION}/FederatedJoinUnionDataset2.csv",
    method="filesystem", is_data_deidentified=True,
))
union_dataset_uids = [query_dataset.uid, dataset2.uid, dataset3.uid]

# --- Union with per-dataset filters ---
configuration = Mean(
    variable="SpO2",
    join_field="UID",
    join_mode="union",
    data_filters=[
        {"filter_column": "Age", "filter_value": 35, "filter_type": ">"},
        {"filter_column": "Gender", "filter_value": "m", "filter_type": "=",
         "filter_dataset": dataset2.uid},
        {"filter_column": "Gender", "filter_value": "f", "filter_type": "=",
         "filter_dataset": dataset3.uid},
    ],
)
federated_results = session.project.joined_dataset_metric(
    query_datasets=union_dataset_uids,
    configuration=configuration
)

# --- Union with FilterVariable shorthand ---
configuration = Mean(
    variable={"data_column": "SpO2", "filter_column": "Gender", "filter_value": "m", "filter_type": "="},
    join_field={"data_column": "UID", "filter_column": "Age", "filter_value": 35, "filter_type": ">"},
    join_mode=JoinMode.UNION
)
federated_results = session.project.joined_dataset_metric(
    query_datasets=union_dataset_uids,
    configuration=configuration
)
