# Rhino Health SDK — Patterns & Gotchas

Practical patterns extracted from working examples + known pitfalls.

---

## 1. Authentication

Always use `getpass()` — never hardcode passwords.

```python
import rhino_health as rh
from getpass import getpass

my_username = "my_email@example.com"
session = rh.login(username=my_username, password=getpass())

# With MFA/OTP:
session = rh.login(username=my_username, password=getpass(), otp_code="123456")
```

**Typical session setup block:**
```python
import rhino_health as rh
from getpass import getpass

session = rh.login(username="my_email@example.com", password=getpass())

PROJECT_NAME = "My Project"
WORKGROUP_UID = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

project = session.project.get_project_by_name(PROJECT_NAME)
workgroup = session.project.get_collaborating_workgroups(project.uid)[0]
```

---

## 2. Getting Resources by Name vs UID

**By UID** — direct and unambiguous (preferred when you have the UID):
```python
dataset = session.dataset.get_dataset(dataset_uid)
code_run = session.code_run.get_code_run(code_run_uid)
```

**By name via project** — most common discovery pattern:
```python
project = session.project.get_project_by_name("My Project")
dataset = project.get_dataset_by_name("My Dataset")         # → Dataset | None
schema  = project.get_data_schema_by_name("My Schema")      # → DataSchema | None
code_obj = project.get_code_object_by_name("My Code")       # → CodeObject | None
```

**GOTCHA:** `get_*_by_name` returns `None` if not found — it does NOT raise an exception.

```python
dataset = project.get_dataset_by_name("Nonexistent Dataset")
# dataset is None — not an exception!

# Always check:
if dataset is None:
    raise ValueError(f"Dataset not found")
```

**Search (partial name, returns list):**
```python
from rhino_health.lib.endpoints.endpoint import NameFilterMode, VersionMode

datasets = project.search_for_datasets_by_name(
    "test",
    name_filter_mode=NameFilterMode.CONTAINS  # default
)
# Returns [] if none match — never raises
```

**All versions of a dataset:**
```python
all_versions = project.search_for_datasets_by_name(
    "My Dataset", version=VersionMode.ALL, name_filter_mode=NameFilterMode.CONTAINS
)
# Sorted newest first
older = project.get_dataset_by_name("My Dataset", version=1)
```

---

## 3. Upsert Pattern

The SDK uses idempotent creation with `return_existing` and `add_version_if_exists`:

```python
from rhino_health.lib.endpoints.dataset.dataset_dataclass import DatasetCreateInput

dataset_input = DatasetCreateInput(
    name="My Dataset",
    project_uid=project.uid,
    workgroup_uid=workgroup.uid,
    data_schema_uid=schema.uid,
    csv_filesystem_location="/rhino_data/data.csv",
    method="filesystem",
    is_data_deidentified=True,
)

# Default: return existing if name matches (idempotent)
dataset = session.dataset.add_dataset(dataset_input)
dataset = session.dataset.add_dataset(dataset_input)  # returns same dataset

# Create new version instead:
new_v = session.dataset.add_dataset(dataset_input, return_existing=False, add_version_if_exists=True)

# Same pattern for code objects:
code_obj = session.code_object.create_code_object(input)
new_v_co = session.code_object.create_code_object(input, return_existing=False, add_version_if_exists=True)
```

---

## 4. Per-Site vs Aggregated vs Joined Metrics

Three patterns for running metrics:

```python
from rhino_health.lib.metrics import Mean

config = Mean(variable="Height")

# Pattern 1: Per-site (queries one dataset at one site)
result = session.dataset.get_dataset_metric(dataset.uid, config)
# — or — shorthand on dataset object:
result = dataset.get_metric(config)
print(result.output)

# Pattern 2: Aggregated across sites (federated)
# NOTE: dataset_uids must be List[str] of UIDs, NOT List[Dataset]
result = session.project.aggregate_dataset_metric(
    dataset_uids=[str(d.uid) for d in my_datasets],
    metric_configuration=config
)
print(result.output)

# Pattern 3: Federated join (correlate across datasets with shared identifiers)
result = session.project.joined_dataset_metric(
    configuration=config,
    query_datasets=[query_dataset.uid],
    filter_datasets=[filter_dataset.uid],   # optional
)
print(result.output)
```

