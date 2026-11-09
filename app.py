
import streamlit as st
import pandas as pd

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="RoA Command Centre",
    page_icon="🏛️",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🏛️ RoA")
st.subheader("Alliance Command Centre")
st.divider()

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("data/alliance.csv", keep_default_na=False)

    # Clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    # Remove empty rows
    df = df.dropna(subset=["playerName", "cluster"])

    df["playerName"] = df["playerName"].astype(str).str.strip()
    df["cluster"] = df["cluster"].astype(str).str.strip()

    df = df[
        (df["playerName"] != "") &
        (df["cluster"] != "")
    ]

    return df


df = load_data()

# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Players",
    df["playerName"].nunique()
)

col2.metric(
    "Clusters",
    df["cluster"].nunique()
)

col3.metric(
    "Total Assignments",
    len(df)
)

st.divider()

# --------------------------------------------------
# CLUSTER OVERVIEW
# --------------------------------------------------

st.subheader("Cluster Overview")

cluster_counts = (
    df.groupby("cluster")
    .size()
    .reset_index(name="Players")
    .sort_values("cluster")
)

st.dataframe(
    cluster_counts,
    use_container_width=True,
    hide_index=True
)

st.divider()

# --------------------------------------------------
# PLAYER SEARCH
# --------------------------------------------------

st.subheader("Player Search")

search = st.text_input(
    "Search for a player",
    placeholder="Enter player name..."
)

if search:
    results = df[
        df["playerName"].str.contains(
            search,
            case=False,
            na=False
        )
    ]

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# CLUSTER FILTER
# --------------------------------------------------

st.subheader("Cluster Members")

clusters = sorted(df["cluster"].unique())

selected_cluster = st.selectbox(
    "Select cluster",
    ["All clusters"] + clusters
)

if selected_cluster == "All clusters":
    filtered_df = df
else:
    filtered_df = df[
        df["cluster"] == selected_cluster
    ]

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)
