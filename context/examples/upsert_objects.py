"""
Creating and Updating Objects (Upsert Pattern)
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/upsert-objects.ipynb

Demonstrates: create/get/version/search for datasets and code objects.
Key patterns: return_existing, add_version_if_exists, VersionMode, NameFilterMode.
"""

from getpass import getpass
import rhino_health as rh
from rhino_health.lib.endpoints.endpoint import NameFilterMode, VersionMode
from rhino_health.lib.endpoints.code_object.code_object_dataclass import CodeObjectCreateInput
from rhino_health.lib.endpoints.dataset.dataset_dataclass import DatasetCreateInput

# --- Login ---
my_username = "my_email@example.com"
my_workgroup_ecr_repo = "rhino-gc-workgroup-XXXXXXXXXXXXXX"
my_image_name = "upserting-objects"
ecr_base_uri = rh.lib.constants.ECRService.PROD_URL
session = rh.login(username=my_username, password=getpass())

# --- Get Project ---
projects = session.project.search_for_projects_by_name("Test")
print([(x.name, x.uid) for x in projects][:10])

project = session.project.get_project_by_name("Test2")
print(project.dict(include={'uid', 'name', 'description'}))

# --- Create Dataset ---
data_schema_uid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

dataset_input = DatasetCreateInput(
    name="Upsert Dataset",
    description="Test Upsert Dataset",
    project_uid=project.uid,
    workgroup_uid=project.primary_workgroup_uid,
    data_schema_uid=data_schema_uid,
    csv_filesystem_location="/rhino_data/test/dataset_data.csv",
    method="filesystem",
    is_data_deidentified=True,
)
dataset = session.dataset.add_dataset(dataset_input)

# return_existing=True (default) → returns existing if name matches
duplicate = session.dataset.add_dataset(dataset_input)
assert duplicate.uid == dataset.uid

# add_version_if_exists=True → creates new version
new_version = session.dataset.add_dataset(dataset_input, return_existing=False, add_version_if_exists=True)
print(new_version.uid, new_version.version)

# --- Get Dataset by name ---
found = project.get_dataset_by_name("Upsert Dataset")
older = project.get_dataset_by_name("Upsert Dataset", version=1)
all_versions = project.search_for_datasets_by_name("upsert", version=VersionMode.ALL, name_filter_mode=NameFilterMode.CONTAINS)
non_existent = project.get_dataset_by_name("I do not exist")  # returns None

# --- Create Code Object ---
image_uri = f"{ecr_base_uri}/{my_workgroup_ecr_repo}:{my_image_name}"
test_code_object = CodeObjectCreateInput(
    name="Upsert Code Object",
    description="Test",
    input_data_schema_uids=[data_schema_uid],
    output_data_schema_uids=[data_schema_uid],
    project_uid=project.uid,
    code_type="Generalized Compute",
    config={"container_image_uri": image_uri},
)
code_object = session.code_object.create_code_object(test_code_object)

# Versioning works the same as datasets
new_version_co = session.code_object.create_code_object(test_code_object, return_existing=False, add_version_if_exists=True)

# --- Search Code Objects ---
partial_search = session.code_object.search_for_code_objects_by_name(
    "Test", version=1, name_filter_mode=NameFilterMode.CONTAINS
)
latest = session.code_object.search_for_code_objects_by_name(
    "Upsert", version=VersionMode.LATEST, name_filter_mode=NameFilterMode.CONTAINS
)
all_co = session.code_object.search_for_code_objects_by_name(
    "Upsert", version=VersionMode.ALL, name_filter_mode=NameFilterMode.CONTAINS
)
