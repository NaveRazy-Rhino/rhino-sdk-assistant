"""
Using External Storage Files in Code Runs
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/runtime_external_files.ipynb

Demonstrates: creating a Python code object that references files from
the workgroup's S3 bucket, using external_storage_file_paths.
"""

from rhino_health.lib.endpoints.code_object.code_object_dataclass import (
    CodeObjectCreateInput,
    CodeObjectRunInput,
    CodeTypes,
)
from textwrap import dedent

# --- Create Code Object that reads external files ---
new_code_object = CodeObjectCreateInput(
    name="Example code object",
    description="A code that references a file",
    code_type=CodeTypes.PYTHON_CODE,
    version=0,
    project_uid=project.uid,
    config={
        "python_version": "3.9",
        "requirements": ["numpy == 1.22.*", "pandas ~= 1.4.2"],
        "python_code": dedent("""
            from pathlib import Path
            text = Path('/external_data/data_files/example_file1.txt').read_text()
        """),
        "code_execution_mode": "snippet",
    },
    input_data_schema_uids=[None],
    output_data_schema_uids=[None],
)
code_object = session.code_object.create_code_object(new_code_object)

# --- Run with external files ---
# Files in S3 bucket are extracted to /external_data/ maintaining folder structure
run_params = CodeObjectRunInput(
    code_object_uid=code_object.uid,
    input_dataset_uids=[[dataset.uid]],
    output_dataset_names_suffix="test",
    external_storage_file_paths=[
        "data_files/example_file1.txt",
        "data_files/example_file2.txt",
    ],
    timeout_seconds=600,
    sync=True,
)
run_result = session.code_object.run_code_object(run_params)
