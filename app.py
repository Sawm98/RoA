
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
# DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #101318;
    color: #e8e3d5;
}

h1, h2, h3 {
    color: #d6b56d !important;
    font-family: Georgia, serif;
}

[data-testid="stMetric"] {
    background-color: #1c222b;
    border: 1px solid #39332a;
    padding: 20px;
    border-radius: 8px;
}

[data-testid="stMetricValue"] {
    color: #d6b56d;
}

[data-testid="stMetricLabel"] {
    color: #b8b8b8;
}

hr {
    border-color: #39332a;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():

    # Load alliance roster
    alliance = pd.read_csv(
        "data/alliance.csv",
        keep_default_na=False
    )

    # Load player coordinates and city counts
    centers = pd.read_csv(
        "data/player_centers.csv",
        keep_default_na=False
    )

    # Clean column names
    alliance.columns = (
        alliance.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    centers.columns = (
        centers.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    # Clean player names
    alliance["playerName"] = alliance["playerName"].astype(str).str.strip()
    centers["playerName"] = centers["playerName"].astype(str).str.strip()

    # Remove empty player names
    alliance = alliance[alliance["playerName"] != ""]
    centers = centers[centers["playerName"] != ""]

    # Ensure cluster values are strings
    alliance["cluster"] = alliance["cluster"].astype(str).str.strip()

    # Convert numerical columns
    centers["x"] = pd.to_numeric(centers["x"], errors="coerce")
    centers["y"] = pd.to_numeric(centers["y"], errors="coerce")
    centers["city_count"] = pd.to_numeric(
        centers["city_count"],
        errors="coerce"
    )

    # One coordinate record per player
    centers = centers.drop_duplicates(
        subset=["playerName"]
    )

    # Combine alliance roster and player information
    df = alliance.merge(
        centers,
        on="playerName",
        how="left",
        validate="many_to_one"
    )

    return df


df = load_data()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🏛️ RoA Command Centre")

st.caption(
    "Alliance intelligence • Player organisation • Strategic overview"
)

st.divider()


# --------------------------------------------------
# OVERVIEW STATISTICS
# --------------------------------------------------

total_players = df["playerName"].nunique()

total_clusters = df["cluster"].nunique()

total_cities = int(df["city_count"].sum(skipna=True))

players_with_coordinates = df["x"].notna().sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Alliance members", total_players)
col2.metric("Clusters", total_clusters)
col3.metric("Total cities", total_cities)
col4.metric("Players with data", players_with_coordinates)


st.divider()


# --------------------------------------------------
# CLUSTER OVERVIEW
# --------------------------------------------------

st.header("Cluster overview")

cluster_summary = (
    df.groupby("cluster")
    .agg(
        Members=("playerName", "nunique"),
        Cities=("city_count", "sum")
    )
    .reset_index()
    .sort_values("cluster")
)

cluster_summary.columns = ["Cluster", "Members", "Cities"]

st.dataframe(
    cluster_summary,
    use_container_width=True,
    hide_index=True
)


st.divider()


# --------------------------------------------------
# PLAYER SEARCH
# --------------------------------------------------

st.header("Player search")

search = st.text_input(
    "Search for a player",
    placeholder="Enter player name..."
)

if search:

    search_results = df[
        df["playerName"].str.contains(
            search,
            case=False,
            na=False
        )
    ]

    if not search_results.empty:

        st.dataframe(
            search_results[
                ["playerName", "cluster", "x", "y", "city_count"]
            ].rename(columns={
                "playerName": "Player",
                "cluster": "Cluster",
                "x": "X",
                "y": "Y",
                "city_count": "Cities"
            }),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning("No player found.")


st.divider()


# --------------------------------------------------
# CLUSTER MEMBERS
# --------------------------------------------------

st.header("Cluster members")

available_clusters = sorted(
    df["cluster"].unique().tolist()
)

cluster_options = ["All clusters"] + available_clusters

selected_cluster = st.selectbox(
    "Select a cluster",
    cluster_options
)

if selected_cluster == "All clusters":

    cluster_df = df.copy()

else:

    cluster_df = df[
        df["cluster"] == selected_cluster
    ].copy()


cluster_df = cluster_df.sort_values("playerName")

st.caption(f"{cluster_df['playerName'].nunique()} members")

st.dataframe(
    cluster_df[
        ["playerName", "cluster", "x", "y", "city_count"]
    ].rename(columns={
        "playerName": "Player",
        "cluster": "Cluster",
        "x": "X",
        "y": "Y",
        "city_count": "Cities"
    }),
    use_container_width=True,
    hide_index=True
)


st.divider()


# --------------------------------------------------
# PLAYER INTELLIGENCE
# --------------------------------------------------

st.header("Player intelligence")

player_options = sorted(df["playerName"].unique().tolist())

selected_player = st.selectbox(
    "Select a player",
    player_options
)

player = df[
    df["playerName"] == selected_player
].iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric("Cluster", player["cluster"])

city_count = player["city_count"]
col2.metric(
    "Cities",
    int(city_count) if pd.notna(city_count) else "Unknown"
)

coordinates_available = (
    pd.notna(player["x"]) and pd.notna(player["y"])
)

if coordinates_available:
    coordinates = f"{player['x']}, {player['y']}"
else:
    coordinates = "Unknown"

col3.metric("Centre coordinates", coordinates)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "RoA Command Centre • Data maintained by the alliance"
)
