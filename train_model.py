from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

data = pd.read_excel(sys.argv[1]).dropna(subset=["CustomerID"]).drop_duplicates()
data["Spend"] = data.Quantity * data.UnitPrice
x = data.groupby("CustomerID").agg(Spend=("Spend", "sum"), Invoices=("InvoiceNo", "nunique"))
x = x[x.Spend > 0]
scaler = StandardScaler()
scaled = scaler.fit_transform(x)
model = KMeans(n_clusters=3, n_init=20, init="k-means++", max_iter=1, random_state=42).fit(scaled)
order = np.argsort(model.cluster_centers_[:, 0])
counts = np.bincount(model.labels_)[order]
print("Lower, moderate, high:", counts)
if counts.tolist() != [4209, 109, 4]:
    raise ValueError("Training results differ from notebook")
Path(__file__).with_name("model.json").write_text(json.dumps(dict(mean=scaler.mean_.tolist(), scale=scaler.scale_.tolist(), centers=model.cluster_centers_[order].tolist()), indent=2))
sample = x.assign(Segment=np.asarray(["Lower spend", "Moderate spend", "High value"])[np.argsort(order)[model.labels_]])
sample.index = [f"DEMO-{number:05d}" for number in range(1, len(sample) + 1)]
sample.index.name = "CustomerID"
sample.to_csv(Path(__file__).with_name("sample_profiles.csv"))