**GOTCHA:** `aggregate_dataset_metric` takes `List[str]` of UIDs — passing `List[Dataset]` silently fails.

```python
# WRONG — passes Dataset objects:
result = project.aggregate_dataset_metric(datasets, config)

# CORRECT — extract UIDs:
result = project.aggregate_dataset_metric([str(d.uid) for d in datasets], config)
```

---

## 5. Filtering

Three approaches to filter metric data:

### 5a. Inline FilterVariable dict (inline filter on the variable)

Pass a dict instead of a column name string:
```python
from rhino_health.lib.metrics import Mean, FilterType

# Filter to only Males before computing mean
mean = Mean(
    variable={
        "data_column": "Height",
        "filter_column": "Gender",
        "filter_value": "M",
        # filter_type omitted → defaults to EQUAL
    }
)

# With explicit filter type:
mean = Mean(
    variable={
        "data_column": "Height",
        "filter_column": "Weight",
        "filter_value": 70,
        "filter_type": FilterType.GREATER_THAN_EQUAL,
    }
)
```

### 5b. data_filters list (multiple filters, federated join support)

```python
from rhino_health.lib.metrics import Mean

config = Mean(
    variable="SpO2",
    join_field="UID",
    data_filters=[
        {"filter_column": "Age", "filter_value": 35, "filter_type": ">"},
        # filter_dataset scopes this filter to a specific dataset (for joins):
        {"filter_column": "BloodType", "filter_value": "a", "filter_type": "=",
         "filter_dataset": filter_dataset.uid},
        {"filter_column": "Gender", "filter_value": "m", "filter_type": "=",
         "filter_dataset": query_dataset.uid},
    ],
)
```

### 5c. Range filter (BETWEEN)

```python
from rhino_health.lib.metrics import Mean, FilterType

# 70 <= Weight <= 100
mean = Mean(
    variable={
        "data_column": "Height",
        "filter_column": "Weight",
        "filter_value": {
            "lower": {"filter_value": 70, "filter_type": FilterType.GREATER_THAN_EQUAL},
            "upper": {"filter_value": 100, "filter_type": FilterType.LESS_THAN_EQUAL},
        },
        "filter_type": FilterType.BETWEEN,
    }
)
```

---

## 6. Group By

Add `group_by` to any metric to split results by a column:

```python
from rhino_health.lib.metrics import Mean

# Group by single column
mean = Mean(
    variable="Height",
    group_by={"groupings": ["Gender"]}
)

# Group by multiple columns
mean = Mean(
    variable="Height",
    group_by={"groupings": ["Gender", "AgeGroup"]}
)

# Combined with filtering:
mean = Mean(
    variable={
        "data_column": "Height",
        "filter_column": "Weight",
        "filter_value": 70,
        "filter_type": FilterType.GREATER_THAN_EQUAL,
    },
    group_by={"groupings": ["Gender"]}
)

# Results are keyed by group value:
result = session.dataset.get_dataset_metric(dataset.uid, mean)
for group, data in result.output.items():
    print(f"{group}: {data}")
```

---

## 7. Federated Joins

Use `joined_dataset_metric` to correlate across multiple datasets using a shared identifier column.

```python
from rhino_health.lib.metrics import Mean
from rhino_health.lib.metrics.base_metric import JoinMode

# INTERSECTION (inner join — only rows with matching identifiers)
config = Mean(
    variable="SpO2",
    join_field={"data_column": "UID", "filter_column": "Age", "filter_value": 35, "filter_type": ">"},
)
result = session.project.joined_dataset_metric(
    filter_datasets=[filter_dataset.uid],   # dataset with filter criteria
    query_datasets=[query_dataset.uid],     # dataset with measurement data
    configuration=config
)

# UNION (outer join — all rows from all query datasets, deduplicated)
config = Mean(
    variable="SpO2",
    join_field="UID",
    join_mode=JoinMode.UNION,   # or join_mode="union"
    data_filters=[
        {"filter_column": "Gender", "filter_value": "m", "filter_type": "=",
         "filter_dataset": dataset2.uid},
    ],
)
result = session.project.joined_dataset_metric(
    query_datasets=[query_dataset.uid, dataset2.uid, dataset3.uid],
    configuration=config        # no filter_datasets for UNION
)
```

