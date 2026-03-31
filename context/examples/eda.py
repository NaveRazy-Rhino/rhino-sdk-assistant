"""
Exploratory Data Analysis with Rhino Health SDK
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/eda.ipynb

Demonstrates: federated analytics — per-site and aggregate metrics with filtering and grouping.
"""

from getpass import getpass
import rhino_health
from rhino_health.lib.metrics import Count, FilterType, Mean, StandardDeviation

# --- Login ---
my_username = "my_email@example.com"
session = rhino_health.login(username=my_username, password=getpass())

# --- Load Datasets ---
FIRST_TEST_DATASET_ID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
SECOND_TEST_DATASET_ID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
first_dataset = session.dataset.get_dataset(FIRST_TEST_DATASET_ID)
second_dataset = session.dataset.get_dataset(SECOND_TEST_DATASET_ID)
all_datasets = [first_dataset.uid, second_dataset.uid]

# --- Per-Site Count ---
count_verification = Count(variable="Height")
individual_results = {
    "site1": session.dataset.get_dataset_metric(first_dataset.uid, count_verification).output,
    "site2": session.dataset.get_dataset_metric(second_dataset.uid, count_verification).output,
}

# --- Per-Site Mean ---
mean_verification = Mean(variable="Height")
individual_results = {
    "site1": session.dataset.get_dataset_metric(first_dataset.uid, mean_verification).output,
    "site2": session.dataset.get_dataset_metric(second_dataset.uid, mean_verification).output,
}

# --- Filtered Mean (Gender = "M") ---
mean_verification = Mean(
    variable={
        "data_column": "Height",
        "filter_column": "Gender",
        "filter_value": "M"
    }
)
individual_results = {
    "site1": session.dataset.get_dataset_metric(first_dataset.uid, mean_verification).output,
    "site2": session.dataset.get_dataset_metric(second_dataset.uid, mean_verification).output,
}

# --- Grouped Mean (by Gender) ---
mean_verification = Mean(
    variable="Height",
    group_by={"groupings": ["Gender"]},
)
individual_results = {
    "site1": session.dataset.get_dataset_metric(first_dataset.uid, mean_verification).output,
    "site2": session.dataset.get_dataset_metric(second_dataset.uid, mean_verification).output,
}

# --- Aggregated across sites ---
grouped_results = session.project.aggregate_dataset_metric(all_datasets, mean_verification)
print(f"{grouped_results.output}")

# --- Complex: filter Weight >= 70, group by Gender ---
configuration = Mean(
    variable={
        "data_column": "Height",
        "filter_column": "Weight",
        "filter_value": 70,
        "filter_type": FilterType.GREATER_THAN_EQUAL,
    },
    group_by={"groupings": ["Gender"]}
)
grouped_results = session.project.aggregate_dataset_metric(all_datasets, configuration)

# --- Range filter: 70 <= Weight <= 100, group by Gender ---
configuration = Mean(
    variable={
        "data_column": "Height",
        "filter_column": "Weight",
        "filter_value": {
            "lower": {"filter_value": 70, "filter_type": FilterType.GREATER_THAN_EQUAL},
            "upper": {"filter_value": 100, "filter_type": FilterType.LESS_THAN_EQUAL},
        },
        "filter_type": FilterType.BETWEEN,
    },
    group_by={"groupings": ["Gender"]}
)
grouped_results = session.project.aggregate_dataset_metric(all_datasets, configuration)

# --- Standard Deviation ---
configuration = StandardDeviation(variable="Height")
individual_results = {
    "site1": session.dataset.get_dataset_metric(first_dataset.uid, configuration).output,
    "site2": session.dataset.get_dataset_metric(second_dataset.uid, configuration).output,
}
