# Rhino Health SDK — Metrics Reference

All metrics live under `rhino_health.lib.metrics`.  
Run metrics with:
- **Per-site:** `session.dataset.get_dataset_metric(dataset_uid, config)` or `dataset.get_metric(config)`
- **Aggregated:** `session.project.aggregate_dataset_metric(dataset_uids, config)`
- **Federated join:** `session.project.joined_dataset_metric(config, query_datasets, filter_datasets)`

---

## Base Types

### BaseMetric (pydantic BaseModel)

Every metric inherits from `BaseMetric`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `data_filters` | List[DataFilter] \| None | [] | Filters applied to dataset before metric |
| `group_by` | GroupingData \| None | None | Group results by column(s) |
| `timeout_seconds` | float \| None | 600.0 | Execution timeout |
| `count_variable_name` | str | 'variable' | Column name for count aggregations |

### DataFilter

Used in the `data_filters` list. Applies column-level filters.

| Field | Type | Default |
|-------|------|---------|
| `filter_column` | str | required |
| `filter_value` | Any \| FilterBetweenRange | required |
| `filter_type` | FilterType | FilterType.EQUAL |
| `filter_dataset` | str \| None | None (scope to specific dataset in federated join) |

### GroupingData

| Field | Type | Default |
|-------|------|---------|
| `groupings` | List[str] | required |
| `dropna` | bool | True |

```python
# Usage:
Mean(variable="Height", group_by={"groupings": ["Gender"]})
```

### MetricResponse

Return type of all metric calls.

| Field | Type |
|-------|------|
| `output` | Dict[str, Any] |
| `metric_configuration_dict` | Dict |
| `dataset_uids` | List[str] |

```python
result = session.dataset.get_dataset_metric(dataset.uid, config)
print(result.output)  # dict with metric results
```

### FilterType (Enum)

```python
from rhino_health.lib.metrics import FilterType

FilterType.EQUAL              # =
FilterType.IN                 # value in list
FilterType.NOT_IN
FilterType.GREATER_THAN       # >
FilterType.LESS_THAN          # <
FilterType.GREATER_THAN_EQUAL # >=
FilterType.LESS_THAN_EQUAL    # <=
FilterType.BETWEEN            # requires FilterBetweenRange as filter_value
```

### FilterVariable (dict or typed object)

Pass either a plain column name (`str`) or a `FilterVariable`-shaped dict:

```python
# Simple column name:
Mean(variable="Height")

# FilterVariable dict — filter before accessing column:
Mean(variable={
    "data_column": "Height",      # column to measure
    "filter_column": "Gender",    # column to filter on
    "filter_value": "M",          # value to match
    "filter_type": FilterType.EQUAL  # optional, defaults to EQUAL
})
```

### FilterBetweenRange

For `FilterType.BETWEEN` — specify lower and upper bounds:

```python
Mean(variable={
    "data_column": "Height",
    "filter_column": "Weight",
    "filter_value": {
        "lower": {"filter_value": 70, "filter_type": FilterType.GREATER_THAN_EQUAL},
        "upper": {"filter_value": 100, "filter_type": FilterType.LESS_THAN_EQUAL},
    },
    "filter_type": FilterType.BETWEEN,
})
```

### JoinMode (Enum)

```python
from rhino_health.lib.metrics.base_metric import JoinMode

JoinMode.INTERSECTION   # inner join — only shared identifiers across datasets
JoinMode.UNION          # outer join — all rows, deduplicated
```

---

## Basic Metrics

All extend `JoinableMetric` — support federated joins via `join_field` and `join_mode`.

**Import:** `from rhino_health.lib.metrics import Count, Mean, StandardDeviation, Sum`

| Metric | Required Parameters | Description |
|--------|--------------------|-|
| `Count` | `variable` | Count of entries |
| `Mean` | `variable` | Arithmetic mean |
| `StandardDeviation` | `variable` | Standard deviation |
| `Sum` | `variable` | Sum of values |

All accept: `variable` (str or FilterVariable), `group_by`, `data_filters`, `join_field`, `join_mode`.

**Usage examples:**
```python
from rhino_health.lib.metrics import Count, Mean, StandardDeviation

# Count patients
Count(variable="patient_id")

# Mean height
Mean(variable="Height")

# Mean height for males only
Mean(variable={"data_column": "Height", "filter_column": "Gender", "filter_value": "M"})

# Mean grouped by gender
Mean(variable="Height", group_by={"groupings": ["Gender"]})

# Aggregate across sites
result = session.project.aggregate_dataset_metric(
    [str(d.uid) for d in datasets],
    Mean(variable="Height")
)
```

---

## Quantile Metrics

All extend `AggregatableMetric`.