**Key rules:**
- `join_field` specifies the shared identifier column
- `filter_datasets` filter *which rows* from `query_datasets` are included (INTERSECTION only)
- `join_mode="union"` aggregates across all `query_datasets` without intersection
- Only `JoinableMetric` subclasses work: `Count`, `Mean`, `StandardDeviation`, `Sum`

---

## 8. Code Object Lifecycle

Full lifecycle: create → (optional) wait for build → run → wait for completion.

```python
from rhino_health.lib.endpoints.code_object.code_object_dataclass import (
    CodeObjectCreateInput, CodeObjectRunInput, CodeTypes
)
import rhino_health as rh

# Step 1: Create (builds Docker image for Generalized Compute)
creation_params = CodeObjectCreateInput(
    name="My Analysis",
    description="...",
    code_type=CodeTypes.GENERALIZED_COMPUTE,
    project_uid=project.uid,
    config={"container_image_uri": f"{ecr_base_uri}/{repo}:{tag}"},
    input_data_schema_uids=[schema.uid],
    output_data_schema_uids=[schema.uid],
)
code_object = session.code_object.create_code_object(creation_params)
# For Generalized Compute, wait for the Docker build:
code_object.wait_for_build()

# Step 2: Run
run_params = CodeObjectRunInput(
    code_object_uid=code_object.uid,
    input_dataset_uids=[[input_dataset.uid]],   # double-nested List[List[str]]
    output_dataset_naming_templates=["{{ input_dataset_names.0 }} - Output"],
    timeout_seconds=600,
)
code_run = session.code_object.run_code_object(run_params)

# Step 3: Wait for completion
result = code_run.wait_for_completion()
print(f"Status: {result.status.value}")

# Multiple outputs (e.g. train/test split):
run_params = CodeObjectRunInput(
    code_object_uid=code_object.uid,
    input_dataset_uids=[[input_dataset.uid]],
    output_dataset_naming_templates=[
        '{{ input_dataset_names.0 }} - Train',
        '{{ input_dataset_names.0 }} - Test',
    ],
    timeout_seconds=300,
)
```

**Python code object (no Docker build required):**
```python
from textwrap import dedent

creation_params = CodeObjectCreateInput(
    name="Python Snippet",
    code_type=CodeTypes.PYTHON_CODE,
    project_uid=project.uid,
    config={
        "python_version": "3.9",
        "requirements": ["numpy == 1.22.*", "pandas ~= 1.4.2"],
        "python_code": dedent("""
            # your Python code here
            # input data at: /input_data/
            # output data to: /output_data/
        """),
        "code_execution_mode": "snippet",
    },
    input_data_schema_uids=[None],
    output_data_schema_uids=[None],
)
code_object = session.code_object.create_code_object(creation_params)
# No wait_for_build needed for PYTHON_CODE
```

---

## 9. Async / Wait for Completion

Several SDK operations are async and return response objects with `wait_for_completion()`.

```python
# Code run (most common)
code_run = session.code_object.run_code_object(run_params)
result = code_run.wait_for_completion(
    timeout_seconds=500,
    poll_frequency=10,
    print_progress=True
)

# Data harmonization
code_run = session.code_object.run_data_harmonization(
    code_object_uid=harmonization_co_uid,
    run_params=data_harmonization_params
)
result = code_run.wait_for_completion()

# SQL query
response = session.sql_query.run_sql_query(query_run_params)
result = response.wait_for_completion()

# Semantic mapping indexing
semantic_mapping.wait_for_completion(timeout_seconds=6000)

# Code object build
code_object.wait_for_build()
```

**Accessing output datasets after harmonization:**
```python
result = code_run.wait_for_completion()
# output_dataset_uids is triply-nested: List[workgroups][slots][dataset_uids]
output_uid = result.output_dataset_uids.root[0].root[0].root[0]
# or for a specific workgroup/slot:
output_uid = code_run.code_run.output_dataset_uids.root[0].root[2].root[0]
```

---

## 10. External Storage Files (S3)

Pass files from a workgroup's S3 bucket into a code run:

