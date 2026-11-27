# SpendLens | ML Customer Segmentation

Which retail customers warrant a cross-selling campaign, and which merit individual attention? SpendLens uses K-means to group **4,322 customers** by total spend and invoice count. Four customers accounted for **10.3% of net sales** in the analysed cohort.

[Explore the analysis notebook](SpendLens_Clustering_ML.ipynb) · [View the source dataset](https://www.kaggle.com/datasets/yasserh/customer-segmentation-dataset)

## Customer segments

| Segment | Customers | Mean invoices per customer | Share of cohort net sales |
| --- | ---: | ---: | ---: |
| Lower spend | 4,209 | 4.1 | 62.6% |
| Moderate spend | 109 | 41.2 | 27.1% |
| High value | 4 | 110.5 | 10.3% |

The 109 moderate spenders are a candidate audience for a cross-selling test because they already buy frequently. The four high-value customers merit individual retention outreach. Both are recommendations. The notebook measures historical purchasing behaviour, and campaign lift would require a separate test.

## From invoice lines to customer profiles

1. Start with 541,909 retail line items. Remove records without a customer ID and drop duplicate rows.
2. Multiply quantity by unit price, sum the resulting sales by customer and count distinct invoice numbers. Keep customers with positive net sales.
3. Standardise the two features and fit K-means in scikit-learn. Compare three to six clusters and use principal component analysis (PCA) to visualise the assignments.

| Evaluation metric | Four-cluster baseline | Selected three-cluster model |
| --- | ---: | ---: |
| Silhouette score (higher is better) | 0.768 | 0.878 |
| Davies–Bouldin index (lower is better) | 0.648 | 0.612 |

These scores describe separation within the observed data. The selected configuration used one K-means iteration, and the smallest segment contains just four customers. Before using these groups for ongoing campaigns, check whether assignments hold across random seeds, additional iterations and later purchase periods.

## Run the notebook

Download the Excel workbook from the [dataset page](https://www.kaggle.com/datasets/yasserh/customer-segmentation-dataset) and save it as `data.xlsx` beside `SpendLens_Clustering_ML.ipynb`. From that directory, run the following in a Python environment, then execute the notebook cells in order.

```sh
python -m pip install jupyterlab pandas numpy scikit-learn matplotlib seaborn openpyxl
python -m jupyterlab SpendLens_Clustering_ML.ipynb
```
