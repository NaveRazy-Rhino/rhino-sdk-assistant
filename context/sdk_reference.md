# Rhino Health SDK — API Reference

> SDK Version: 2.1.20  
> Source: https://rhinohealth.github.io/rhino_sdk_docs/html/index.html

---

## Authentication & RhinoSession

**Full `rh.login()` signature:**
```python
import rhino_health as rh

session = rh.login(
    username="my_email@example.com",       # or None if using authentication_details
    password="...",                         # or None if using authentication_details
    otp_code="123456",                     # optional — required if 2FA is enabled
    rhino_api_url="https://prod.rhinohealth.com/api/",  # default is PROD; change for dev/QA
    authentication_details=None,           # alternative to username/password (SSO, session reuse)
    sdk_version="stable",                  # use default
    show_traceback=False,                  # include traceback info in errors
    accept_nonstandard_ssl_certs=False,    # for private envs behind corporate firewalls
) → RhinoSession
```

**Common login patterns:**
```python
import rhino_health as rh
from getpass import getpass

# Basic login (defaults to production)
session = rh.login(username="my_email@example.com", password=getpass())

# With MFA:
session = rh.login(username="my_email@example.com", password=getpass(), otp_code="123456")

# Non-production environment (dev1, QA, etc.):
from rhino_health.lib.constants import ApiEnvironment
session = rh.login(
    username="my_email@example.com",
    password=getpass(),
    rhino_api_url=ApiEnvironment.DEV1_AWS_URL,
)

# SSO login (Google):
session = rh.login(authentication_details={
    "sso_access_token": "MyAccessToken",
    "sso_provider": "google",
    "sso_client": "my_hospital",
})

# SSO login (Azure AD):
session = rh.login(authentication_details={
    "sso_access_token": "MyAccessToken",
    "sso_id_token": "MyIdToken",
    "sso_provider": "azure_ad",
})

# Session reuse (persist and restore):
session_info = old_session.session_info()
session = rh.login(authentication_details=session_info)
```

`rh.login()` returns a `RhinoSession` object. `RhinoSession` inherits from `RhinoClient`.

**Key session methods:**
```python
session.current_user          # → User (authenticated user)
session.session_info()        # → dict {session_token, session_timeout, ...} for persistence/reuse
session.switch_user(authentication_details, otp_code=None)
session.get_container_image_uri(image_tag, rhino_common_image=False)
```

**ECR base URL:**
```python
import rhino_health as rh
ecr_base_uri = rh.lib.constants.ECRService.PROD_URL
```

---

## ApiEnvironment

**Import:** `from rhino_health.lib.constants import ApiEnvironment`

All API URLs end with `/api/`. Pass to `rh.login(rhino_api_url=...)`.

| Constant | URL |
|----------|-----|
| `ApiEnvironment.PROD_API_URL` / `PROD_AWS_URL` | `https://prod.rhinohealth.com/api/` (default) |
| `ApiEnvironment.PROD_GCP_URL` | `https://prod.rhinofcp.com/api/` |
| `ApiEnvironment.PROD_US2_GCP_URL` | `https://us2.rhinofcp.com/api/` |
| `ApiEnvironment.DEV1_AWS_URL` | `https://dev1.rhinohealth.com/api/` |
| `ApiEnvironment.DEV1_GCP_URL` | `https://dev1.rhinofcp.com/api/` |
| `ApiEnvironment.DEV2_AWS_URL` | `https://dev2.rhinohealth.com/api/` |
| `ApiEnvironment.DEV3_AWS_URL` | `https://dev3.rhinohealth.com/api/` |
| `ApiEnvironment.QA_AWS_URL` / `QA_URL` | `https://qa-cloud.rhinohealth.com/api/` |
| `ApiEnvironment.QA_GCP_URL` | `https://qa-cloud.rhinofcp.com/api/` |
| `ApiEnvironment.STAGING_AWS_URL` | `https://staging.rhinohealth.com/api/` |
| `ApiEnvironment.STAGING_GCP_URL` | `https://staging.rhinofcp.com/api/` |
| `ApiEnvironment.DEMO_URL` | `https://demo-prod.rhinohealth.com/api/` |
| `ApiEnvironment.DEMO_DEV_URL` | `https://demo-dev.rhinohealth.com/api/` |
| `ApiEnvironment.LOCALHOST_API_URL` | `http://localhost:8080/api/` |

**CRITICAL:** `rh.login()` defaults to **production**. If your credentials are for dev1, you MUST pass `rhino_api_url=ApiEnvironment.DEV1_AWS_URL` or authentication will fail with HTTP 401.

---

## Endpoint Accessors

