import streamlit as st
import json
import os
import pandas as pd

# ---------------------- UTILS ----------------------
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# ------------------ APP SETUP ----------------------
PLAYER_FILE = "players.json"
TEAM_FILE = "teams.json"
MATCH_FILE = "matches.json"

if "players" not in st.session_state:
    st.session_state.players = load_data(PLAYER_FILE)
if "teams" not in st.session_state:
    st.session_state.teams = load_data(TEAM_FILE)
if "matches" not in st.session_state:
    st.session_state.matches = load_data(MATCH_FILE)

st.set_page_config(page_title="CricManager", layout="wide")
st.title("🏏 CricManager - Cricket Management & Scoring")

menu = st.sidebar.radio("Menu", ["Player Manager", "Team Manager", "Score Match", "Match History", "Leaderboard", "Export Stats"])

# ---------------- PLAYER MANAGER -------------------
if menu == "Player Manager":
    st.header("👤 Player Manager")
    name = st.text_input("Player Name")
    age = st.number_input("Age", min_value=10, max_value=50, step=1)
    role = st.selectbox("Role", ["Batsman", "Bowler", "All-rounder", "Wicketkeeper"])

    if st.button("Add Player"):
        player = {"name": name, "age": age, "role": role, "runs": 0, "wickets": 0, "matches": 0}
        st.session_state.players.append(player)
        save_data(PLAYER_FILE, st.session_state.players)
        st.success(f"Added player {name}")

    st.subheader("All Players")
    for p in st.session_state.players:
        st.markdown(f"**{p['name']}** | Age: {p['age']} | Role: {p['role']} | Matches: {p['matches']} | Runs: {p['runs']} | Wickets: {p['wickets']}")

# ---------------- TEAM MANAGER ---------------------
elif menu == "Team Manager":
    st.header("🧑‍🤝‍🧑 Team Manager")
    team_name = st.text_input("Team Name")
    selected_players = st.multiselect("Select Players", [p["name"] for p in st.session_state.players])

    if st.button("Create Team"):
        team = {"name": team_name, "players": selected_players}
        st.session_state.teams.append(team)
        save_data(TEAM_FILE, st.session_state.teams)
        st.success(f"Team {team_name} created")

    st.subheader("All Teams")
    for t in st.session_state.teams:
        st.markdown(f"**{t['name']}** - {', '.join(t['players'])}")

