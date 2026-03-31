"""
Train-Test Split with Generalized Compute
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/train-test-split.ipynb

Demonstrates: creating and running a Generalized Compute code object
with multiple output datasets and naming templates.
"""

from getpass import getpass
import rhino_health as rh
from rhino_health.lib.endpoints.code_object.code_object_dataclass import (
    CodeObjectCreateInput,
    CodeTypes,
    CodeObjectRunInput,
)

# --- Login ---
my_username = "my_email@example.com"
my_workgroup_ecr_repo = "rhino-gc-workgroup-XXXXXXXXXXXXXX"
my_image_name = "train-test-split"
ecr_base_uri = rh.lib.constants.ECRService.PROD_URL
session = rh.login(username=my_username, password=getpass())

# --- Create Code Object ---
project_uid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
data_schema_uid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

creation_params = CodeObjectCreateInput(
    name="Train Test Split",
    description="Train Test Split",
    code_type=CodeTypes.GENERALIZED_COMPUTE,
    config={"container_image_uri": f"{ecr_base_uri}/{my_workgroup_ecr_repo}:{my_image_name}"},
    project_uid=project_uid,
    input_data_schema_uids=[data_schema_uid],
    output_data_schema_uids=[data_schema_uid, data_schema_uid],  # two outputs: train + test
)
code = session.code_object.create_code_object(creation_params)

# --- Run Code Object ---
input_dataset_uid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
run_params = CodeObjectRunInput(
    code_object_uid=code.uid,
    input_dataset_uids=[[input_dataset_uid]],
    output_dataset_naming_templates=[
        '{{ input_dataset_names.0 }} - Train',
        '{{ input_dataset_names.0 }} - Test'
    ],
    timeout_seconds=300,
)

print("Starting train_test_split")
code_run = session.code_object.run_code_object(run_params)
run_result = code_run.wait_for_completion()
print(f"Status: '{run_result.status.value}'")
print(f"Errors: {run_result.results_info.get('errors') if run_result.results_info else None}")