| Accessor | Class | Purpose |
|----------|-------|---------|
| `session.project` | `ProjectEndpoints` | Projects, workgroups, cross-site metrics |
| `session.dataset` | `DatasetEndpoints` | Datasets, per-site metrics |
| `session.data_schema` | `DataSchemaEndpoints` | Data schemas |
| `session.code_object` | `CodeObjectEndpoints` | Code objects, runs, harmonization |
| `session.code_run` | `CodeRunEndpoints` | Run status, inference, model params |
| `session.sql_query` | `SQLQueryEndpoints` | On-prem SQL queries |
| `session.semantic_mapping` | `SemanticMappingEndpoints` | Semantic vocabulary mappings |
| `session.syntactic_mapping` | `SyntacticMappingEndpoints` | Syntactic/structural mappings |
| `session.workgroup` | `WorkgroupEndpoints` | Workgroups, storage paths |
| `session.federated_dataset` | `FederatedDatasetEndpoints` | Federated dataset registry |
| `session.user` | `UserEndpoints` | Users |

---

## ProjectEndpoints

**Import:** `from rhino_health.lib.endpoints.endpoint import NameFilterMode, VersionMode`

```python
# Project CRUD
session.project.get_projects(project_uids: List[str] | None = None) → List[Project]
session.project.get_project_by_name(name: str) → Project
session.project.search_for_projects_by_name(name: str, name_filter_mode=NameFilterMode.CONTAINS) → List[Project]
session.project.get_project_stats(project_uid: str) → Dict[str, Any]
session.project.add_project(project: ProjectCreateInput) → Project
session.project.remove_project(project_or_uid: str | Project)

# Workgroup / Collaborators
session.project.get_collaborating_workgroups(project_or_uid: str | Project) → List[Workgroup]
session.project.add_collaborator(project_uid: str, collaborating_workgroup_uid: str)
session.project.remove_collaborator(project_uid: str, collaborating_workgroup_uid: str)
session.project.get_system_resources_for_workgroup(project_uid: str, workgroup_uid: str) → SystemResources

# Dataset methods (also available on project object directly)
session.project.get_datasets(project_uid: str) → List[Dataset]
session.project.get_dataset_by_name(name, version=VersionMode.LATEST, project_uid=None) → Dataset | None
session.project.search_for_datasets_by_name(name, version=VersionMode.LATEST, project_uid=None, name_filter_mode=None, get_all_pages=True) → List[Dataset]

# Data schema methods
session.project.get_data_schemas(project_uid: str) → List[DataSchema]
session.project.get_data_schema_by_name(name, version=VersionMode.LATEST, project_uid=None) → DataSchema | None
session.project.search_for_data_schemas_by_name(name, version=VersionMode.LATEST, project_uid=None, name_filter_mode=None, get_all_pages=True) → List[DataSchema]

# Code object methods
session.project.get_code_objects(project_uid: str) → List[CodeObject]
session.project.get_code_object_by_name(name, version=VersionMode.LATEST, project_uid=None) → CodeObject | None
session.project.search_for_code_objects_by_name(name, version=VersionMode.LATEST, project_uid=None, name_filter_mode=None, get_all_pages=True) → List[CodeObject]

# Semantic/Syntactic mappings
session.project.get_semantic_mappings(project_uid: str) → List[SemanticMapping]
session.project.get_semantic_mapping_by_name(name, version=VersionMode.LATEST, project_uid=None) → SemanticMapping | None
session.project.get_vocabularies(project_uid: str) → List[Vocabulary]
session.project.get_vocabulary_by_name(name, version=VersionMode.LATEST, project_uid=None) → Vocabulary | None
session.project.search_for_vocabularies_by_name(name, version=VersionMode.LATEST, project_uid=None, name_filter_mode=None) → List[Vocabulary]
session.project.get_syntactic_mappings(project_uid: str) → List[SyntacticMapping]
session.project.get_syntactic_mapping_by_name(name, version=VersionMode.LATEST, project_uid=None) → SyntacticMapping | None

# Federated metrics
session.project.aggregate_dataset_metric(
    dataset_uids: List[str],          # NOTE: List[str] of UIDs, NOT List[Dataset]
    metric_configuration: BaseMetric,
    aggregation_method_override: Callable | None = None
) → MetricResponse

session.project.joined_dataset_metric(
    configuration: JoinableMetric,
    query_datasets: List[str],
    filter_datasets: List[str] | None = None
) → MetricResponse
```

**Note:** All `get_*_by_name`, `search_for_*_by_name`, `aggregate_dataset_metric`, and `joined_dataset_metric` are also available directly on a `Project` object (e.g. `project.get_dataset_by_name(...)`).

---

## DatasetEndpoints

**Import:** `from rhino_health.lib.endpoints.dataset.dataset_dataclass import Dataset, DatasetCreateInput`

