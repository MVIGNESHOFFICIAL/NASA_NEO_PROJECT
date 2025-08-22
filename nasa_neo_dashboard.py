# nasa_neo_dashboard_linear.py

import streamlit as st
import pandas as pd
import mysql.connector as db
from datetime import datetime

# Database connection

conn = db.connect(
    host="localhost",
    user="vignesh",
    password="1234",
    database="guvi_neo_project"
)

# Streamlit App Setup

st.set_page_config(page_title="NASA NEO Dashboard", layout="wide")

# Neon header and dataframe style

st.markdown("""
    <style>
    h1, h2, h3 {
        color: #66fcf1;
        text-shadow: 0 0 5px #66fcf1, 0 0 10px #66fcf1, 0 0 20px #66fcf1;
    }
    .dataframe thead th { background-color: #1f2833; color: #66fcf1; }
    .dataframe tbody tr th { vertical-align: top; }
    .dataframe tbody tr th:only-of-type { vertical-align: middle; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# NASA logo

st.markdown('<div class="logo-container"><img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="200"></div>', unsafe_allow_html=True)
st.title("🚀 NASA Near-Earth Objects Dashboard")

# Sidebar menu

menu = st.sidebar.radio("Select Mode", ["Queries", "Filters"])

# Guvi Queries

QUERIES = {
    "Q1. Count how many times each asteroid has approached Earth":
        "SELECT name, COUNT(*) AS approach_count FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY name",
    "Q2. Average velocity of each asteroid over multiple approaches":
        "SELECT name, AVG(relative_velocity_kmph) AS avg_velocity FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY name",
    "Q3. List top 10 fastest asteroids":
        "SELECT name, MAX(relative_velocity_kmph) AS max_velocity FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id GROUP BY name ORDER BY max_velocity DESC LIMIT 10",
    "Q4. Find potentially hazardous asteroids that have approached Earth more than 3 times":
        "SELECT name, COUNT(*) AS approach_count FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE a.is_potentially_hazardous_asteroid=1 GROUP BY name HAVING COUNT(*) > 3",
    "Q5. Find the month with the most asteroid approaches":
        "SELECT DATE_FORMAT(close_approach_date,'%Y-%m') AS month, COUNT(*) AS total_approaches FROM close_approach GROUP BY month ORDER BY total_approaches DESC LIMIT 1",
    "Q6. Get the asteroid with the fastest ever approach speed":
        "SELECT name, relative_velocity_kmph FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY relative_velocity_kmph DESC LIMIT 1",
    "Q7. Sort asteroids by maximum estimated diameter (descending)":
        "SELECT name, estimated_diameter_max_km FROM asteroids ORDER BY estimated_diameter_max_km DESC",
    "Q8. An asteroid whose closest approach is getting nearer over time":
        "SELECT name, close_approach_date, miss_distance_lunar AS miss_distance_ld FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY name, close_approach_date ASC, miss_distance_lunar ASC",
    "Q9. Display the name of each asteroid along with the date and miss distance of its closest approach to Earth":
        "SELECT name, close_approach_date, miss_distance_lunar AS miss_distance_ld FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id ORDER BY miss_distance_lunar ASC",
    "Q10. List names of asteroids that approached Earth with velocity > 50,000 km/h":
        "SELECT name, relative_velocity_kmph FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE relative_velocity_kmph > 50000",
    "Q11. Count how many approaches happened per month":
        "SELECT DATE_FORMAT(close_approach_date,'%Y-%m') AS month, COUNT(*) AS total_approaches FROM close_approach GROUP BY month ORDER BY month",
    "Q12. Find asteroid with the highest brightness (lowest magnitude value)":
        "SELECT name, absolute_magnitude_h FROM asteroids ORDER BY absolute_magnitude_h ASC LIMIT 1",
    "Q13. Get number of hazardous vs non-hazardous asteroids":
        "SELECT is_potentially_hazardous_asteroid, COUNT(*) AS count FROM asteroids GROUP BY is_potentially_hazardous_asteroid",
    "Q14. Find asteroids that passed closer than the Moon (<1 LD), along with their close approach date and distance":
        "SELECT name, close_approach_date, miss_distance_lunar AS miss_distance_ld FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE miss_distance_lunar < 1",
    "Q15. Find asteroids that came within 0.05 AU":
        "SELECT name, close_approach_date, astronomical AS miss_distance_au FROM asteroids a JOIN close_approach c ON a.id = c.neo_reference_id WHERE astronomical < 0.05"
}


                # Queries output Section

if menu == "Queries":
    st.subheader("Select a Query to Run")
    query_selection = st.selectbox("Choose a Query", list(QUERIES.keys()))
    if st.button("Run Query"):
        df = pd.read_sql(QUERIES[query_selection], conn)
        st.subheader(f"Results for: {query_selection}")
        st.dataframe(df)

                # Filters output Section

elif menu == "Filters":
    st.subheader("Filter Asteroid Data")

    # Single line date input
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Close Approach Start Date", datetime(2000,1,1))
    with col2:
        end_date = st.date_input("Close Approach End Date", datetime.today())

    # Sliders in two columns
    col3, col4 = st.columns(2)
    with col3:
        min_au, max_au = st.slider("Astronomical Units (AU)", 0.0, 10.0, (0.0, 1.0), 0.01)
        min_ld, max_ld = st.slider("Lunar Distance (LD)", 0.0, 1000.0, (0.0, 10.0), 0.01)
    with col4:
        min_vel, max_vel = st.slider("Relative Velocity (km/h)", 0.0, 100000.0, (0.0, 100000.0), 100.0)
        min_dia, max_dia = st.slider("Estimated Diameter (km)", 0.0, 50.0, (0.0, 50.0), 0.01)

    hazardous = st.selectbox("Hazardous?", ["All", "Yes", "No"])

    if st.button("Apply Filters"):
        sql_filter = f"""
            SELECT a.name, c.close_approach_date, c.astronomical, c.miss_distance_lunar,
                   c.relative_velocity_kmph, a.estimated_diameter_max_km,
                   a.is_potentially_hazardous_asteroid
            FROM asteroids a
            JOIN close_approach c ON a.id = c.neo_reference_id
            WHERE c.close_approach_date BETWEEN '{start_date}' AND '{end_date}'
            AND c.astronomical BETWEEN {min_au} AND {max_au}
            AND c.miss_distance_lunar BETWEEN {min_ld} AND {max_ld}
            AND c.relative_velocity_kmph BETWEEN {min_vel} AND {max_vel}
            AND a.estimated_diameter_max_km BETWEEN {min_dia} AND {max_dia}
        """
        if hazardous != "All":
            val = 1 if hazardous == "Yes" else 0
            sql_filter += f" AND a.is_potentially_hazardous_asteroid = {val}"

        df = pd.read_sql(sql_filter, conn)
        st.subheader("Filtered Results")
        st.dataframe(df)

# Close DB connection at the end

conn.close()
