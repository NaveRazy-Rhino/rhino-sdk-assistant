"""
FHIR Data Pipeline — End-to-End Harmonization
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/fhir-pipeline.py

Demonstrates: data harmonization → FHIR resource generation → CSV export.
Full pipeline using code objects and data harmonization.
"""

import getpass
from pprint import pprint
import rhino_health as rh
from rhino_health.lib.endpoints.code_object.code_object_dataclass import (
    CodeObjectRunInput
)
from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import (
    DataHarmonizationRunInput
)


def main():
    # --- Login ---
    my_username = ""  # Replace with your email
    session = rh.login(username=my_username, password=getpass.getpass())

    project_uid = '2d32128d-3a27-408a-9315-e7e37c458718'
    workgroup_uid = 'c50eb65a-7c61-422f-84a5-dd515fff5c24'

    # --- Step 1: Transform Data to FlatFHIR ---
    print("Transforming Data to FlatFHIR")
    data_harmonization_params = DataHarmonizationRunInput(
        input_dataset_uids=['1f124ad2-6a14-4bcd-ba00-9951cdf33758'],
        semantic_mapping_uids_by_vocabularies={}
    )
    code_run = session.code_object.run_data_harmonization(
        code_object_uid='120569bb-6c9e-4760-9a1d-1151d6e57ca4',
        run_params=data_harmonization_params
    )
    run_result = code_run.wait_for_completion()
    output_dataset_uid = run_result.output_dataset_uids.root[0].root[2].root[0]

    # --- Step 2: Generate FHIR Resources ---
    print("Generating FHIR Resources")
    code_object_params = CodeObjectRunInput(
        code_object_uid='b54d8b44-3b10-4a64-85e0-767df07aa40b',
        input_dataset_uids=[[output_dataset_uid]],
        timeout_seconds=8600
    )
    code_run = session.code_object.run_code_object(code_object_params)
    run_result = code_run.wait_for_completion()
    fhir_dataset_uid = code_run.code_run.output_dataset_uids.root[0].root[0].root[0]

    # --- Step 3: Export as CSV ---
    print("Saving FHIR JSON To Rhino Client")
    export_response = session.dataset.export_dataset(
        dataset_uid=fhir_dataset_uid,
        output_location='/rhino_data/fhir_data/',
        output_format='csv'
    )
    return export_response


if __name__ == "__main__":
    main()