```python
session.dataset.get_dataset(dataset_uid: str) → Dataset
session.dataset.get_dataset_by_name(name, version=VersionMode.LATEST, project_uid=None) → Dataset | None
session.dataset.search_for_datasets_by_name(
    name: str,
    version=VersionMode.LATEST,
    project_uid=None,
    name_filter_mode=NameFilterMode.CONTAINS,
    get_all_pages=True
) → List[Dataset]

session.dataset.get_dataset_metric(dataset_uid: str, metric_configuration: BaseMetric) → MetricResponse
# Queries on-prem at the site where the dataset lives

session.dataset.add_dataset(
    dataset: DatasetCreateInput,
    return_existing=True,      # return existing if name already exists
    add_version_if_exists=False
) → Dataset

session.dataset.remove_dataset(dataset_or_uid: str | Dataset)
session.dataset.publish(dataset_or_uid, unpublish_other_versions: bool = True)
session.dataset.unpublish(dataset_or_uid)
session.dataset.export_dataset(dataset_uid: str, output_location: str, output_format: str)
```

**Dataset convenience methods:**
```python
dataset.get_metric(metric_configuration: BaseMetric) → MetricResponse
dataset.dataset_info        # property — sanitized metadata about the dataset
dataset.data_schema         # property (cached) — returns DataSchema object
dataset.project             # property (cached) — returns Project object
dataset.workgroup           # property (cached) — returns Workgroup object

# Quick code execution on a dataset (under development):
output_datasets, code_run = dataset.run_code(
    run_code="import pandas as pd\ndf = pd.read_csv('/input_data/dataset.csv')\n...",
    print_progress=True,
    timeout_seconds=600,
)
```

---

## DataSchemaEndpoints

**Import:** `from rhino_health.lib.endpoints.data_schema.data_schema_dataclass import DataSchema, DataSchemaCreateInput, SchemaField`

```python
session.data_schema.get_data_schema_by_name(
    name: str,
    version=VersionMode.LATEST,
    project_uid=None
) → DataSchema | None

session.data_schema.search_for_data_schemas_by_name(
    name: str,
    version=VersionMode.LATEST,
    project_uid=None,
    name_filter_mode=NameFilterMode.CONTAINS,
    get_all_pages=True
) → List[DataSchema]

session.data_schema.create_data_schema(data_schema: DataSchemaCreateInput) → DataSchema
session.data_schema.remove_data_schema(data_schema_or_uid: str | DataSchema)
session.data_schema.publish(data_schema_or_uid, unpublish_other_versions=True)
session.data_schema.unpublish(data_schema_or_uid)
```

---

## CodeObjectEndpoints

**Import:** `from rhino_health.lib.endpoints.code_object.code_object_dataclass import CodeObject, CodeObjectCreateInput, CodeObjectRunInput, CodeTypes, CodeExecutionMode`

```python
session.code_object.get_code_object(code_object_uid: str) → CodeObject
session.code_object.get_code_object_by_name(name, version=VersionMode.LATEST, project_uid=None) → CodeObject | None
session.code_object.search_for_code_objects_by_name(
    name, version=VersionMode.LATEST, project_uid=None,
    name_filter_mode=NameFilterMode.CONTAINS, get_all_pages=True
) → List[CodeObject]
session.code_object.get_build_logs(code_object_uid: str) → str

session.code_object.create_code_object(
    code_object: CodeObjectCreateInput,
    return_existing=True,
    add_version_if_exists=False
) → CodeObject

session.code_object.remove_code_object(code_object_or_uid: str | CodeObject)
session.code_object.rename(code_object_uid: str | CodeObject, new_name: str)
session.code_object.publish(code_object_or_uid, unpublish_other_versions: bool = True)
session.code_object.unpublish(code_object_or_uid)

session.code_object.run_code_object(
    code_object: CodeObjectRunInput
) → CodeObjectRunSyncResponse | CodeObjectRunAsyncResponse

session.code_object.run_data_harmonization(
    code_object_uid: str | CodeObject,
    run_params: DataHarmonizationRunInput
) → CodeObjectRunAsyncResponse

session.code_object.train_model(model: ModelTrainInput) → ModelTrainAsyncResponse  # NVFlare
```

**Response methods:**
```python
code_run = session.code_object.run_code_object(run_params)
result = code_run.wait_for_completion()  # blocks until done
result.status         # CodeRunStatus value
result.output_dataset_uids   # CodeObjectRunSyncResponse only
```

**CodeObject convenience methods:**
```python
code_object.wait_for_build()   # wait for Docker image build
code_object.build_logs         # build log text (property)
```

---

## CodeRunEndpoints

**Import:** `from rhino_health.lib.endpoints.code_run.code_run_dataclass import CodeRun, CodeRunStatus`

```python
session.code_run.get_code_run(code_run_uid: str) → CodeRun
session.code_run.remove_code_run(code_run_or_uid: str | CodeRun)
session.code_run.publish(code_run_or_uid, unpublish_other_versions: bool = True)
session.code_run.unpublish(code_run_or_uid)

session.code_run.run_inference(
    code_run_uid: str,
    validation_dataset_uids: List[str],
    validation_datasets_suffix: str,
    timeout_seconds: int,
    extra_data: Dict | None = None
) → ModelInferenceAsyncResponse

session.code_run.get_model_params(
    code_run_uid: str,
    model_weights_files: List[str] | None = None
) → io.BytesIO
```

