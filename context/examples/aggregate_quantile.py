"""
Federated Percentiles with Differential Privacy
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/aggregate_quantile_example.ipynb

Demonstrates: calculating aggregate percentiles across federated datasets.
"""

from getpass import getpass
import rhino_health
from rhino_health.lib.metrics import Percentile

# --- Login ---
my_username = "my_email@example.com"
session = rhino_health.login(username=my_username, password=getpass())

# --- Load Project & Datasets ---
project = session.project.get_project_by_name("PROJECT_NAME")
datasets = [
    project.get_dataset_by_name("DATASET_1"),
    project.get_dataset_by_name("DATASET_2"),
]

# --- 90th Percentile ---
metric_configuration = Percentile(variable="Weight", percentile=90)
result = session.project.aggregate_dataset_metric(
    dataset_uids=[str(dataset.uid) for dataset in datasets],
    metric_configuration=metric_configuration,
)
print(f"Aggregate Weight 90th Percentile: {result.output['Weight']}")

# --- 10th Percentile ---
metric_configuration = Percentile(variable="Weight", percentile=10)
result = session.project.aggregate_dataset_metric(
    dataset_uids=[str(dataset.uid) for dataset in datasets],
    metric_configuration=metric_configuration,
)
print(f"Aggregate Weight 10th Percentile: {result.output['Weight']}")