```python
# List available files
files = session.workgroup.list_external_storage_file_paths(workgroup.uid)

# Reference in run — files are extracted to /external_data/ at runtime
run_params = CodeObjectRunInput(
    code_object_uid=code_object.uid,
    input_dataset_uids=[[dataset.uid]],
    external_storage_file_paths=[
        "data_files/model_weights.bin",
        "config/params.json",
    ],
    timeout_seconds=600,
    sync=True,
)
# Inside the code object, access as: /external_data/data_files/model_weights.bin
```

---

## 11. Common Import Paths Cheatsheet

```python
# Session and core
import rhino_health as rh
from rhino_health.lib.endpoints.endpoint import NameFilterMode, VersionMode
from rhino_health.lib.constants import ApiEnvironment

# Dataclasses
from rhino_health.lib.endpoints.project.project_dataclass import ProjectCreateInput
from rhino_health.lib.endpoints.dataset.dataset_dataclass import DatasetCreateInput
from rhino_health.lib.endpoints.data_schema.data_schema_dataclass import (
    DataSchemaCreateInput, DataSchema, SchemaField, SchemaFields
)
from rhino_health.lib.endpoints.code_object.code_object_dataclass import (
    CodeObjectCreateInput, CodeObjectRunInput, CodeTypes
)
from rhino_health.lib.endpoints.syntactic_mapping.syntactic_mapping_dataclass import (
    DataHarmonizationRunInput, SyntacticMappingDataModel
)
from rhino_health.lib.endpoints.sql_query.sql_query_dataclass import (
    SQLQueryInput, SQLQueryImportInput, ConnectionDetails, SQLServerTypes
)

# Semantic mappings & vocabularies
from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import (
    SemanticMapping, SemanticMappingCreateInput, SemanticMappingEntry,
    Vocabulary, VocabularyInput, VocabularyType,
    IndexingStatusTypes, SemanticMappingProcessingStatus, DatasetColumn
)

# Metrics (CORRECT paths)
from rhino_health.lib.metrics import (
    Count, Mean, StandardDeviation, Sum,
    Percentile, Median, Min, Max,
    KaplanMeier, Cox,
    RocAuc, RocAucWithCI,
    FilterType
)
from rhino_health.lib.metrics.base_metric import JoinMode
from rhino_health.lib.metrics.statistics_tests import ChiSquare, TTest, OneWayANOVA, Pearson, Spearman
from rhino_health.lib.metrics.epidemiology.two_by_two_table_based_metrics import TwoByTwoTable, OddsRatio
from rhino_health.lib.metrics.epidemiology.time_range_based_metrics import Prevalence, Incidence
```

---

## 12. Gotchas & Pitfalls

### WRONG import paths — the most common LLM mistake

```python
# WRONG — these paths do NOT exist:
from rhino_health.metrics import Mean                     # ❌
from rhino_health.endpoints.dataset import DatasetCreateInput  # ❌

# CORRECT:
from rhino_health.lib.metrics import Mean                 # ✓
from rhino_health.lib.endpoints.dataset.dataset_dataclass import DatasetCreateInput  # ✓
```

### aggregate_dataset_metric expects List[str] of UIDs

```python
datasets = [dataset1, dataset2]

# WRONG — passes Dataset objects:
result = project.aggregate_dataset_metric(datasets, config)  # ❌

# CORRECT — extract UIDs first:
result = project.aggregate_dataset_metric(
    [str(d.uid) for d in datasets], config  # ✓
)
```

### Alias fields in CreateInput classes

Pydantic aliases: when constructing, use the Python attribute name; they serialize to a different name for the API.

```python
# These use Python kwarg names (NOT the alias):
DatasetCreateInput(
    project_uid=project.uid,    # serializes as 'project'
    workgroup_uid=workgroup.uid, # serializes as 'workgroup'
    data_schema_uid=schema.uid, # serializes as 'data_schema'
)

CodeObjectCreateInput(
    project_uid=project.uid,    # serializes as 'project'
    code_type=CodeTypes.GC,     # serializes as 'type'
)

ProjectCreateInput(
    primary_workgroup_uid=wg.uid,  # serializes as 'primary_workgroup'
)
```

### CodeObjectRunInput.input_dataset_uids is double-nested