**CodeRun methods:**
```python
code_run.wait_for_completion(timeout_seconds=500, poll_frequency=10, print_progress=True) → CodeRun
```

---

## SQLQueryEndpoints

**Import:** `from rhino_health.lib.endpoints.sql_query.sql_query_dataclass import SQLQueryInput, SQLQueryImportInput, ConnectionDetails, SQLServerTypes`

```python
session.sql_query.get_sql_query(sql_query_uid: str) → SQLQuery

session.sql_query.run_sql_query(sql_query_input: SQLQueryInput) → SQLQuery
# Runs metrics on query results; does NOT return raw data

session.sql_query.import_dataset_from_sql_query(
    sql_query_input: SQLQueryImportInput
) → SQLQuery
# Imports SQL query results as a Dataset
```

**SQLQuery methods:**
```python
sql_query.wait_for_completion(timeout_seconds=500, poll_frequency=10, print_progress=True)
```

---

## SemanticMappingEndpoints

**Import:** `from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import SemanticMapping, SemanticMappingCreateInput, VocabularyType, Vocabulary, VocabularyInput, SemanticMappingEntry, IndexingStatusTypes, SemanticMappingProcessingStatus`

```python
# Semantic mapping CRUD
session.semantic_mapping.create_semantic_mapping(
    semantic_mapping_create_input: SemanticMappingCreateInput,
    return_existing=True,
    add_version_if_exists=False
) → SemanticMapping

session.semantic_mapping.get_semantic_mapping(semantic_mapping_or_uid) → SemanticMapping
session.semantic_mapping.get_semantic_mapping_by_name(name, version=VersionMode.LATEST, project_uid=None) → SemanticMapping | None
session.semantic_mapping.search_for_semantic_mappings_by_name(name, ...) → List[SemanticMapping]
session.semantic_mapping.remove_semantic_mapping(semantic_mapping_or_uid)

# Semantic mapping entry data (inspect individual term mappings)
session.semantic_mapping.get_semantic_mapping_data(
    semantic_mapping_or_uid: str | SemanticMapping
) → List[SemanticMappingEntry]
```

**SemanticMapping methods:**
```python
semantic_mapping.wait_for_completion(timeout_seconds=6000, poll_frequency=10, print_progress=True)
```

**Vocabulary access (via project):**
```python
session.project.get_vocabularies(project_uid: str) → List[Vocabulary]
session.project.get_vocabulary_by_name(name, version=VersionMode.LATEST, project_uid=None) → Vocabulary | None
session.project.search_for_vocabularies_by_name(name, ...) → List[Vocabulary]
```

---

## SyntacticMappingEndpoints

**Import:** `from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import SyntacticMapping, SyntacticMappingCreateInput, DataHarmonizationRunInput, SyntacticMappingDataModel, TransformationType`

```python
session.syntactic_mapping.create_syntactic_mapping(
    syntactic_mapping_input: SyntacticMappingCreateInput,
    return_existing=True,
    add_version_if_exists=False
) → SyntacticMapping

session.syntactic_mapping.get_syntactic_mapping(syntactic_mapping_or_uid) → SyntacticMapping
session.syntactic_mapping.get_syntactic_mapping_by_name(name, version=VersionMode.LATEST, project_uid=None) → SyntacticMapping | None
session.syntactic_mapping.search_for_syntactic_mappings_by_name(name, ...) → List[SyntacticMapping]
session.syntactic_mapping.remove_syntactic_mapping(syntactic_mapping_or_uid)

session.syntactic_mapping.run_data_harmonization(
    syntactic_mapping_or_uid: str | SyntacticMapping,
    run_params: DataHarmonizationRunInput
) → CodeObjectRunAsyncResponse

session.syntactic_mapping.generate_config(syntactic_mapping_or_uid) → APIResponse
# LLM-based config auto-generation (async)
```

---

## WorkgroupEndpoints

**Import:** `from rhino_health.lib.endpoints.workgroup.workgroup_dataclass import Workgroup`

```python
session.workgroup.get_workgroups(workgroup_uids: List[str] = None) → List[Workgroup]
session.workgroup.list_external_storage_file_paths(workgroup_uid: str) → List[str]
```

---

## FederatedDatasetEndpoints

**Note:** All methods are under active development. Use with caution.

**Import:** `from rhino_health.lib.endpoints.federated_dataset.federated_dataset_dataclass import FederatedDataset, FederatedDatasetCreateInput`

```python
session.federated_dataset.get_federated_datasets(uids: List[str] | None = None) → List[FederatedDataset]
session.federated_dataset.get_federated_dataset_by_name(name, version=VersionMode.LATEST) → FederatedDataset | None
session.federated_dataset.search_for_federated_datasets_by_name(name, ...) → List[FederatedDataset]
session.federated_dataset.remove_federated_dataset(federated_dataset_or_uid)
```

---

## Key Enums

