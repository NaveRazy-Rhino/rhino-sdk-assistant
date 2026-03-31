"""
Pneumonia Model Results Analysis — ROC Curves
Source: https://github.com/RhinoHealth/user-resources/tree/main/examples/rhino-sdk/pneumonia-results-analysis.ipynb

Demonstrates: RocAuc, RocAucWithCI, group_by analysis, visualization, report upload.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import base64
import json
from getpass import getpass
import rhino_health
from rhino_health.lib.metrics import RocAuc, RocAucWithCI

# --- Login ---
my_username = "my_email@example.com"
session = rhino_health.login(username=my_username, password=getpass())

# --- Load Dataset ---
site1_results_dataset = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
dataset = session.dataset.get_dataset(site1_results_dataset)
print(f"Loaded dataset '{dataset.name}'")

# --- Basic ROC ---
metric_configuration = RocAuc(y_true_variable="Pneumonia", y_pred_variable="ModelScore")
results = dataset.get_metric(metric_configuration)
roc_metrics = results.output

fig, ax = plt.subplots(figsize=[6, 4], dpi=200)
ax.plot(roc_metrics['fpr'], roc_metrics['tpr'])
ax.set_title('Overall ROC')
ax.set_xlabel('1 - Specificity')
ax.set_ylabel('Sensitivity')
ax.grid(True)
ax.set_xlim([0, 1])
ax.set_ylim([0, 1])

# --- ROC with Confidence Interval ---
metric_configuration = RocAucWithCI(
    timeout_seconds=30.0,
    y_true_variable="Pneumonia",
    y_pred_variable="ModelScore",
    confidence_interval=95
)
results = dataset.get_metric(metric_configuration)
roc_metrics = results.output
tpr_ci = roc_metrics['tpr_ci']

fig, ax = plt.subplots(figsize=[6, 4], dpi=200)
ax.fill_between(roc_metrics['fpr'], tpr_ci[0], tpr_ci[1], alpha=0.33)
ax.plot(roc_metrics['fpr'], roc_metrics['tpr'])
ax.set_title('Overall ROC with Confidence Interval')

# --- ROC Grouped by Gender ---
metric_configuration = RocAuc(
    y_true_variable="Pneumonia",
    y_pred_variable="ModelScore",
    group_by={'groupings': ['Gender']}
)
results = dataset.get_metric(metric_configuration)

for group in results.output.keys():
    roc_metrics = results.output[group]
    fig, ax = plt.subplots(figsize=[6, 4], dpi=200)
    ax.plot(roc_metrics['fpr'], roc_metrics['tpr'])
    ax.set_title(group)

# --- Upload Report to FCP ---
code_result_uid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

def add_images_to_report(report_data, image_files):
    for image_file in image_files:
        with open(image_file, "rb") as temp_image:
            base_64_image = base64.b64encode(temp_image.read()).decode("utf-8")
            report_data.append({
                "type": "Image",
                "data": {"image_filename": image_file, "image_base64": base_64_image},
                "width": 100 / len(image_files)
            })

report_data = []
report_data.append({"type": "Title", "data": "Overall ROC"})
add_images_to_report(report_data, ('Overall_ROC.png', 'Overall_ROC_CI.png'))

result = session.post(
    f"code_runs/{code_result_uid}/set_report/",
    data={"report_data": json.dumps(report_data)}
)
