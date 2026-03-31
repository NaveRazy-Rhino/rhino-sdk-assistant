# SDK Examples Index

All examples sourced from https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk

---

## Examples

| File | Use Case | Key SDK Methods | Level | Read First |
|------|----------|----------------|-------|-----------|
| [`eda.py`](eda.py) | Exploratory data analysis: per-site & aggregate metrics, filtering, grouping, range filters | `get_dataset_metric`, `aggregate_dataset_metric`, `Count`, `Mean`, `StandardDeviation`, `FilterType` | Basic | `patterns_and_gotchas.md` §4–6 |
| [`aggregate_quantile.py`](aggregate_quantile.py) | Federated percentile calculations | `Percentile`, `aggregate_dataset_metric` | Basic | `metrics_reference.md` §Quantile |
| [`upsert_objects.py`](upsert_objects.py) | Create/version/search datasets & code objects | `add_dataset`, `create_code_object`, `return_existing`, `add_version_if_exists`, `VersionMode`, `NameFilterMode` | Basic | `patterns_and_gotchas.md` §3 |
| [`cox.py`](cox.py) | Cox proportional hazard regression across federated sites | `Cox`, `aggregate_dataset_metric`, `get_project_by_name`, `get_dataset_by_name` | Intermediate | `metrics_reference.md` §Survival |
| [`metrics_examples.py`](metrics_examples.py) | Comprehensive metrics: TwoByTwoTable, OddsRatio, ChiSquare, TTest, OneWayANOVA | `TwoByTwoTable`, `OddsRatio`, `ChiSquare`, `TTest`, `OneWayANOVA`, `aggregate_dataset_metric` | Intermediate | `metrics_reference.md` §Epidemiology, §Stats |
| [`roc_analysis.py`](roc_analysis.py) | ROC curves, confidence intervals, group-by analysis, report upload | `RocAuc`, `RocAucWithCI`, `dataset.get_metric`, `group_by`, `session.post` | Intermediate | `metrics_reference.md` §ROC |
| [`sql_data_ingestion.py`](sql_data_ingestion.py) | On-prem SQL queries; import query results as datasets | `SQLQueryInput`, `SQLQueryImportInput`, `ConnectionDetails`, `run_sql_query`, `import_dataset_from_sql_query` | Intermediate | `sdk_reference.md` §SQLQueryEndpoints |
| [`train_test_split.py`](train_test_split.py) | Generalized Compute code object with multiple output datasets and naming templates | `CodeObjectCreateInput`, `CodeObjectRunInput`, `CodeTypes.GENERALIZED_COMPUTE`, `output_dataset_naming_templates` | Intermediate | `patterns_and_gotchas.md` §8, `sdk_reference.md` §CodeObjectEndpoints |
| [`runtime_external_files.py`](runtime_external_files.py) | Python code object using S3 bucket files at runtime | `CodeTypes.PYTHON_CODE`, `external_storage_file_paths`, `code_execution_mode: snippet` | Intermediate | `patterns_and_gotchas.md` §8, §10 |
| [`federated_join.py`](federated_join.py) | SQL-like joins across distributed datasets (INTERSECTION & UNION modes) | `joined_dataset_metric`, `JoinMode`, `join_field`, `filter_datasets`, `query_datasets`, `data_filters` | Advanced | `patterns_and_gotchas.md` §7, `sdk_reference.md` §ProjectEndpoints |
| [`fhir_pipeline.py`](fhir_pipeline.py) | End-to-end: data harmonization → FHIR generation → CSV export | `run_data_harmonization`, `DataHarmonizationRunInput`, `run_code_object`, `export_dataset`, `output_dataset_uids.root` | Advanced | `sdk_reference.md` §SyntacticMappingEndpoints, `patterns_and_gotchas.md` §9 |

---

## Patterns By Example

### Authentication
All examples use:
```python
import rhino_health as rh
from getpass import getpass

session = rh.login(username="email@example.com", password=getpass())
```

### Getting Data
```python
# By UID
dataset = session.dataset.get_dataset(uid)

# By name via project (returns None if not found — NOT an exception)
project = session.project.get_project_by_name("Name")
dataset = project.get_dataset_by_name("Name")
```

### Running Metrics
```python
# Per-site
result = session.dataset.get_dataset_metric(dataset_uid, config)
result = dataset.get_metric(config)  # shorthand

# Aggregated across sites (List[str] of UIDs required!)
result = session.project.aggregate_dataset_metric(
    [str(d.uid) for d in datasets], config
)

# Federated join
result = session.project.joined_dataset_metric(
    configuration=config,
    query_datasets=[query_dataset.uid],
    filter_datasets=[filter_dataset.uid]  # optional
)
```

### Code Object Run Lifecycle
```python
code_object = session.code_object.create_code_object(params)
code_object.wait_for_build()  # Generalized Compute only

code_run = session.code_object.run_code_object(run_params)
result = code_run.wait_for_completion()

# Access output datasets (triply-nested!)
output_uid = result.output_dataset_uids.root[0].root[0].root[0]
```