### NameFilterMode
```python
from rhino_health.lib.endpoints.endpoint import NameFilterMode
NameFilterMode.CONTAINS   # partial match (default)
```

### VersionMode
```python
from rhino_health.lib.endpoints.endpoint import VersionMode
VersionMode.LATEST   # most recent (default)
VersionMode.ALL      # all versions
```

### FilterType
```python
from rhino_health.lib.metrics import FilterType
FilterType.EQUAL              # =
FilterType.IN                 # value in list
FilterType.NOT_IN
FilterType.GREATER_THAN       # >
FilterType.LESS_THAN          # <
FilterType.GREATER_THAN_EQUAL # >=
FilterType.LESS_THAN_EQUAL    # <=
FilterType.BETWEEN            # inclusive range (requires FilterBetweenRange)
```

### CodeTypes
```python
from rhino_health.lib.endpoints.code_object.code_object_dataclass import CodeTypes
CodeTypes.GENERALIZED_COMPUTE   # = 'Generalized Compute'
CodeTypes.PYTHON_CODE           # = 'Python Code'
CodeTypes.DATA_HARMONIZATION    # = 'Data Harmonization'
CodeTypes.INTERACTIVE_CONTAINER
CodeTypes.NVIDIA_FLARE_V2_0     # through V2_6
```

### CodeRunStatus
```python
from rhino_health.lib.endpoints.code_run.code_run_dataclass import CodeRunStatus
CodeRunStatus.INITIALIZING
CodeRunStatus.STARTED
CodeRunStatus.COMPLETED
CodeRunStatus.FAILED
CodeRunStatus.HALTING
CodeRunStatus.HALTED_SUCCESS
CodeRunStatus.HALTED_FAILURE
```

### SyntacticMappingDataModel
```python
from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import SyntacticMappingDataModel
SyntacticMappingDataModel.OMOP
SyntacticMappingDataModel.FHIR
SyntacticMappingDataModel.CUSTOM
```

### JoinMode
```python
from rhino_health.lib.metrics.base_metric import JoinMode
JoinMode.INTERSECTION   # inner join — only shared identifiers
JoinMode.UNION          # outer join — all rows, deduplicated
```

### UserWorkgroupRole
```python
from rhino_health.lib.endpoints.user.user_dataclass import UserWorkgroupRole
UserWorkgroupRole.MEMBER
UserWorkgroupRole.WORKGROUP_ADMIN
UserWorkgroupRole.ORG_ADMIN
UserWorkgroupRole.RHINO_ADMIN
```

### VocabularyType
```python
from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import VocabularyType
VocabularyType.STANDARD   # = 'standard'
VocabularyType.CUSTOM     # = 'custom'
```

### IndexingStatusTypes
```python
from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import IndexingStatusTypes
IndexingStatusTypes.NOT_NEEDED    # = 'Not Needed'
IndexingStatusTypes.NOT_STARTED   # = 'Not Started'
IndexingStatusTypes.IN_PROGRESS   # = 'In Progress'
IndexingStatusTypes.COMPLETED     # = 'Completed'
IndexingStatusTypes.ERROR         # = 'Error'
```

### SemanticMappingProcessingStatus
```python
from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import SemanticMappingProcessingStatus
SemanticMappingProcessingStatus.NOT_STARTED   # = 'Not Started'
SemanticMappingProcessingStatus.IN_PROGRESS   # = 'In Progress'
SemanticMappingProcessingStatus.NEEDS_REVIEW  # = 'Needs Review'
SemanticMappingProcessingStatus.APPROVED      # = 'Approved'
SemanticMappingProcessingStatus.ERROR         # = 'Error'
```

### ApiEnvironment
```python
from rhino_health.lib.constants import ApiEnvironment
ApiEnvironment.PROD_API_URL      # = 'https://prod.rhinohealth.com/api/' (default)
ApiEnvironment.DEV1_AWS_URL      # = 'https://dev1.rhinohealth.com/api/'
ApiEnvironment.QA_AWS_URL        # = 'https://qa-cloud.rhinohealth.com/api/'
ApiEnvironment.STAGING_AWS_URL   # = 'https://staging.rhinohealth.com/api/'
# See ApiEnvironment section above for full list
```

---

## CreateInput Summaries

### ProjectCreateInput
```python
from rhino_health.lib.endpoints.project.project_dataclass import ProjectCreateInput

ProjectCreateInput(
    name="My Project",
    description="Description",
    type="Validation",                     # or "Refinement"
    primary_workgroup_uid=WORKGROUP_UID,   # alias: 'primary_workgroup'
    permissions=None,                      # JSON-encoded permissions dict
)
```

### DatasetCreateInput
```python
from rhino_health.lib.endpoints.dataset.dataset_dataclass import DatasetCreateInput

DatasetCreateInput(
    name="My Dataset",
    description="Description",
    project_uid=project.uid,               # alias: 'project'
    workgroup_uid=workgroup.uid,           # alias: 'workgroup'
    data_schema_uid=schema.uid,            # alias: 'data_schema'
    csv_filesystem_location="/rhino_data/data.csv",
    method="filesystem",                   # or "DICOM"
    is_data_deidentified=True,
    sync=True,                             # synchronous import
)
```

