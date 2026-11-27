import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
SEGMENTS = ["Lower spend", "Moderate spend", "High value"]
COLORS = ["#5888b8", "#168975", "#cc951e"]
REQUIRED = ["CustomerID", "InvoiceNo", "Quantity", "UnitPrice"]

st.set_page_config(page_title="SpendLens", layout="wide")
st.sidebar.title("SpendLens")
source = st.sidebar.radio("Data source", ["Sample dataset", "Upload file"])
subtitle = "Dec 2010 to Dec 2011 · Online Retail sample"

if source == "Sample dataset":
    profiles = pd.read_csv(ROOT / "sample_profiles.csv")
else:
    st.sidebar.caption("Use approximately 12 months of invoice history.")
    upload = st.sidebar.file_uploader("Upload invoice history", type=["csv", "xlsx"])
    if upload is None:
        st.title("Customer segments")
        st.info("Upload a CSV or Excel workbook with CustomerID, InvoiceNo, Quantity and UnitPrice.")
        st.stop()
    try:
        dtype = {"CustomerID": "string", "InvoiceNo": "string"}
        data = pd.read_csv(upload, dtype=dtype) if upload.name.lower().endswith(".csv") else pd.read_excel(upload, dtype=dtype)
        missing = set(REQUIRED) - set(data.columns)
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        original_rows = len(data)
        data = data.drop_duplicates().copy()
        for column in ["Quantity", "UnitPrice"]:
            data[column] = pd.to_numeric(data[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
        for column in ["CustomerID", "InvoiceNo"]:
            data[column] = data[column].str.strip().replace("", pd.NA)
        data = data.dropna(subset=REQUIRED).copy()
        data["Spend"] = data.Quantity * data.UnitPrice
        data = data[np.isfinite(data.Spend)]
        profiles = data.groupby("CustomerID", as_index=False).agg(Spend=("Spend", "sum"), Invoices=("InvoiceNo", "nunique"))
        profiles = profiles[(profiles.Spend > 0) & np.isfinite(profiles.Spend)].copy()
        if profiles.empty:
            raise ValueError("No customers with positive net sales remain after cleaning.")
        model = json.loads((ROOT / "model.json").read_text())
        scaled = (profiles[["Spend", "Invoices"]].to_numpy() - model["mean"]) / model["scale"]
        distances = np.linalg.norm(scaled[:, None] - model["centers"], axis=2)
        profiles["Segment"] = np.asarray(SEGMENTS)[distances.argmin(axis=1)]
        subtitle = f"Uploaded batch · {len(data):,} invoice lines used"
        st.sidebar.caption(f"{original_rows - len(data):,} duplicate or incomplete lines excluded.")
    except (ValueError, OSError, ImportError, KeyError) as error:
        st.error(f"Unable to analyse this file. {error}")
        st.stop()

st.title("Customer segments")
st.caption(f"{len(profiles):,} customers · {subtitle}")
total_sales = profiles.Spend.sum()
for column, segment, color in zip(st.columns(3), SEGMENTS, COLORS):
    group = profiles[profiles.Segment == segment]
    with column:
        st.markdown(
            f'<div style="border-left:5px solid {color};background:{color}18;padding:16px;border-radius:10px">'
            f'<strong>{segment}</strong><br>{len(group):,} customers<br>'
            f'{group.Spend.sum()/total_sales:.1%} of net sales</div>',
            unsafe_allow_html=True,
        )

st.write("")
plot, campaign = st.columns([2, 1])
with plot:
    with st.container(border=True):
        st.subheader("Spend and invoice frequency")
        chart = alt.Chart(profiles).mark_circle(size=40, opacity=0.65).encode(
            x=alt.X("Invoices:Q", title="Invoice count"),
            y=alt.Y("Spend:Q", title="Net sales (log scale)", scale=alt.Scale(type="log")),
            color=alt.Color("Segment:N", scale=alt.Scale(domain=SEGMENTS, range=COLORS), legend=alt.Legend(orient="bottom")),
            tooltip=["Segment:N", "Invoices:Q", alt.Tooltip("Spend:Q", format=",.2f")],
        ).properties(height=380).interactive()
        with alt.data_transformers.enable("default", max_rows=None):
            st.altair_chart(chart, use_container_width=True)
with campaign:
    with st.container(border=True):
        st.subheader("Campaign audience")
        target = st.selectbox("Segment", SEGMENTS, index=1)
        audience = profiles[profiles.Segment == target].sort_values("Spend", ascending=False)
        campaign_type = {"Lower spend": "Re-engagement", "Moderate spend": "Cross-selling", "High value": "Retention"}
        st.write(f"{len(audience):,} customers · {campaign_type[target]}")
        export = audience.copy()
        export["CustomerID"] = export.CustomerID.astype(str).str.replace(r"^([=+@\-\t\r])", r"'\1", regex=True)
        st.download_button("Download audience CSV", export.to_csv(index=False), "spendlens-audience.csv", "text/csv", disabled=audience.empty, type="primary")
        st.dataframe(audience.head(8), hide_index=True)
