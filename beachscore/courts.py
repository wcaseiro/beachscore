from collections import defaultdict
from threading import RLock

from . import engine


class CourtManager:
    def __init__(self, store):
        self.store = store
        self._states = {}
        self._undo = defaultdict(list)
        self._lock = RLock()
        self.ensure_court("arena-1", "Arena 01")

    def ensure_court(self, court_id, name):
        with self._lock:
            self.store.ensure_court(court_id, name)
            state = self.store.active_match(court_id)
            if state is None:
                state = engine.default_state(court_id, name)
                match_id = self.store.create_match(court_id, state["match_name"], state)
                state["match_id"] = match_id
                self.store.save_match_state(match_id, state)
                self.store.append_event(
                    court_id, match_id, "match_created", "Partida criada", state
                )
            self._states[court_id] = state
            return state

    def courts(self):
        return self.store.list_courts()

    def matches(self, court_id=None):
        return self.store.list_matches(court_id)

    def state(self, court_id="arena-1"):
        with self._lock:
            return engine.public_state(self._load(court_id))

    def point(self, court_id, team):
        with self._lock:
            state = self._load(court_id)
            self._remember(court_id, state)
            messages = engine.add_point(state, team)
            text = messages[-1] if messages else "Partida ja encerrada"
            return self._save(court_id, "point", text)

    def undo(self, court_id):
        with self._lock:
            if self._undo[court_id]:
                old = self._undo[court_id].pop()
                current_events = self._load(court_id).get("events", [])
                old["events"] = current_events
                self._states[court_id] = old
                engine.add_event(old, "Ultima acao desfeita")
            return self._save(court_id, "undo", "Ultima acao desfeita")

    def new_match(self, court_id):
        with self._lock:
            state = self._load(court_id)
            self._undo[court_id].clear()
            engine.reset_match(state)
            match_id = self.store.create_match(court_id, state["match_name"], state)
            state["match_id"] = match_id
            self.store.save_match_state(match_id, state)
            self.store.append_event(
                court_id, match_id, "new_match", "Nova partida iniciada", state
            )
            return engine.public_state(state)

    def config(self, court_id, data):
        with self._lock:
            state = self._load(court_id)
            self._remember(court_id, state)
            engine.update_config(state, data)
            self.store.ensure_court(court_id, state["court"])
            return self._save(court_id, "config", "Configuracao atualizada")

    def toggle_side_change(self, court_id):
        with self._lock:
            state = self._load(court_id)
            self._remember(court_id, state)
            engine.toggle_side_change(state)
            return self._save(court_id, "side_change", "Virada de campo alterada")

    def replay_state(self, event_id):
        event = self.store.event_snapshot(event_id)
        if not event:
            return None
        event["state"] = engine.public_state(event["state"])
        return event

    def timeline(self, court_id, limit=100):
        return self.store.timeline(court_id, limit)

    def _load(self, court_id):
        if court_id not in self._states:
            court_name = court_id.replace("-", " ").title()
            return self.ensure_court(court_id, court_name)
        return self._states[court_id]

    def _remember(self, court_id, state):
        self._undo[court_id].append(engine.snapshot(state))
        self._undo[court_id] = self._undo[court_id][-50:]

    def _save(self, court_id, action, text):
        state = self._load(court_id)
        self.store.save_match_state(state["match_id"], state)
        self.store.append_event(court_id, state["match_id"], action, text, state)
        return engine.public_state(state)