### DataSchemaCreateInput
```python
from rhino_health.lib.endpoints.data_schema.data_schema_dataclass import DataSchemaCreateInput

DataSchemaCreateInput(
    name="My Schema",
    description="Description",
    primary_workgroup_uid=WORKGROUP_UID,
    project_uid=project.uid,               # or projects=[project.uid]
    file_path="./schema.csv",              # recommended over schema_fields
)
```

### CodeObjectCreateInput
```python
from rhino_health.lib.endpoints.code_object.code_object_dataclass import CodeObjectCreateInput, CodeTypes

CodeObjectCreateInput(
    name="My Code Object",
    description="Description",
    project_uid=project.uid,               # alias: 'project'
    code_type=CodeTypes.GENERALIZED_COMPUTE,  # alias: 'type'
    config={"container_image_uri": f"{ecr_base_uri}/{repo}:{tag}"},
    input_data_schema_uids=[schema.uid],
    output_data_schema_uids=[schema.uid],
)

# For PYTHON_CODE type:
CodeObjectCreateInput(
    ...
    code_type=CodeTypes.PYTHON_CODE,
    config={
        "python_version": "3.9",
        "requirements": ["numpy == 1.22.*"],
        "python_code": "...",
        "code_execution_mode": "snippet",  # or "file"
    },
)
```

### CodeObjectRunInput
```python
from rhino_health.lib.endpoints.code_object.code_object_dataclass import CodeObjectRunInput

CodeObjectRunInput(
    code_object_uid=code_object.uid,
    input_dataset_uids=[[dataset.uid]],    # List[List[str]] — double-nested
    output_dataset_naming_templates=[
        '{{ input_dataset_names.0 }} - Train',
        '{{ input_dataset_names.0 }} - Test',
    ],
    timeout_seconds=600,
    sync=False,                            # async by default
    external_storage_file_paths=["path/in/bucket/file.txt"],
)
```

### SQLQueryInput / SQLQueryImportInput
```python
from rhino_health.lib.endpoints.sql_query.sql_query_dataclass import (
    SQLQueryInput, SQLQueryImportInput, ConnectionDetails, SQLServerTypes
)

conn = ConnectionDetails(
    server_user="db_user", password="db_password",
    server_type=SQLServerTypes.POSTGRESQL,
    server_url="myserver:5432", db_name="mydb"
)

SQLQueryInput(
    session=session, project=project_uid, workgroup=workgroup_uid,
    connection_details=conn,
    sql_query="SELECT * FROM patients",
    metric_definitions=[Mean(variable="age"), Count(variable="id")],
    timeout_seconds=600,
)

SQLQueryImportInput(
    session=session, project=project_uid, workgroup=workgroup_uid,
    connection_details=conn,
    sql_query="SELECT * FROM patients",
    dataset_name="Imported Dataset",
    data_schema_uid=schema.uid,
    is_data_deidentified=False,
    timeout_seconds=600,
)
```

### DataHarmonizationRunInput
```python
from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import DataHarmonizationRunInput

DataHarmonizationRunInput(
    input_dataset_uids=[dataset.uid],                     # List[str]
    semantic_mapping_uids_by_vocabularies={},             # dict vocab_uid → semantic_mapping_uid
    timeout_seconds=600.0,
)
```

---

## Key Dataclass Fields

### Project
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str | Unique ID |
| `name` | str | Project name |
| `type` | Literal["Validation", "Refinement"] | Project type |
| `primary_workgroup_uid` | str | Primary workgroup |
| `creator_uid` | str | Creator UID |

### Dataset
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str | Unique ID |
| `name` | str | Dataset name |
| `num_cases` | int | Row count |
| `data_schema_uid` | str | Schema UID |
| `version` | int \| None | Revision (0-indexed) |
| `import_status` | str | Import status |

### CodeObject
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str | Unique ID |
| `name` | str | Code object name |
| `code_type` | str | CodeTypes value |
| `build_status` | CodeObjectBuildStatus | NOT_STARTED, IN_PROGRESS, COMPLETE, ERROR |
| `version` | int \| None | Revision |
| `published` | bool | Published status |

### CodeRun
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str | Run UID |
| `status` | CodeRunStatus | Current status |
| `code_object_uid` | str | Parent code object |
| `input_dataset_uids` | CodeRunInputDatasets | Triple-nested: List[List[List[str]]] |
| `output_dataset_uids` | CodeRunOutputDatasets | Triple-nested — access via `.root[i].root[j].root[k]` |
| `results_report` | str \| dict \| None | Run report |

### Workgroup
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str | Unique ID |
| `name` | str | Workgroup name |
| `org_name` | str | Organization name |
| `image_repo_name` | str \| None | ECR image repo suffix |
| `storage_bucket_name_part` | str \| None | S3 bucket name part |