**Import:** `from rhino_health.lib.metrics import Percentile, Median, Min, Max`

| Metric | Required Parameters | Description |
|--------|--------------------|-|
| `Median` | `variable` | Median value |
| `Percentile` | `variable`, `percentile: int\|float` | K-th percentile |
| `Min` | `variable` | Minimum value |
| `Max` | `variable` | Maximum value |

**Usage example:**
```python
from rhino_health.lib.metrics import Percentile

# 90th percentile of Weight, federated
result = session.project.aggregate_dataset_metric(
    [str(d.uid) for d in datasets],
    Percentile(variable="Weight", percentile=90)
)
print(result.output["Weight"])
```

---

## Survival Analysis

**Import:** `from rhino_health.lib.metrics import KaplanMeier, Cox`

### KaplanMeier

| Parameter | Type | Description |
|-----------|------|-------------|
| `time_variable` | str \| FilterVariable | Time-to-event column |
| `event_variable` | str \| FilterVariable | Binary event indicator (1=event, 0=censored) |

**Usage:**
```python
from rhino_health.lib.metrics import KaplanMeier

result = session.project.aggregate_dataset_metric(
    dataset_uids, KaplanMeier(time_variable="Time", event_variable="Event")
)
```

### Cox

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `time_variable` | str \| FilterVariable | required | Time-to-event column |
| `event_variable` | str \| FilterVariable | required | Binary event indicator |
| `covariates` | List[str \| FilterVariable] \| None | None | Covariate columns |
| `initial_beta` | "zero" \| "mean" \| None | None | Initial coefficient estimate |
| `max_iterations` | int | 100 | Max optimization iterations |
| `accuracy` | float | 1e-06 | Convergence threshold |

**Usage:**
```python
from rhino_health.lib.metrics import Cox

result = session.project.aggregate_dataset_metric(
    [str(d.uid) for d in datasets],
    Cox(
        time_variable="Time",
        event_variable="Event",
        covariates=["Age", "Smoking"],
        initial_beta="mean",
        max_iterations=50
    )
)
print(result.output)  # dict with coefficients, p-values, etc.
```

---

## Classification Metrics

All extend `AggregatableMetric`. All parameters accept `FilterVariableTypeOrColumnName`.

**Import:** `from rhino_health.lib.metrics import AccuracyScore, F1Score, ConfusionMatrix, ...`

| Metric | Key Parameters |
|--------|---------------|
| `AccuracyScore` | y_true, y_pred, normalize=True |
| `F1Score` | y_true, y_pred, average='binary', pos_label=1 |
| `PrecisionScore` | y_true, y_pred, average='binary', pos_label=1 |
| `RecallScore` | y_true, y_pred, average='binary', pos_label=1 |
| `ConfusionMatrix` | y_true, y_pred, labels, normalize=True |
| `AveragePrecisionScore` | y_true, y_score, average='macro', pos_label=1 |
| `BalancedAccuracyScore` | y_true, y_pred, adjusted=False |
| `BrierScoreLoss` | y_true, y_prob, pos_label |
| `CohenKappaScore` | y1, y2, labels, weights |
| `LogLoss` | y_true, y_pred, normalize=True |
| `MatthewsCorrelationCoefficient` | y_true, y_pred |
| `TopKAccuracyScore` | y_true, y_score, k=2, normalize=True |
| `ZeroOneLoss` | y_true, y_score, normalize=True |

---

## ROC / AUC

**Import:** `from rhino_health.lib.metrics import RocAuc, RocAucWithCI`

### RocAuc

| Parameter | Type |
|-----------|------|
| `y_true_variable` | str \| FilterVariable |
| `y_pred_variable` | str \| FilterVariable |
| `seed` | int \| None |

### RocAucWithCI (extends RocAuc)

Additional parameters: `confidence_interval: int` (e.g. 95), `bootstrap_iterations: int | None`

**Usage:**
```python
from rhino_health.lib.metrics import RocAuc, RocAucWithCI

# Basic ROC
result = dataset.get_metric(
    RocAuc(y_true_variable="Pneumonia", y_pred_variable="ModelScore")
)
roc = result.output  # keys: fpr, tpr, roc_auc

# With confidence interval
result = dataset.get_metric(
    RocAucWithCI(
        y_true_variable="Pneumonia",
        y_pred_variable="ModelScore",
        confidence_interval=95
    )
)

# Grouped by Gender
result = dataset.get_metric(
    RocAuc(
        y_true_variable="Pneumonia",
        y_pred_variable="ModelScore",
        group_by={"groupings": ["Gender"]}
    )
)
```

### FRoc / FRocWithCI