# ---------------- MATCH SCORING --------------------
elif menu == "Score Match":
    st.header("🎯 Score a Match")
    team1 = st.selectbox("Select Team 1", [t["name"] for t in st.session_state.teams])
    team2 = st.selectbox("Select Team 2", [t["name"] for t in st.session_state.teams if t["name"] != team1])
    overs = st.number_input("Overs", min_value=1, max_value=50, step=1)

    players = [p["name"] for p in st.session_state.players]
    ball_by_ball = []

    if st.button("Start Match"):
        st.session_state.current_match = {
            "team1": team1,
            "team2": team2,
            "overs": overs,
            "team1_balls": [],
            "team2_balls": [],
            "team1_players": {},
            "team2_players": {},
            "extras": {"wide": 0, "no_ball": 0, "byes": 0, "leg_byes": 0},
            "status": "scoring",
            "current_over": 0,
            "balls_in_over": 0,
            "striker": None,
            "non_striker": None,
            "current_bowler": None,
        }

    if "current_match" in st.session_state and st.session_state.current_match.get("status") == "scoring":
        st.subheader(f"Ball-by-Ball Scoring")
        
        col1, col2 = st.columns(2)
        with col1:
            batting_team = st.radio("Batting Team", [st.session_state.current_match['team1'], st.session_state.current_match['team2']], index=0)
            batter = st.selectbox("Batsman (Striker)", players, index=0)
            run = st.selectbox("Runs Scored on this Ball", [0, 1, 2, 3, 4, 6, 'W', 'Wide', 'No Ball', 'Bye', 'Leg Bye'])
        
        with col2:
            bowler = st.selectbox("Bowler", players)
            is_wicket = st.checkbox("Wicket?")

        if st.button("Add Ball"):
            if run == 'W':
                run_val = -1
            elif run == 'Wide':
                run_val = 1  # Wide adds one extra run
                st.session_state.current_match["extras"]["wide"] += 1
            elif run == 'No Ball':
                run_val = 1  # No ball adds one extra run
                st.session_state.current_match["extras"]["no_ball"] += 1
            elif run == 'Bye':
                run_val = 0  # Bye adds runs but no change in batsman score
                st.session_state.current_match["extras"]["byes"] += 1
            elif run == 'Leg Bye':
                run_val = 0  # Leg bye adds runs but no change in batsman score
                st.session_state.current_match["extras"]["leg_byes"] += 1
            else:
                run_val = int(run)

            # Update batsman (Striker) runs
            ball_data = {
                "batter": batter, "bowler": bowler, "run": run_val,
                "ball_type": run, "wicket": is_wicket
            }

            # Update striker and non-striker
            if batting_team == st.session_state.current_match['team1']:
                st.session_state.current_match['team1_balls'].append(ball_data)
                if batter not in st.session_state.current_match['team1_players']:
                    st.session_state.current_match['team1_players'][batter] = 0
                if bowler not in st.session_state.current_match['team2_players']:
                    st.session_state.current_match['team2_players'][bowler] = 0
                if run_val >= 0:
                    st.session_state.current_match['team1_players'][batter] += run_val
                if is_wicket:
                    # Update player stats for dismissal
                    st.session_state.current_match['team1_players'][batter] = 'W'

            else:
                st.session_state.current_match['team2_balls'].append(ball_data)
                if batter not in st.session_state.current_match['team2_players']:
                    st.session_state.current_match['team2_players'][batter] = 0
                if bowler not in st.session_state.current_match['team1_players']:
                    st.session_state.current_match['team1_players'][bowler] = 0
                if run_val >= 0:
                    st.session_state.current_match['team2_players'][batter] += run_val
                if is_wicket:
                    # Update player stats for dismissal
                    st.session_state.current_match['team2_players'][batter] = 'W'

            # Change striker and non-striker after each ball
            if run_val != 0 and not is_wicket:
                st.session_state.current_match['striker'], st.session_state.current_match['non_striker'] = st.session_state.current_match['non_striker'], st.session_state.current_match['striker']

            # Ball count and over progress
            st.session_state.current_match["balls_in_over"] += 1
            if st.session_state.current_match["balls_in_over"] == 6:
                st.session_state.current_match["current_over"] += 1
                st.session_state.current_match["balls_in_over"] = 0

        if st.button("Submit Match Result"):
            team1_score = sum([r['run'] for r in st.session_state.current_match['team1_balls'] if r['run'] >= 0])
            team2_score = sum([r['run'] for r in st.session_state.current_match['team2_balls'] if r['run'] >= 0])
            st.session_state.current_match["team1_score"] = team1_score
            st.session_state.current_match["team2_score"] = team2_score
            st.session_state.current_match["status"] = "completed"

            # Update player stats
            for player in st.session_state.players:
                name = player["name"]
                if name in st.session_state.current_match["team1_players"] or name in st.session_state.current_match["team2_players"]:
                    player["matches"] += 1
                    player["runs"] += st.session_state.current_match["team1_players"].get(name, 0)
                    player["runs"] += st.session_state.current_match["team2_players"].get(name, 0)
                    player["wickets"] += st.session_state.current_match["team1_players"].get(name, 0) if name in st.session_state.current_match["team2_players"] else 0
                    player["wickets"] += st.session_state.current_match["team2_players"].get(name, 0) if name in st.session_state.current_match["team1_players"] else 0

            st.session_state.matches.append(st.session_state.current_match)
            save_data(MATCH_FILE, st.session_state.matches)
            save_data(PLAYER_FILE, st.session_state.players)
            del st.session_state.current_match
            st.success("Match result saved successfully!")

# ---------------- MATCH HISTORY --------------------
elif menu == "Match History":
    st.header("📜 Match History")
    for m in st.session_state.matches:
        result = "Draw"
        if m["team1_score"] > m["team2_score"]:
            result = f"{m['team1']} won"
        elif m["team2_score"] > m["team1_score"]:
            result = f"{m['team2']} won"
        st.markdown(f"### 🏁 {m['team1']} vs {m['team2']}")
        st.markdown(f"**Overs:** {m['overs']} | **Score:** {m['team1_score']} - {m['team2_score']} | **Result:** {result}")

        with st.expander("Match Summary"):
            st.subheader(f"{m['team1']} Batting")
            for player, score in m.get("team1_players", {}).items():
                st.markdown(f"- {player}: {score if score >= 0 else 0} runs")
            st.subheader(f"{m['team2']} Batting")
            for player, score in m.get("team2_players", {}).items():
                st.markdown(f"- {player}: {score if score >= 0 else 0} runs")

# ---------------- LEADERBOARD ----------------------
elif menu == "Leaderboard":
    st.header("🏅 Leaderboard")
    sorted_players = sorted(st.session_state.players, key=lambda x: (x["runs"], x["wickets"]), reverse=True)
    for i, p in enumerate(sorted_players, 1):
        st.markdown(f"**{i}. {p['name']}** - Runs: {p['runs']}, Wickets: {p['wickets']}, Matches: {p['matches']}")

# ---------------- EXPORT STATS ---------------------
elif menu == "Export Stats":
    st.header("🗃 Export Stats")
    df_players = pd.DataFrame(st.session_state.players)
    st.dataframe(df_players)
    csv = df_players.to_csv(index=False).encode('utf-8')
    st.download_button("Download Player Stats as CSV", csv, "players.csv")