### DataSchema
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str \| None | Unique ID |
| `name` | str | Schema name |
| `description` | str | Description |
| `schema_fields` | SchemaFields | **RootModel** — access items via `.root` (see below) |
| `published` | bool | Published status (default False) |
| `version` | int \| None | Revision (default 0) |
| `extra_data` | Dict[str, Any] \| None | Extra JSON metadata |
| `base_version_uid` | str \| None | If versioned, UID of base schema |
| `creator_uid` | str | Creator UID |
| `created_at` | str | Creation timestamp |
| `project_name` | str | Project name |
| `primary_workgroup_name` | str | Workgroup name |

**Properties:** `project`, `primary_workgroup`, `creator` (all cached).
**Methods:** `delete()`, `publish()`, `unpublish()`.

### SchemaFields (Pydantic RootModel)

`SchemaFields` wraps a list of `SchemaField` objects. It inherits from `pydantic.RootModel` — access the list via `.root`.

```python
schema = project.get_data_schema_by_name("My Schema")
fields = schema.schema_fields        # SchemaFields object (NOT a plain list)
field_list = schema.schema_fields.root   # List[SchemaField] — the actual list
field_names = schema.schema_fields.field_names  # property — collection of field names
num_fields = len(schema.schema_fields.root)     # count of fields
```

### SchemaField
| Field | Type | Notes |
|-------|------|-------|
| `name` | str | Field/column name |
| `identifier` | str \| None | Optional identifier |
| `description` | str \| None | Description |
| `role` | str \| None | Role |
| `type` | str \| None | Data type |
| `type_params` | Any | Type parameters |
| `units` | str \| None | Units |
| `may_contain_phi` | bool \| None | PHI flag |
| `permissions` | str \| None | Permissions |

