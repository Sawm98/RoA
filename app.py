
import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(
    page_title="IMPERIUM Command Centre",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ IMPERIUM")
st.subheader("Alliance Command Centre")

st.divider()

# Load alliance data
@st.cache_data
def load_data():
    return pd.read_csv("data/alliance.csv")

df = load_data()

# Basic statistics
col1, col2, col3 = st.columns(3)

col1.metric("Players", df["playerName"].nunique())
col2.metric("Clusters", df["cluster"].nunique())
col3.metric("Alliance Members", len(df))

st.divider()

# Cluster selection
clusters = sorted(df["cluster"].unique())

selected_cluster = st.selectbox(
    "Select cluster",
    ["All clusters"] + list(clusters)
)

if selected_cluster != "All clusters":
    filtered_df = df[df["cluster"] == selected_cluster]
else:
    filtered_df = df

st.subheader("Alliance Members")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)