| Parameter | Type |
|-----------|------|
| `y_true_variable` | FilterVariable |
| `y_pred_variable` | FilterVariable |
| `specimen_variable` | FilterVariable |
| `seed` | int \| None |

`FRocWithCI` adds: `confidence_interval: int`, `bootstrap_iterations: int | None`

---

## Statistical Tests

All extend `AggregatableMetric`.

**Import:** `from rhino_health.lib.metrics.statistics_tests import ChiSquare, TTest, OneWayANOVA, Pearson, Spearman, ICC, Wilcoxon`

| Metric | Parameters | Description |
|--------|-----------|-------------|
| `ChiSquare` | variable, variable_1, variable_2 | Chi-square test of independence |
| `TTest` | numeric_variable, categorical_variable | Welch's two-sample t-test |
| `OneWayANOVA` | variable, numeric_variable, categorical_variable | One-way ANOVA |
| `Pearson` | variable_1, variable_2 | Pearson correlation coefficient |
| `Spearman` | variable_1, variable_2 | Spearman rank correlation |
| `ICC` | variable_1, variable_2 | Intraclass correlation coefficient |
| `Wilcoxon` | variable, abs_values_variable | Wilcoxon signed-rank test |

**Usage:**
```python
from rhino_health.lib.metrics.statistics_tests import ChiSquare, TTest, OneWayANOVA

# Chi-square: test independence of Pneumonia and Smoking
result = session.project.aggregate_dataset_metric(
    dataset_uids,
    ChiSquare(variable="id", variable_1="Pneumonia", variable_2="Smoking")
)

# T-test: compare SpO2 between Pneumonia groups
result = session.project.aggregate_dataset_metric(
    dataset_uids,
    TTest(numeric_variable="Spo2 Level", categorical_variable="Pneumonia")
)

# ANOVA
result = project.aggregate_dataset_metric(
    dataset_uids,
    OneWayANOVA(variable="id", numeric_variable="Spo2 Level", categorical_variable="Inflammation Level")
)
```

---

## Epidemiology

### Two-by-Two Table Metrics

**Import:** `from rhino_health.lib.metrics.epidemiology.two_by_two_table_based_metrics import TwoByTwoTable, OddsRatio, Risk, RiskRatio, Odds`

All share: `variable`, `detected_column_name`, `exposed_column_name`

| Metric | Description |
|--------|-------------|
| `TwoByTwoTable` | Returns 2×2 contingency table |
| `OddsRatio` | Calculates odds ratio with confidence interval |
| `Risk` | Returns absolute risk |
| `RiskRatio` | Computes risk ratio |
| `Odds` | Ratio of positive to negative (params: `variable`, `column_name`) |

**TwoByTwoTableMetricResponse** helper methods: `as_table()`, `as_dataframe()`, `risk()`, `risk_ratio()`, `odds()`, `odds_ratio()`

**Usage:**
```python
from rhino_health.lib.metrics.epidemiology.two_by_two_table_based_metrics import TwoByTwoTable, OddsRatio

# 2x2 table: Pneumonia × Smoking
result = session.project.aggregate_dataset_metric(
    dataset_uids,
    TwoByTwoTable(
        variable="id",
        detected_column_name="Pneumonia",
        exposed_column_name="Smoking"
    )
)

# Odds ratio
result = session.project.aggregate_dataset_metric(
    dataset_uids,
    OddsRatio(variable="id", detected_column_name="Pneumonia", exposed_column_name="Smoking")
)
```

### Time Range Metrics

**Import:** `from rhino_health.lib.metrics.epidemiology.time_range_based_metrics import Prevalence, Incidence`

Common params: `variable`, `detected_column_name`, `time_column_name`, `start_time`, `end_time`

| Metric | Description |
|--------|-------------|
| `Prevalence` | Proportion with condition at a point in time |
| `Incidence` | New cases over a time period |

---

## Quick Decision Guide

| Question | Metric to Use |
|----------|--------------|
| How many records? | `Count` |
| Average / mean of a column? | `Mean` |
| Distribution spread? | `StandardDeviation` |
| Percentiles / quartiles? | `Percentile`, `Median`, `Min`, `Max` |
| Survival analysis? | `KaplanMeier` (curve) or `Cox` (regression) |
| Binary classifier performance? | `RocAuc`, `RocAucWithCI`, `F1Score`, `AccuracyScore` |
| Two categorical variables related? | `ChiSquare`, `TwoByTwoTable` |
| Compare means between groups? | `TTest` (2 groups) or `OneWayANOVA` (3+ groups) |
| Odds / risk of outcome? | `OddsRatio`, `RiskRatio`, `TwoByTwoTable` |
| Correlation between two columns? | `Pearson` (linear), `Spearman` (rank) |
| Prevalence / incidence? | `Prevalence`, `Incidence` |
