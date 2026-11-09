# IMPERIUM | Ikariam Alliance Operations Center

A free Python/Streamlit starter application for alliance geography and player clustering.

## Features

- Shared member password and separate shared administrator password
- Admin-only CSV/XLSX upload
- Supports raw city data (`playerName`, `cityName`, `x`, `y`) and player-center data (`playerName`, `x`, `y`, optional `city_count`)
- Aggregates multiple city coordinates into one player center using the median
- Balanced geographical clustering with configurable minimum and maximum players per cluster
- Interactive Plotly map, cluster roster, player search
- Exports `playerName,cluster` CSV and city-level assignments
- No database

## 1. Run locally

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` using the template below, then run:

```bash
streamlit run app.py
```

## 2. Configure passwords

Generate SHA-256 hashes:

```bash
python -c "import hashlib,getpass; print(hashlib.sha256(getpass.getpass('Password: ').encode()).hexdigest())"
```

Run it twice, once for the member password and once for the administrator password.

Create `.streamlit/secrets.toml`:

```toml
[auth]
member_password_hash = "PASTE_MEMBER_HASH_HERE"
admin_password_hash = "PASTE_ADMIN_HASH_HERE"
```

Never commit the real `secrets.toml` file to GitHub. It is ignored by `.gitignore`.

The app has two shared passwords:
- Member password: view-only access
- Admin password: upload and configure data

## 3. Input data

Minimum required columns:

| Column | Meaning |
|---|---|
| `playerName` | Exact alliance player name |
| `x` | Ikariam X coordinate |
| `y` | Ikariam Y coordinate |

For city-level data, also include `cityName`. Multiple cities belonging to one player are collapsed into one representative player point using median X and median Y.

For precomputed player-center data, one row per player is ideal. `city_count` is optional.

Example:

```csv
playerName,cityName,x,y
Caesar,Roma,42,51
Caesar,Mediolanum,44,53
Augustus,Alexandria,48,49
```

## 4. Clustering behavior

The application uses K-Means to initialize geographical centers, then a capacity-constrained assignment step (SciPy's linear sum assignment) to keep cluster sizes balanced.

Default bounds are 4–5 players per cluster. If the total player count cannot be divided within the selected bounds, the app explains the issue and asks you to adjust the limits.

Each player is assigned to exactly one cluster. All of their cities inherit that cluster in the city-level export.

Coordinates are treated as a flat Ikariam world coordinate plane, not latitude/longitude.

## 5. Free hosting on Streamlit Community Cloud

1. Create a free GitHub account and a new repository.
2. Upload the project files.
3. Open Streamlit Community Cloud and connect the GitHub repository.
4. Deploy `app.py`.
5. In the app's deployment settings, add the same TOML secrets under **Secrets**.
6. Share the resulting `*.streamlit.app` URL and the member password with alliance members.

Official links:
- https://streamlit.io/cloud
- https://docs.streamlit.io/deploy/streamlit-community-cloud

## 6. Important data-sharing limitation

This starter uses no database. An admin upload is held in that admin's Streamlit session only. It is not automatically shared with other members and may disappear when the session restarts.

To publish a dataset for all members, replace `data/alliance.csv` in the GitHub repository with the current alliance dataset and redeploy/reboot the app. The app loads that file as the shared default.

If you later want admins to upload once and have every member immediately see the new data without a redeploy, the next step is a small persistent storage service. Some providers have free tiers, but that would be a different architecture.

## Security note

This is a lightweight shared-password gate suitable for a low-risk private alliance dashboard. It is not enterprise authentication. Anyone who knows the member password can view the app, and anyone who knows the admin password can upload data. Use strong, distinct passwords, keep secrets out of GitHub, and do not upload personal or sensitive information.
