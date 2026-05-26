class VoiceService:
    def __init__(self, courts):
        self.courts = courts

    def handle(self, court_id, command):
        cmd = (command or "").lower().strip()

        if any(token in cmd for token in ("azul", "dupla a", "time a")):
            state = self.courts.point(court_id, "A")
            return "Ponto para Azul", state

        if any(token in cmd for token in ("vermelho", "vermelha", "dupla b", "time b")):
            state = self.courts.point(court_id, "B")
            return "Ponto para Vermelho", state

        if any(token in cmd for token in ("desfaz", "desfazer", "voltar")):
            state = self.courts.undo(court_id)
            return "Ultima acao desfeita", state

        if any(token in cmd for token in ("zerar", "reset", "novo jogo", "nova partida")):
            state = self.courts.new_match(court_id)
            return "Nova partida iniciada", state

        if any(token in cmd for token in ("troca lado", "virada", "trocar lado")):
            state = self.courts.toggle_side_change(court_id)
            return "Virada de campo alterada", state

        return "Comando nao reconhecido", self.courts.state(court_id)