```python
# WRONG — flat list:
run_params = CodeObjectRunInput(
    input_dataset_uids=[dataset.uid],   # ❌ — must be List[List[str]]
)

# CORRECT — wrapped in inner list:
run_params = CodeObjectRunInput(
    input_dataset_uids=[[dataset.uid]],  # ✓ one workgroup, one input slot
)

# Multiple input datasets (parallel inputs):
run_params = CodeObjectRunInput(
    input_dataset_uids=[[dataset1.uid], [dataset2.uid]],  # ✓ two input slots
)
```

### output_dataset_uids is triply-nested

```python
result = code_run.wait_for_completion()

# WRONG — direct access:
uid = result.output_dataset_uids[0]   # ❌ — AttributeError

# CORRECT:
uid = result.output_dataset_uids.root[0].root[0].root[0]  # ✓

# Structure: .root[workgroup_index].root[slot_index].root[dataset_index]
# For single output:
first_output = result.output_dataset_uids.root[0].root[0].root[0]
```

### get_by_name returns None — not an exception

```python
dataset = project.get_dataset_by_name("Typo In Name")
# Returns None, NOT a ResourceNotFoundError

# Always check:
if dataset is None:
    raise ValueError("Dataset not found: check project and name")

# Same for: get_project_by_name, get_code_object_by_name, get_data_schema_by_name, etc.
```

### ECR image URI requires correct constants

```python
import rhino_health as rh

ecr_base_uri = rh.lib.constants.ECRService.PROD_URL
image_uri = f"{ecr_base_uri}/{my_workgroup_ecr_repo}:{my_image_tag}"
```

### DataSchemaCreateInput: use file_path, not schema_fields directly

```python
# Preferred — pass CSV file path:
DataSchemaCreateInput(
    ...
    file_path="./my_schema.csv",   # ✓ reads schema from CSV
)

# Avoid constructing schema_fields manually unless necessary
```

### Enum display strings — use `.value`

SDK enums inherit from `str, Enum`. Printing them directly shows the full enum path (e.g. `SemanticMappingProcessingStatus.APPROVED`). Use `.value` for clean strings.

```python
mapping = session.semantic_mapping.get_semantic_mapping(uid)

# Verbose:
print(mapping.processing_status)          # SemanticMappingProcessingStatus.APPROVED
print(vocab.indexing_status)              # IndexingStatusTypes.NOT_NEEDED

# Clean:
print(mapping.processing_status.value)    # 'Approved'
print(vocab.indexing_status.value)        # 'Not Needed'
print(vocab.type.value)                   # 'custom'
```

### SchemaFields is a RootModel — access via `.root`

`DataSchema.schema_fields` is a `SchemaFields` object (Pydantic `RootModel`), NOT a plain list.

```python
schema = project.get_data_schema_by_name("My Schema")

# WRONG — SchemaFields is not iterable directly:
for field in schema.schema_fields:          # ❌ May not iterate as expected
    print(field.name)
num = len(schema.schema_fields)             # ❌ May not return field count

# CORRECT — access the list via .root:
for field in schema.schema_fields.root:     # ✓ List[SchemaField]
    print(field.name)
num = len(schema.schema_fields.root)        # ✓ correct count

# Shortcut for field names:
names = schema.schema_fields.field_names    # ✓ property
```

### Vocabulary indexing_status enum values

The `Vocabulary.indexing_status` field uses `IndexingStatusTypes` enum. Valid values include `'Not Needed'` — do not confuse with `'Not Started'`.

```python
from rhino_health.lib.endpoints.semantic_mapping.semantic_mapping_dataclass import IndexingStatusTypes

# All valid values:
# IndexingStatusTypes.NOT_NEEDED   = 'Not Needed'
# IndexingStatusTypes.NOT_STARTED  = 'Not Started'
# IndexingStatusTypes.IN_PROGRESS  = 'In Progress'
# IndexingStatusTypes.COMPLETED    = 'Completed'
# IndexingStatusTypes.ERROR        = 'Error'
```

---

## 13. Environment Configuration

`rh.login()` defaults to production (`https://prod.rhinohealth.com/api/`). If your account is on a different environment (dev1, QA, staging), you MUST specify `rhino_api_url`.

