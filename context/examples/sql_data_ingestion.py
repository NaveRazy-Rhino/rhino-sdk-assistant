"""
SQL Data Ingestion — Running On-Prem SQL Queries via FCP
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/sql-data-ingestion.ipynb

Demonstrates: connecting to on-prem SQL databases, running metrics on queries,
importing query results as datasets.
"""

from getpass import getpass
from pprint import pprint
import rhino_health as rh
from rhino_health.lib.endpoints.sql_query.sql_query_dataclass import (
    SQLQueryImportInput,
    SQLQueryInput,
    SQLServerTypes,
    ConnectionDetails,
)
from rhino_health.lib.metrics import Count, FilterType, Mean, StandardDeviation

# --- Login ---
my_username = "my_email@example.com"
session = rh.login(username=my_username, password=getpass())

# --- Connection Setup ---
connection_details = ConnectionDetails(
    server_user="db_user",
    password="db_password",
    server_type=SQLServerTypes.POSTGRESQL,
    server_url="myserver:5432",
    db_name="mydb"
)

project_uid = session.project.get_project_by_name('Your project name').uid
workgroup_uid = session.project.get_collaborating_workgroups(project_uid)[0].uid

# --- Run Exploratory Query (returns metrics, not raw data) ---
query_run_params = SQLQueryInput(
    session=session,
    project=project_uid,
    workgroup=workgroup_uid,
    connection_details=connection_details,
    sql_query="SELECT * FROM patients WHERE age > 30",
    timeout_seconds=600,
    metric_definitions=[Mean(variable="age"), Count(variable="id")]
)
response = session.sql_query.run_sql_query(query_run_params)
pprint(f"Metric results: {response.dict()}")

# --- Import Query Results as Dataset ---
dataschemas = session.project.get_data_schemas(project_uid)
dataschema = dataschemas[0]

import_run_params = SQLQueryImportInput(
    session=session,
    project=project_uid,
    workgroup=workgroup_uid,
    connection_details=connection_details,
    dataset_name="my_dataset",
    data_schema_uid=dataschema.uid,
    timeout_seconds=600,
    is_data_deidentified=False,
    sql_query="SELECT * FROM patients",
)
response = session.sql_query.import_dataset_from_sql_query(import_run_params)
pprint(f"Import result: {response.dict()}")
