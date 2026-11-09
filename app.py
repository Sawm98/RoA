
import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="RoA Command Centre",
    page_icon="🏛️",
    layout="wide"
)

# ==================================================
# HEADER
# ==================================================

st.title("🏛️ RoA")
st.subheader("Alliance Command Centre")

st.divider()

# ==================================================
# LOAD AND PROCESS DATA
# ==================================================

@st.cache_data
def load_data():

    # Load cluster assignments
    alliance = pd.read_csv(
        "data/alliance.csv",
        keep_default_na=False
    )

    # Load player coordinates
    centers = pd.read_csv(
        "data/player_centers.csv",
        keep_default_na=False
    )

    # Clean column names
    for frame in [alliance, centers]:
        frame.columns = (
            frame.columns
            .str.strip()
            .str.replace("\ufeff", "", regex=False)
        )

    # Validate required columns
    required_alliance = {"playerName", "cluster"}
    required_centers = {"playerName", "x", "y", "city_count"}

    if not required_alliance.issubset(alliance.columns):
        raise ValueError("alliance.csv must contain playerName and cluster")

    if not required_centers.issubset(centers.columns):
        raise ValueError("player_centers.csv must contain playerName, x, y and city_count")

    # Clean player names
    alliance["playerName"] = alliance["playerName"].astype(str).str.strip()
    centers["playerName"] = centers["playerName"].astype(str).str.strip()

    # Remove genuinely empty rows
    alliance = alliance[
        (alliance["playerName"] != "") &
        (alliance["cluster"].astype(str).str.strip() != "")
    ]

    centers = centers[centers["playerName"] != ""]

    # Convert coordinate data to numbers
    for column in ["x", "y", "city_count"]:
        centers[column] = pd.to_numeric(
            centers[column],
            errors="coerce"
        )

    # Remove duplicate player centers
    centers = centers.drop_duplicates(
        subset=["playerName"]
    )

    # Combine datasets
    df = alliance.merge(
        centers,
        on="playerName",
        how="left",
        validate="many_to_one"
    )

    return df


df = load_data()

# ==================================================
# STATISTICS
# ==================================================

st.subheader("Alliance Statistics")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Players",
    df["playerName"].nunique()
)

col2.metric(
    "Clusters",
    df["cluster"].nunique()
)

col3.metric(
    "Total Cities",
    int(df["city_count"].sum())
)

col4.metric(
    "Players with Coordinates",
    df.loc[df["x"].notna() & df["y"].notna(), "playerName"].nunique()
)

st.divider()

# ==================================================
# CLUSTER OVERVIEW
# ==================================================

st.subheader("Cluster Overview")

cluster_counts = (
    df.groupby("cluster")
    .agg(
        Players=("playerName", "nunique"),
        Cities=("city_count", "sum")
    )
    .reset_index()
    .sort_values("cluster")
)

st.dataframe(
    cluster_counts,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# DATA QUALITY
# ==================================================

missing_coordinates = df[
    df["x"].isna() | df["y"].isna()
]["playerName"].nunique()

if missing_coordinates > 0:
    st.warning(
        f"{missing_coordinates} players have no matching coordinates."
    )

st.divider()

# ==================================================
# PLAYER SEARCH
# ==================================================

st.subheader("Player Search")

search = st.text_input(
    "Search player",
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

# ==================================================
# CLUSTER FILTER
# ==================================================

st.subheader("Cluster Members")

clusters = sorted(df["cluster"].unique())

selected_cluster = st.selectbox(
    "Select cluster",
    ["All clusters"] + list(clusters)
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

# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "RoA Command Centre | Alliance Intelligence"
)
