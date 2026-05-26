from flask import Blueprint, current_app, jsonify, request


api_bp = Blueprint("api", __name__)


def courts():
    return current_app.extensions["beachscore_courts"]


def voice():
    return current_app.extensions["beachscore_voice"]


def ws():
    return current_app.extensions["beachscore_websocket"]


def requested_court_id(default="arena-1"):
    if request.is_json:
        data = request.get_json(silent=True) or {}
        return data.get("court_id", default)
    return request.args.get("court_id", default)


@api_bp.get("/state")
def legacy_state():
    return jsonify(courts().state(requested_court_id()))


@api_bp.route("/point/<team>", methods=["POST", "GET"])
def legacy_point(team):
    cid = requested_court_id()
    state = courts().point(cid, team)
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.route("/undo", methods=["POST", "GET"])
def legacy_undo():
    cid = requested_court_id()
    state = courts().undo(cid)
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.route("/new", methods=["POST", "GET"])
def legacy_new():
    cid = requested_court_id()
    state = courts().new_match(cid)
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.post("/command")
def legacy_command():
    data = request.get_json() or {}
    cid = data.get("court_id", "arena-1")
    result, state = voice().handle(cid, data.get("command", ""))
    ws().emit_state(cid, state)
    return jsonify({"ok": True, "result": result, "state": state})


@api_bp.post("/config")
def legacy_config():
    data = request.get_json() or {}
    cid = data.get("court_id", "arena-1")
    state = courts().config(cid, data)
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.get("/courts")
def list_courts():
    return jsonify({"courts": courts().courts()})


@api_bp.post("/courts")
def create_court():
    data = request.get_json() or {}
    cid = data.get("id") or slugify(data.get("name") or "Arena")
    name = data.get("name") or cid.replace("-", " ").title()
    state = courts().ensure_court(cid, name)
    public = courts().state(state["court_id"])
    ws().emit_state(cid, public)
    return jsonify(public), 201


@api_bp.get("/courts/<cid>/state")
def court_state(cid):
    return jsonify(courts().state(cid))


@api_bp.post("/courts/<cid>/point/<team>")
def court_point(cid, team):
    state = courts().point(cid, team)
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.post("/courts/<cid>/undo")
def court_undo(cid):
    state = courts().undo(cid)
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.post("/courts/<cid>/new")
def court_new(cid):
    state = courts().new_match(cid)
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.post("/courts/<cid>/config")
def court_config(cid):
    state = courts().config(cid, request.get_json() or {})
    ws().emit_state(cid, state)
    return jsonify(state)


@api_bp.post("/courts/<cid>/command")
def court_command(cid):
    data = request.get_json() or {}
    result, state = voice().handle(cid, data.get("command", ""))
    ws().emit_state(cid, state)
    return jsonify({"ok": True, "result": result, "state": state})


@api_bp.get("/courts/<cid>/timeline")
def court_timeline(cid):
    limit = int(request.args.get("limit", 100))
    return jsonify({"events": courts().timeline(cid, limit)})


@api_bp.get("/replay/<int:event_id>")
def replay(event_id):
    event = courts().replay_state(event_id)
    if not event:
        return jsonify({"error": "event not found"}), 404
    return jsonify(event)


@api_bp.get("/matches")
def list_matches():
    return jsonify({"matches": courts().matches(request.args.get("court_id"))})


def slugify(value):
    chars = []
    for char in value.lower().strip():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "court"