```python
import rhino_health as rh
from rhino_health.lib.constants import ApiEnvironment
from getpass import getpass

# Production (default — no rhino_api_url needed):
session = rh.login(username="user@example.com", password=getpass())

# Dev1 environment:
session = rh.login(
    username="user@example.com",
    password=getpass(),
    rhino_api_url=ApiEnvironment.DEV1_AWS_URL,
)

# Or with a raw URL string:
session = rh.login(
    username="user@example.com",
    password=getpass(),
    rhino_api_url="https://dev1.rhinohealth.com/api/",
)
```

**Environment selection from env vars pattern:**
```python
import os
import rhino_health as rh
from rhino_health.lib.constants import ApiEnvironment
from getpass import getpass

ENV_MAP = {
    "prod": ApiEnvironment.PROD_API_URL,
    "dev1": ApiEnvironment.DEV1_AWS_URL,
    "dev2": ApiEnvironment.DEV2_AWS_URL,
    "qa": ApiEnvironment.QA_AWS_URL,
    "staging": ApiEnvironment.STAGING_AWS_URL,
}

username = os.environ.get("RHINO_USERNAME") or input("Username: ")
password = os.environ.get("RHINO_PASSWORD") or getpass("Password: ")
env_name = os.environ.get("RHINO_ENVIRONMENT", "prod")
api_url = ENV_MAP.get(env_name, ApiEnvironment.PROD_API_URL)

session = rh.login(username=username, password=password, rhino_api_url=api_url)
```

**GOTCHA:** If you get HTTP 401 / `NotAuthenticatedError` with correct credentials, the most likely cause is wrong environment URL.

---

## 14. Pydantic RootModel Access

Several SDK dataclasses use Pydantic's `RootModel` to wrap lists. The data lives in `.root`, not directly on the object.

### SchemaFields

```python
schema = project.get_data_schema_by_name("My Schema")

# The schema_fields attribute is a SchemaFields(RootModel), not a list
fields = schema.schema_fields.root          # List[SchemaField]
num_cols = len(schema.schema_fields.root)   # field count
names = schema.schema_fields.field_names    # property shortcut

for field in schema.schema_fields.root:
    print(f"{field.name}: {field.type}")
```

### CodeRun output_dataset_uids

```python
result = code_run.wait_for_completion()

# output_dataset_uids is triply nested via RootModel:
# .root[workgroup_idx].root[slot_idx].root[dataset_idx]
output_uid = result.output_dataset_uids.root[0].root[0].root[0]

# For multi-workgroup runs:
for wg_idx, wg in enumerate(result.output_dataset_uids.root):
    for slot_idx, slot in enumerate(wg.root):
        for ds_uid in slot.root:
            print(f"wg={wg_idx} slot={slot_idx}: {ds_uid}")
```

### General RootModel rule

When you get `TypeError`, `AttributeError`, or unexpected behavior accessing a field that should be a list, try `.root`:
```python
# If obj.some_field doesn't behave like a list:
actual_list = obj.some_field.root  # Try this
```

---

## 15. Semantic Mapping Data Access

To inspect individual term mappings within a semantic mapping, use `get_semantic_mapping_data()`:

```python
# Get the mapping object
mapping = session.semantic_mapping.get_semantic_mapping(mapping_uid)
# — or —
mapping = project.get_semantic_mapping_by_name("country_code_mapping")

# Get all entries (term-level data)
entries = session.semantic_mapping.get_semantic_mapping_data(mapping.uid)

for entry in entries:
    print(f"{entry.source_term_name} → {entry.target_term_name}")
    print(f"  Status: {entry.status}")
    print(f"  Approved: {entry.is_approved}")
    print(f"  Appearances: {entry.num_appearances}")
    print(f"  Recommendations: {entry.recommendation_data}")
```

**SemanticMappingEntry fields:**
- `entry_uid` — unique entry ID
- `source_term_name` — the source data value
- `target_term_name` — the mapped target vocabulary term
- `recommendation_data` — `List[Dict]` with AI recommendations and confidence scores
- `num_appearances` — how many times the source term appeared in the dataset
- `status` — `'calculating'`, `'failed'`, `'needs_review'`, or `'approved'`
- `is_approved` — boolean
- `approved_by` — `Dict[str, str]` with approver info
- `index` — entry position

