from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from copy import deepcopy
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

POINTS = ["0", "15", "30", "40"]

state = {
    "court": "Quadra 1",
    "match_name": "Partida Demo",
    "team_a": "Dupla Azul",
    "team_b": "Dupla Vermelha",
    "server": "A",
    "side_change": False,
    "finished": False,
    "sets_to_win": 2,
    "no_ad": True,
    "score": {
        "A": {"points": 0, "games": 0, "sets": 0},
        "B": {"points": 0, "games": 0, "sets": 0}
    },
    "history": [],
    "events": []
}

undo_stack = []


def snapshot():
    s = deepcopy(state)
    s["history"] = []
    s["events"] = []
    return s


def point_label(team):
    points = state["score"][team]["points"]
    other = "B" if team == "A" else "A"
    other_points = state["score"][other]["points"]

    if not state["no_ad"]:
        if points >= 3 and other_points >= 3:
            if points == other_points:
                return "40"
            if points > other_points:
                return "VANT"
            return "40"

    if points >= 3:
        return "40"

    return POINTS[points]


def add_event(text):
    state["events"].insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "text": text
    })
    state["events"] = state["events"][:8]


def emit_state():
    socketio.emit("state", public_state())


def public_state():
    data = deepcopy(state)
    data["score"]["A"]["label"] = point_label("A")
    data["score"]["B"]["label"] = point_label("B")
    return data


def reset_points():
    state["score"]["A"]["points"] = 0
    state["score"]["B"]["points"] = 0


def check_side_change():
    total_games = state["score"]["A"]["games"] + state["score"]["B"]["games"]
    state["side_change"] = total_games > 0 and total_games % 2 == 1


def switch_server():
    state["server"] = "B" if state["server"] == "A" else "A"


def win_game(team):
    other = "B" if team == "A" else "A"
    state["score"][team]["games"] += 1
    reset_points()
    switch_server()
    check_side_change()

    add_event(f"Game para {state['team_a'] if team == 'A' else state['team_b']}")

    if state["score"][team]["games"] >= 6 and state["score"][team]["games"] - state["score"][other]["games"] >= 2:
        win_set(team)


def win_set(team):
    state["score"][team]["sets"] += 1
    state["score"]["A"]["games"] = 0
    state["score"]["B"]["games"] = 0
    reset_points()
    state["side_change"] = False

    add_event(f"Set para {state['team_a'] if team == 'A' else state['team_b']}")

    if state["score"][team]["sets"] >= state["sets_to_win"]:
        state["finished"] = True
        add_event(f"Fim de partida")


def add_point(team):
    if state["finished"]:
        return

    undo_stack.append(snapshot())

    other = "B" if team == "A" else "A"

    state["score"][team]["points"] += 1

    p = state["score"][team]["points"]
    op = state["score"][other]["points"]

    if state["no_ad"]:
        if p >= 4:
            win_game(team)
    else:
        if p >= 4 and p - op >= 2:
            win_game(team)

    add_event(f"Ponto para {state['team_a'] if team == 'A' else state['team_b']}")


def undo():
    if undo_stack:
        old = undo_stack.pop()
        for key in old:
            if key not in ["history", "events"]:
                state[key] = old[key]
        add_event("Última ação desfeita")


def new_match():
    undo_stack.clear()
    state["finished"] = False
    state["side_change"] = False
    state["server"] = "A"
    state["score"]["A"] = {"points": 0, "games": 0, "sets": 0}
    state["score"]["B"] = {"points": 0, "games": 0, "sets": 0}
    state["events"] = []
    add_event("Nova partida iniciada")


def parse_command(command):
    cmd = command.lower().strip()

    if "azul" in cmd or "dupla a" in cmd or "time a" in cmd:
        add_point("A")
        return "Ponto para Azul"

    if "vermelho" in cmd or "vermelha" in cmd or "dupla b" in cmd or "time b" in cmd:
        add_point("B")
        return "Ponto para Vermelho"

    if "desfaz" in cmd or "desfazer" in cmd or "voltar" in cmd:
        undo()
        return "Última ação desfeita"

    if "zerar" in cmd or "reset" in cmd or "novo jogo" in cmd or "nova partida" in cmd:
        new_match()
        return "Nova partida iniciada"

    if "troca lado" in cmd or "virada" in cmd or "trocar lado" in cmd:
        undo_stack.append(snapshot())
        state["side_change"] = not state["side_change"]
        add_event("Virada de campo alterada manualmente")
        return "Virada de campo alterada"

    return "Comando não reconhecido"


@app.route("/")
def placar():
    return render_template("placar.html")


@app.route("/control")
def control():
    return render_template("control.html")


@app.route("/api/state")
def api_state():
    return jsonify(public_state())


@app.route("/api/point/<team>", methods=["POST", "GET"])
def api_point(team):
    team = team.upper()
    if team in ["A", "B"]:
        add_point(team)
        emit_state()
    return jsonify(public_state())


@app.route("/api/undo", methods=["POST", "GET"])
def api_undo():
    undo()
    emit_state()
    return jsonify(public_state())


@app.route("/api/new", methods=["POST", "GET"])
def api_new():
    new_match()
    emit_state()
    return jsonify(public_state())


@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json() or {}
    command = data.get("command", "")
    result = parse_command(command)
    emit_state()
    return jsonify({"ok": True, "result": result, "state": public_state()})


@app.route("/api/config", methods=["POST"])
def api_config():
    data = request.get_json() or {}

    undo_stack.append(snapshot())

    state["court"] = data.get("court", state["court"])
    state["match_name"] = data.get("match_name", state["match_name"])
    state["team_a"] = data.get("team_a", state["team_a"])
    state["team_b"] = data.get("team_b", state["team_b"])
    state["server"] = data.get("server", state["server"])

    add_event("Configuração da partida atualizada")
    emit_state()

    return jsonify(public_state())


@socketio.on("connect")
def on_connect():
    emit_state()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        certfile="cert.pem",
        keyfile="key.pem"
    )
