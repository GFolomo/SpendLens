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

## Dataset and scope

The source workbook covers 1 December 2010 to 9 December 2011. Its eight fields record the invoice number, stock code, product description, quantity, invoice date, unit price, customer ID and country. Sales shares below the project heading refer to customers with positive net sales after cleaning.

## From invoice lines to customer profiles

### 1. Define the business question

Which customers buy frequently, and which account for the most sales? The unit of analysis is one customer. With no preassigned customer labels, the project uses unsupervised clustering to find groups that a marketing team could target differently.

### 2. Explore and clean the invoice data

The notebook loads the Excel workbook into pandas and checks its shape, data types, missing values and duplicate records. Of 541,909 invoice lines, 135,080 lack a customer ID and cannot be attributed to a buyer. Removing those rows and 5,225 duplicate lines leaves 401,604 lines for customer-level aggregation.

### 3. Engineer and explore customer features

For each customer, the notebook computes **net sales** by summing quantity × unit price across their invoice lines. It measures **purchasing frequency** by counting distinct invoice numbers, so buying several products on one invoice counts once. Aggregation yields 4,372 customer profiles. Keeping customers with positive net sales leaves 4,322 for modelling.

The median customer has three invoices, while the maximum is 248. A scatter plot of spend against invoice count shows that the features also have very different numerical ranges. Because K-means assigns customers by distance, the notebook applies scikit-learn’s `StandardScaler` to both features before fitting the model.

### 4. Establish a clustering baseline

The notebook fits K-means for one through ten clusters and plots inertia, the sum of squared distances from customers to their assigned cluster centres. The elbow plot guides the choice of a four-cluster baseline. A scatter plot shows the assignments, and a two-component PCA view provides a second way to inspect the same groups. The model uses the two standardised customer features.

### 5. Tune and evaluate the model

A manual grid search compares 16 configurations across three to six clusters, one or 20 initialisations, and a limit of one or 100 iterations per start. The notebook selects the configuration with the highest silhouette score, a measure of how closely customers resemble their own group relative to neighbouring groups.

| Metric | Four-cluster baseline | Best value observed in the search |
| --- | ---: | ---: |
| Silhouette score (higher is better) | 0.768 | 0.878 |
| Davies–Bouldin index (lower is better) | 0.648 | 0.612 |

The silhouette winner uses three clusters, k-means++ initialisation, 20 starts and one iteration per start. The notebook tracks the lowest Davies–Bouldin index independently across all configurations. The scores describe cluster separation within this dataset.

### 6. Interpret the segments for marketing

The notebook groups customers by their final labels and summarises spend and invoice counts in their original units. The moderate-spend group averages 41.2 invoices per customer, compared with 4.1 in the lower-spend group. That repeat buying makes the 109 moderate spenders a candidate audience for a cross-selling test. The four high-value customers account for 10.3% of cohort net sales, which supports a separate retention proposal.

Before using the segments for ongoing campaigns, check whether the four-customer group persists across random seeds, additional iterations and later purchase periods. A controlled campaign test could then measure whether targeting improves sales.

## Further analysis

Test whether adding time since last purchase helps distinguish dormant customers from occasional buyers. Compare the resulting segments with hierarchical clustering and DBSCAN. Customer surveys could then explore why buying patterns differ across groups.

## Run the notebook

Download the Excel workbook from the [dataset page](https://www.kaggle.com/datasets/yasserh/customer-segmentation-dataset) and save it as `data.xlsx` beside `SpendLens_Clustering_ML.ipynb`. From that directory, run the following in a Python environment, then execute the notebook cells in order.

```sh
python -m pip install jupyterlab pandas numpy scikit-learn matplotlib seaborn openpyxl
python -m jupyterlab SpendLens_Clustering_ML.ipynb
```