### Vocabulary
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str | Unique ID |
| `name` | str | Vocabulary name |
| `type` | VocabularyType | `STANDARD` or `CUSTOM` |
| `version` | int \| None | Revision (default 0) |
| `indexing_status` | IndexingStatusTypes | `NOT_NEEDED`, `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `ERROR` |
| `indexing_error_message` | List[str] \| None | Error details if indexing failed |
| `possible_domain_names` | List[str] \| None | Domain names |
| `prefiltering_service_table` | str \| None | Prefiltering table |
| `creator_uid` | str | Creator UID |
| `created_at` | str | Creation timestamp |
| `primary_workgroup_name` | str | Workgroup name |
| `project_name` | str | Project name |

**Properties:** `primary_workgroup`, `project`, `creator` (all cached).

### SemanticMapping
| Field | Type | Notes |
|-------|------|-------|
| `uid` | str | Unique ID |
| `processing_status` | SemanticMappingProcessingStatus | `NOT_STARTED`, `IN_PROGRESS`, `NEEDS_REVIEW`, `APPROVED`, `ERROR` |
| `processing_error_message` | List[str] \| None | Error details |
| `input_vocabulary_uid` | Any | Input vocabulary (alias: `input_vocabulary`) |
| `output_vocabulary_uid` | Any | Output vocabulary (alias: `output_vocabulary`) |
| `semantic_mapping_info` | Dict[str, Any] \| None | Mapping metadata |
| `creator_uid` | str | Creator UID |
| `created_at` | str | Creation timestamp |
| `primary_workgroup_name` | str | Workgroup name |
| `project_name` | str | Project name |

**Properties:** `primary_workgroup`, `project`, `creator` (all cached).
**Method:** `wait_for_completion(timeout_seconds=6000, poll_frequency=10, print_progress=True)`.

### SemanticMappingEntry
| Field | Type | Notes |
|-------|------|-------|
| `entry_uid` | str | Entry unique ID |
| `source_term_name` | str | Source term (from input vocabulary) |
| `target_term_name` | str | Mapped target term (from output vocabulary) |
| `recommendation_data` | List[Dict[str, Any]] | AI recommendations with scores |
| `num_appearances` | int | Times the source term appeared in the dataset |
| `status` | Literal['calculating', 'failed', 'needs_review', 'approved'] | Review status |
| `is_approved` | bool | Whether the entry is approved |
| `approved_at` | str | Approval timestamp |
| `approved_by` | Dict[str, str] | Approver info |
| `index` | int | Entry index |
| `created_at` | str | Creation timestamp |

### SemanticMappingCreateInput
| Field | Type | Notes |
|-------|------|-------|
| `name` | str | Mapping name |
| `description` | str \| None | Description |
| `primary_workgroup_uid` | str | Workgroup (alias: `primary_workgroup`) |
| `project_uid` | str | Project (alias: `project`) |
| `input_vocabulary_uid` | str | Input vocabulary (alias: `input_vocabulary`) |
| `output_vocabulary_uid` | str | Output vocabulary (alias: `output_vocabulary`) |
| `output_vocabulary_categories` | List[str] \| None | Restrict to categories |
| `source_dataset_columns` | List[DatasetColumn] | `[{"dataset_uid": uid, "field_name": col}]` |
| `base_version_uid` | str \| None | Base version for updates |
| `version` | int \| None | Revision (default 0) |

---

## Import Path Reference

| Class | Import |
|-------|--------|
| `NameFilterMode`, `VersionMode` | `from rhino_health.lib.endpoints.endpoint import NameFilterMode, VersionMode` |
| `Project`, `ProjectCreateInput` | `from rhino_health.lib.endpoints.project.project_dataclass import Project, ProjectCreateInput` |
| `Dataset`, `DatasetCreateInput` | `from rhino_health.lib.endpoints.dataset.dataset_dataclass import Dataset, DatasetCreateInput` |
| `DataSchema`, `DataSchemaCreateInput` | `from rhino_health.lib.endpoints.data_schema.data_schema_dataclass import DataSchema, DataSchemaCreateInput` |
| `CodeObject`, `CodeObjectCreateInput` | `from rhino_health.lib.endpoints.code_object.code_object_dataclass import CodeObject, CodeObjectCreateInput` |
| `CodeObjectRunInput`, `CodeTypes` | `from rhino_health.lib.endpoints.code_object.code_object_dataclass import CodeObjectRunInput, CodeTypes` |
| `CodeRun`, `CodeRunStatus` | `from rhino_health.lib.endpoints.code_run.code_run_dataclass import CodeRun, CodeRunStatus` |
| `SQLQueryInput`, `ConnectionDetails` | `from rhino_health.lib.endpoints.sql_query.sql_query_dataclass import SQLQueryInput, SQLQueryImportInput, ConnectionDetails, SQLServerTypes` |
| `SemanticMapping`, `SemanticMappingCreateInput` | `from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import SemanticMapping, SemanticMappingCreateInput` |
| `SemanticMappingEntry` | `from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import SemanticMappingEntry` |
| `Vocabulary`, `VocabularyInput` | `from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import Vocabulary, VocabularyInput` |
| `VocabularyType`, `IndexingStatusTypes` | `from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import VocabularyType, IndexingStatusTypes` |
| `SemanticMappingProcessingStatus` | `from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import SemanticMappingProcessingStatus` |
| `DatasetColumn` | `from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import DatasetColumn` |
| `SchemaField`, `SchemaFields` | `from rhino_health.lib.endpoints.data_schema.data_schema_dataclass import SchemaField, SchemaFields` |
| `ApiEnvironment` | `from rhino_health.lib.constants import ApiEnvironment` |
| `SyntacticMapping`, `SyntacticMappingCreateInput` | `from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import SyntacticMapping, SyntacticMappingCreateInput` |
| `DataHarmonizationRunInput` | `from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import DataHarmonizationRunInput` |
| `SyntacticMappingDataModel`, `TransformationType` | `from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import SyntacticMappingDataModel, TransformationType` |
| `Workgroup` | `from rhino_health.lib.endpoints.workgroup.workgroup_dataclass import Workgroup` |
| `User`, `UserWorkgroupRole` | `from rhino_health.lib.endpoints.user.user_dataclass import User, UserWorkgroupRole` |
| `FederatedDataset`, `FederatedDatasetCreateInput` | `from rhino_health.lib.endpoints.federated_dataset.federated_dataset_dataclass import FederatedDataset, FederatedDatasetCreateInput` |
| `Count`, `Mean`, `StandardDeviation`, `Sum` | `from rhino_health.lib.metrics import Count, Mean, StandardDeviation, Sum` |
| `Percentile`, `Median`, `Min`, `Max` | `from rhino_health.lib.metrics import Percentile, Median, Min, Max` |
| `KaplanMeier`, `Cox` | `from rhino_health.lib.metrics import KaplanMeier, Cox` |
| `RocAuc`, `RocAucWithCI` | `from rhino_health.lib.metrics import RocAuc, RocAucWithCI` |
| `FilterType`, `FilterBetweenRange` | `from rhino_health.lib.metrics import FilterType` |
| `JoinMode` | `from rhino_health.lib.metrics.base_metric import JoinMode` |
| `ChiSquare`, `TTest`, `OneWayANOVA`, `Pearson`, `Spearman`, `ICC`, `Wilcoxon` | `from rhino_health.lib.metrics.statistics_tests import ChiSquare, TTest, OneWayANOVA, Pearson, Spearman, ICC, Wilcoxon` |
| `TwoByTwoTable`, `OddsRatio`, `Risk`, `RiskRatio`, `Odds` | `from rhino_health.lib.metrics.epidemiology.two_by_two_table_based_metrics import TwoByTwoTable, OddsRatio, Risk, RiskRatio, Odds` |
| `Prevalence`, `Incidence` | `from rhino_health.lib.metrics.epidemiology.time_range_based_metrics import Prevalence, Incidence` |
| `RuntimeFile` | `from rhino_health.lib.endpoints.runtime_file.runtime_file_dataclass import RuntimeFile` |
