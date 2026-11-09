import hashlib
import hmac
import io
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans

APP_DIR = Path(__file__).parent
DEFAULT_DATA = APP_DIR / "data" / "alliance.csv"

st.set_page_config(
    page_title="IMPERIUM | Alliance Operations Center",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Authentication ----------
def password_matches(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(candidate, stored_hash.strip().lower())


def login_screen():
    st.markdown(
        """
        <div style="padding: 2rem 0 1rem 0; text-align:center;">
          <div style="font-size:3rem;">🏛️</div>
          <h1 style="letter-spacing:.18em; margin-bottom:0;">IMPERIUM</h1>
          <p style="color:#9aa6b2; letter-spacing:.12em;">ALLIANCE OPERATIONS CENTER</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        password = st.text_input("Alliance password", type="password")
        submitted = st.form_submit_button("Enter operations center", use_container_width=True)
    if submitted:
        try:
            admin_hash = st.secrets["auth"]["admin_password_hash"]
            member_hash = st.secrets["auth"]["member_password_hash"]
        except Exception:
            st.error("Authentication is not configured. Add the passwords to Streamlit secrets.")
            return

        if password_matches(password, admin_hash):
            st.session_state["authenticated"] = True
            st.session_state["role"] = "admin"
            st.rerun()
        elif password_matches(password, member_hash):
            st.session_state["authenticated"] = True
            st.session_state["role"] = "member"
            st.rerun()
        else:
            st.error("Incorrect password.")


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
    st.stop()

# ---------- Data preparation ----------
def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Please upload a CSV or Excel file.")


def clean_and_prepare(raw: pd.DataFrame):
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    required = {"playerName", "x", "y"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "Missing required column(s): " + ", ".join(sorted(missing))
            + ". Required columns are playerName, x and y."
        )

    df = df.dropna(subset=["playerName", "x", "y"]).copy()
    df["playerName"] = df["playerName"].astype(str).str.strip()
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df = df.dropna(subset=["x", "y"])
    df = df[df["playerName"] != ""]
    if df.empty:
        raise ValueError("The uploaded file contains no usable player coordinates.")

    # Raw city-level data: collapse all cities to one representative point per player.
    # Precomputed player_centers data: duplicate rows are also safely aggregated.
    aggregation = {"x": "median", "y": "median"}
    if "city_count" in df.columns:
        aggregation["city_count"] = "max"
    centers = df.groupby("playerName", as_index=False).agg(aggregation)

    if "city_count" not in centers.columns:
        counts = df.groupby("playerName").size().rename("city_count").reset_index()
        centers = centers.merge(counts, on="playerName", how="left")

    centers["city_count"] = centers["city_count"].fillna(1).astype(int)
    return df, centers


def balanced_kmeans(points: pd.DataFrame, min_size: int, max_size: int):
    n = len(points)
    if n < min_size:
        raise ValueError(
            f"There are {n} players. At least {min_size} are needed for one cluster "
            f"with the selected minimum size."
        )

    k_min = math.ceil(n / max_size)
    k_max = n // min_size
    if k_min > k_max:
        raise ValueError(
            f"{n} players cannot be divided into clusters of {min_size}–{max_size}. "
            "Adjust the size limits."
        )

    target = (min_size + max_size) / 2
    k = max(k_min, min(k_max, round(n / target)))

    coords = points[["x", "y"]].to_numpy(dtype=float)
    initial = KMeans(n_clusters=k, n_init=20, random_state=42).fit(coords)
    centers = initial.cluster_centers_

    # Distribute capacity as evenly as possible, never exceeding the selected bounds.
    capacities = [n // k] * k
    for i in range(n % k):
        capacities[i] += 1

    slots = [cluster_id for cluster_id, capacity in enumerate(capacities) for _ in range(capacity)]

    # Repeatedly assign each player to a cluster slot using the globally minimum
    # total squared distance, then recalculate the cluster centers.
    for _ in range(40):
        costs = ((coords[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        slot_costs = costs[:, slots]
        row_ind, col_ind = linear_sum_assignment(slot_costs)
        labels = [None] * n
        for row, col in zip(row_ind, col_ind):
            labels[row] = slots[col]
        labels = pd.Series(labels, dtype=int).to_numpy()

        new_centers = centers.copy()
        for cluster_id in range(k):
            members = coords[labels == cluster_id]
            if len(members):
                new_centers[cluster_id] = members.mean(axis=0)

        if (new_centers == centers).all():
            break
        centers = new_centers

    # Give cluster numbers a predictable left-to-right ordering on the map.
    order = sorted(range(k), key=lambda cid: (centers[cid][0], centers[cid][1]))
    remap = {old: new + 1 for new, old in enumerate(order)}
    final_labels = [remap[int(label)] for label in labels]

    result = points[["playerName", "x", "y", "city_count"]].copy()
    result["cluster"] = final_labels
    return result.sort_values(["cluster", "playerName"]).reset_index(drop=True)


# ---------- Header and sidebar ----------
with st.sidebar:
    st.markdown("## 🏛️ IMPERIUM")
    st.caption("ALLIANCE OPERATIONS CENTER")
    role = st.session_state.get("role", "member")
    st.success("Administrator access" if role == "admin" else "Member access")
    if st.button("Log out", use_container_width=True):
        for key in ("authenticated", "role", "active_data", "active_filename", "cluster_result"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.markdown("**Navigation**")
    st.caption("Alliance overview · Territory · Clusters · Data export")

st.markdown(
    """
    <div style="padding:.3rem 0 1rem 0;">
      <span style="font-size:.85rem; letter-spacing:.16em; color:#9aa6b2;">IMPERIUM / COMMAND</span>
      <h1 style="margin:.15rem 0;">Alliance Operations Center</h1>
      <p style="color:#9aa6b2; margin:0;">Geographical organization and operational overview</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Dataset selection ----------
if role == "admin":
    with st.expander("⬆️ Upload alliance data", expanded=("active_data" not in st.session_state)):
        uploaded = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx", "xls"],
            help="Required columns: playerName, x, y. Optional: cityName and city_count.",
        )
        if uploaded is not None:
            if st.button("Use uploaded dataset", type="primary"):
                try:
                    st.session_state["active_data"] = read_uploaded_file(uploaded)
                    st.session_state["active_filename"] = uploaded.name
                    st.session_state.pop("cluster_result", None)
                    st.success("Dataset loaded for this session.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

if "active_data" in st.session_state:
    raw_data = st.session_state["active_data"].copy()
    data_label = st.session_state.get("active_filename", "Uploaded dataset")
elif DEFAULT_DATA.exists():
    try:
        raw_data = pd.read_csv(DEFAULT_DATA)
        data_label = "Shared repository dataset"
    except Exception:
        raw_data = pd.DataFrame()
        data_label = "No usable dataset"
else:
    raw_data = pd.DataFrame()
    data_label = "No dataset loaded"

if raw_data.empty:
    st.info(
        "No alliance dataset is loaded yet. An administrator can upload a CSV/XLSX above. "
        "For a dataset visible to every member, place the published CSV at data/alliance.csv "
        "in the application repository."
    )
    st.stop()

try:
    city_data, player_centers = clean_and_prepare(raw_data)
except Exception as exc:
    st.error(f"Could not process dataset: {exc}")
    st.stop()

# ---------- Clustering controls ----------
if role == "admin":
    with st.sidebar:
        st.divider()
        st.markdown("### Cluster settings")
        min_size = st.number_input("Minimum players", min_value=2, max_value=50, value=4, step=1)
        max_size = st.number_input("Maximum players", min_value=int(min_size), max_value=60, value=max(5, int(min_size)), step=1)
        run_clusters = st.button("Generate clusters", type="primary", use_container_width=True)
else:
    # Members see the published clustering defaults; only administrators can
    # change the cluster-size rules and regenerate assignments.
    min_size, max_size, run_clusters = 4, 5, False

if run_clusters or "cluster_result" not in st.session_state:
    try:
        st.session_state["cluster_result"] = balanced_kmeans(
            player_centers, int(min_size), int(max_size)
        )
        st.session_state["cluster_settings"] = (int(min_size), int(max_size))
    except Exception as exc:
        st.error(str(exc))
        st.stop()

result = st.session_state["cluster_result"].copy()
if len(result) != len(player_centers):
    st.warning("The dataset has changed. Generate clusters again.")
    st.stop()

# ---------- Dashboard ----------
cluster_count = result["cluster"].nunique()
total_players = result["playerName"].nunique()
total_cities = int(result["city_count"].sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Players", f"{total_players:,}")
m2.metric("Clusters", f"{cluster_count:,}")
m3.metric("Cities", f"{total_cities:,}")
m4.metric("Players / cluster", f"{total_players / cluster_count:.1f}" if cluster_count else "0")

st.caption(f"Dataset: **{data_label}** · One player is assigned to exactly one cluster.")

left, right = st.columns([2.2, 1])
with left:
    st.subheader("Territory map")
    fig = px.scatter(
        result,
        x="x",
        y="y",
        color=result["cluster"].astype(str),
        hover_name="playerName",
        hover_data={"city_count": True, "x": True, "y": True, "cluster": False},
        labels={"x": "X coordinate", "y": "Y coordinate", "color": "Cluster", "city_count": "Cities"},
        template="plotly_dark",
        height=620,
    )
    fig.update_traces(marker=dict(size=11, opacity=0.88, line=dict(width=0.7, color="#111827")))
    fig.update_layout(
        legend_title_text="Cluster",
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Cluster roster")
    summary = (
        result.groupby("cluster")
        .agg(players=("playerName", "count"), cities=("city_count", "sum"),
             center_x=("x", "mean"), center_y=("y", "mean"))
        .reset_index()
    )
    for _, row in summary.iterrows():
        with st.container(border=True):
            st.markdown(f"**Cluster {int(row['cluster']):02d}**")
            st.metric("Players", int(row["players"]))
            st.caption(
                f"{int(row['cities'])} cities · Center "
                f"({row['center_x']:.1f}, {row['center_y']:.1f})"
            )

st.divider()
st.subheader("Player assignments")
search = st.text_input("Search player")
visible = result
if search.strip():
    visible = visible[visible["playerName"].str.contains(search.strip(), case=False, na=False)]
st.dataframe(
    visible[["playerName", "cluster", "city_count", "x", "y"]],
    use_container_width=True,
    hide_index=True,
)

# ---------- Downloads ----------
st.subheader("Export")
player_export = result[["playerName", "cluster"]].sort_values(["cluster", "playerName"])
csv_bytes = player_export.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ Download playerName, cluster CSV",
    data=csv_bytes,
    file_name="ikariam_player_clusters.csv",
    mime="text/csv",
    type="primary",
)

city_export = city_data.merge(
    result[["playerName", "cluster"]], on="playerName", how="left"
)
city_csv = city_export.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ Download city-level data with clusters",
    data=city_csv,
    file_name="ikariam_city_assignments.csv",
    mime="text/csv",
)

if role == "admin":
    st.caption(
        "Publishing note: uploads are private to the current session. To make a new dataset "
        "the shared default for all members, replace data/alliance.csv in the GitHub repository."
    )