**Inspecting AI recommendations:**
```python
for entry in entries:
    if entry.recommendation_data:
        top = entry.recommendation_data[0]
        score = top.get("score", 0)
        term = top.get("term_display_name", "")
        print(f"{entry.source_term_name}: top recommendation = {term} ({score:.1%})")

        if len(entry.recommendation_data) > 1:
            runner_up = entry.recommendation_data[1]
            gap = score - runner_up.get("score", 0)
            print(f"  Runner-up gap: {gap:.3f}")
```

---

## 16. Session Persistence & Reuse

Use `session_info()` to persist session state and restore it later without re-authenticating:

```python
import rhino_health as rh
from getpass import getpass

# First session — authenticate normally
session = rh.login(username="user@example.com", password=getpass())

# Save session info (dict with session_token, session_timeout, etc.)
info = session.session_info()

# Later — restore without re-authenticating:
restored = rh.login(authentication_details=info)

# Or pass to another process / script:
import json
with open("session.json", "w") as f:
    json.dump(info, f)

# ... in another script:
with open("session.json") as f:
    info = json.load(f)
session = rh.login(authentication_details=info)
```

**SSO authentication:**
```python
# Google SSO:
session = rh.login(authentication_details={
    "sso_access_token": "MyAccessToken",
    "sso_provider": "google",
    "sso_client": "my_hospital",
})

# Azure AD SSO:
session = rh.login(authentication_details={
    "sso_access_token": "MyAccessToken",
    "sso_id_token": "MyIdToken",
    "sso_provider": "azure_ad",
})
```

---

## 17. Raw API Escape Hatch (SDK/API Version Mismatch)

When the Rhino backend API adds new values (e.g. a new enum like `"Not Needed"`) but the locally installed SDK hasn't been updated to match, Pydantic validation crashes even though the HTTP request succeeds with 200 OK. The typical error:

```
ValidationError: Input should be 'Not Started', 'In Progress', 'Completed' or 'Error'
  input_value='Not Needed', input_type=str
```

**DO NOT** try to construct raw HTTP requests with `requests.get()` — you'll get the URL wrong, the auth wrong, or both. Instead, use the SDK's own HTTP client and bypass only the deserialization layer:

```python
# The SDK session has .get() and .post() methods that handle auth + base URL.
# The result has .raw_response with the raw requests.Response object.

result = session.get("/vocabularies", params={"project_uid": project.uid})
items = result.raw_response.json().get("data", [])

for item in items:
    print(f"  {item['name']} — {item.get('indexing_status', 'unknown')} — {item['uid']}")
```

**Why this works:**
1. `session.get(path, params=...)` uses the SDK's internal HTTP client — it already knows the base URL and handles auth tokens
2. `result.raw_response` gives the raw `requests.Response` before Pydantic parsing
3. `.json()` returns plain dicts, bypassing the broken dataclass entirely

**General pattern for any endpoint:**
```python
# GET with query params
result = session.get("/vocabularies", params={"project_uid": project.uid})
data = result.raw_response.json()

# GET a specific resource by UID
result = session.get(f"/vocabularies/{vocab_uid}")
vocab_data = result.raw_response.json()

# POST (for create/update operations)
result = session.post("/some-endpoint", data={"key": "value"})
response_data = result.raw_response.json()
```

**When to use this pattern:**
- `ValidationError` from Pydantic on a field that the API returns successfully
- SDK enum doesn't include a new backend value
- SDK dataclass is missing a new field the API returns
- Any case where the HTTP call works (200 OK) but the SDK model crashes

**When NOT to use this pattern:**
- HTTP errors (401, 403, 404, 500) — these are real API errors, not SDK bugs
- Normal SDK usage that works fine — always prefer the typed SDK methods

**Known SDK/API mismatches (update your SDK to fix):**

| Symptom | Cause | Raw API workaround |
|---------|-------|-------------------|
| Vocabulary `indexing_status` rejects `"Not Needed"` | SDK < 2.1.20 missing `IndexingStatusTypes.NOT_NEEDED` | `session.get("/vocabularies", params={"project_uid": uid})` |
| New fields missing from dataclass | SDK older than API version | Access via `.raw_response.json()` and read dict keys |

**First choice is always to upgrade the SDK:** `pip install --upgrade rhino-health`. The raw API escape hatch is for when you can't upgrade immediately.
