"""
Cox Proportional Hazard Calculations
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/cox.ipynb

Demonstrates: federated Cox PH regression across multiple sites.
"""

from getpass import getpass
import rhino_health
import pandas as pd
from rhino_health.lib.metrics import Cox

# --- Login ---
my_username = "my_email@example.com"
session = rhino_health.login(username=my_username, password=getpass())

# --- Load Project & Datasets ---
project = session.project.get_project_by_name("PROJECT_NAME")
dataset_uids = [
    project.get_dataset_by_name("DATASET_1"),
    project.get_dataset_by_name("DATASET_2"),
]

# --- Expected data format ---
# pd.DataFrame({
#     'Time': [84.0, 97.0, 91.0, 90.0, 124.0, 97.0],
#     'Event': [1, 0, 0, 1, 1, 1],
#     'COV1': [0.3, 0.51, 0.12, 0.03, 0.413, 0.3],
#     'COV2': [5.3, 1.51, 1.8, 0.03, 13, 0.3]
# })

# --- Cox Model ---
time_variable = "Time"
event_variable = "Event"
covariates = ["COV1", "COV2"]

metric_configuration = Cox(
    time_variable=time_variable,
    event_variable=event_variable,
    covariates=covariates,
    initial_beta="mean",
    max_iterations=50
)

results = project.aggregate_dataset_metric(
    dataset_uids=[str(dataset.uid) for dataset in dataset_uids],
    metric_configuration=metric_configuration
)
print(results.output)
