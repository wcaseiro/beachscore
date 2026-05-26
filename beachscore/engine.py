from copy import deepcopy
from datetime import datetime


POINTS = ["0", "15", "30", "40"]


def default_state(court_id="arena-1", court_name="Arena 01"):
    return {
        "court_id": court_id,
        "court": court_name,
        "match_id": None,
        "match_name": "Partida Principal",
        "team_a": "Dupla Azul",
        "team_b": "Dupla Vermelha",
        "server": "A",
        "side_change": False,
        "finished": False,
        "sets_to_win": 2,
        "no_ad": True,
        "score": {
            "A": {"points": 0, "games": 0, "sets": 0},
            "B": {"points": 0, "games": 0, "sets": 0},
        },
        "events": [],
    }


def snapshot(state):
    data = deepcopy(state)
    data["events"] = []
    return data


def public_state(state):
    data = deepcopy(state)
    data["score"]["A"]["label"] = point_label(state, "A")
    data["score"]["B"]["label"] = point_label(state, "B")
    return data


def point_label(state, team):
    points = state["score"][team]["points"]
    other = other_team(team)
    other_points = state["score"][other]["points"]

    if not state["no_ad"] and points >= 3 and other_points >= 3:
        if points == other_points:
            return "40"
        if points > other_points:
            return "VANT"
        return "40"

    if points >= 3:
        return "40"

    return POINTS[points]


def add_event(state, text):
    event = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "text": text,
    }
    state["events"].insert(0, event)
    state["events"] = state["events"][:8]
    return event


def add_point(state, team):
    if state["finished"]:
        return []

    team = normalize_team(team)
    messages = []
    state["score"][team]["points"] += 1

    other = other_team(team)
    points = state["score"][team]["points"]
    other_points = state["score"][other]["points"]

    if state["no_ad"]:
        if points >= 4:
            messages.extend(win_game(state, team))
    elif points >= 4 and points - other_points >= 2:
        messages.extend(win_game(state, team))

    messages.append(f"Ponto para {team_name(state, team)}")
    for message in messages:
        add_event(state, message)
    return messages


def win_game(state, team):
    other = other_team(team)
    messages = []
    state["score"][team]["games"] += 1
    reset_points(state)
    switch_server(state)
    check_side_change(state)

    messages.append(f"Game para {team_name(state, team)}")

    if (
        state["score"][team]["games"] >= 6
        and state["score"][team]["games"] - state["score"][other]["games"] >= 2
    ):
        messages.extend(win_set(state, team))

    return messages


def win_set(state, team):
    messages = [f"Set para {team_name(state, team)}"]
    state["score"][team]["sets"] += 1
    state["score"]["A"]["games"] = 0
    state["score"]["B"]["games"] = 0
    reset_points(state)
    state["side_change"] = False

    if state["score"][team]["sets"] >= state["sets_to_win"]:
        state["finished"] = True
        messages.append("Fim de partida")

    return messages


def reset_points(state):
    state["score"]["A"]["points"] = 0
    state["score"]["B"]["points"] = 0


def check_side_change(state):
    total_games = state["score"]["A"]["games"] + state["score"]["B"]["games"]
    state["side_change"] = total_games > 0 and total_games % 2 == 1


def switch_server(state):
    state["server"] = other_team(state["server"])


def reset_match(state):
    state["finished"] = False
    state["side_change"] = False
    state["server"] = "A"
    state["score"]["A"] = {"points": 0, "games": 0, "sets": 0}
    state["score"]["B"] = {"points": 0, "games": 0, "sets": 0}
    state["events"] = []
    add_event(state, "Nova partida iniciada")


def update_config(state, data):
    if "arena" in data and data["arena"]:
        data = {**data, "court": data["arena"]}

    for key in ("court", "match_name", "team_a", "team_b"):
        if key in data and data[key]:
            state[key] = data[key]

    server = data.get("server")
    if server:
        state["server"] = normalize_team(server)

    for key in ("sets_to_win",):
        if key in data:
            state[key] = int(data[key])

    if "no_ad" in data:
        state["no_ad"] = bool(data["no_ad"])

    add_event(state, "Configuracao da partida atualizada")


def toggle_side_change(state):
    state["side_change"] = not state["side_change"]
    add_event(state, "Virada de campo alterada manualmente")


def normalize_team(team):
    team = str(team).upper()
    if team not in ("A", "B"):
        raise ValueError("team must be A or B")
    return team


def other_team(team):
    return "B" if normalize_team(team) == "A" else "A"


def team_name(state, team):
    return state["team_a"] if normalize_team(team) == "A" else state["team_b"]
