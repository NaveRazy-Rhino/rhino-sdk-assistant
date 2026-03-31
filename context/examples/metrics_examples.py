"""
Comprehensive Metrics Examples
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/metrics_examples.ipynb

Demonstrates: Mean, TwoByTwoTable, OddsRatio, ChiSquare, TTest, OneWayANOVA.
"""

from getpass import getpass
import rhino_health
from rhino_health.lib.metrics import Mean
from rhino_health.lib.metrics.epidemiology.two_by_two_table_based_metrics import (
    TwoByTwoTable, OddsRatio
)
from rhino_health.lib.metrics.statistics_tests import ChiSquare, TTest, OneWayANOVA

# --- Login ---
my_username = "my_email@example.com"
session = rhino_health.login(username=my_username, password=getpass())
project = session.project.get_project_by_name("PROJECT_NAME")
dataset_uids = [
    project.get_dataset_by_name("DATASET_1"),
    project.get_dataset_by_name("DATASET_2"),
]

# --- Mean ---
mean_config = Mean(variable="Weight")
session.project.aggregate_dataset_metric(dataset_uids, mean_config)

# --- Two-by-Two Table ---
tbtt = TwoByTwoTable(
    variable="id",
    detected_column_name="Pneumonia",
    exposed_column_name="Smoking",
)
table = session.project.aggregate_dataset_metric(dataset_uids, tbtt)

# --- Odds Ratio ---
odds_ratio = OddsRatio(
    variable="id",
    detected_column_name="Pneumonia",
    exposed_column_name="Smoking",
)
session.project.aggregate_dataset_metric(dataset_uids, odds_ratio)

# --- Chi-Square ---
chi_square = ChiSquare(
    variable="id",
    variable_1="Pneumonia",
    variable_2="Smoking"
)
session.project.aggregate_dataset_metric(dataset_uids, chi_square)

# --- T-Test ---
t_test = TTest(numeric_variable="Spo2 Level", categorical_variable="Pneumonia")
session.project.aggregate_dataset_metric(dataset_uids, t_test)

# --- One-Way ANOVA ---
anova_config = OneWayANOVA(
    variable="id",
    numeric_variable="Spo2 Level",
    categorical_variable="Inflammation Level",
)
result = project.aggregate_dataset_metric(dataset_uids, anova_config)
