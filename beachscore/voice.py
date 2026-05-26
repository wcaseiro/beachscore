import re
import unicodedata


class VoiceService:
    def __init__(self, courts):
        self.courts = courts

    def handle(self, court_id, command):
        state = self.courts.state(court_id)
        cmd = normalize(command)
        team_a_tokens = team_tokens(state["team_a"], ("a", "azul"))
        team_b_tokens = team_tokens(state["team_b"], ("b", "vermelho", "vermelha"))

        if matches_team(cmd, team_a_tokens):
            state = self.courts.point(court_id, "A")
            return f"Ponto para {state['team_a']}", state, True

        if matches_team(cmd, team_b_tokens):
            state = self.courts.point(court_id, "B")
            return f"Ponto para {state['team_b']}", state, True

        if any(token in cmd for token in ("desfaz", "desfazer", "voltar")):
            state = self.courts.undo(court_id)
            return "Ultima acao desfeita", state, True

        if any(token in cmd for token in ("zerar", "reset", "novo jogo", "nova partida")):
            state = self.courts.new_match(court_id)
            return "Nova partida iniciada", state, True

        if any(token in cmd for token in ("troca lado", "virada", "trocar lado")):
            state = self.courts.toggle_side_change(court_id)
            return "Virada de campo alterada", state, True

        return "Comando nao reconhecido", state, False


def normalize(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    return re.sub(r"[^a-z0-9 ]+", " ", value)


def team_tokens(team_name, aliases):
    ignored = {"dupla", "time", "e", "x"}
    words = [word for word in normalize(team_name).split() if word not in ignored]
    return set(words).union(aliases)


def matches_team(command, tokens):
    words = set(command.split())
    if words.intersection(tokens):
        return True
    return any(f"dupla {token}" in command or f"time {token}" in command for token in tokens)
