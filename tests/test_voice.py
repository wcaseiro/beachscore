import os
import tempfile
import unittest

from beachscore import create_app


class VoiceServiceTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        self.app = create_app({"TESTING": True, "DATABASE_PATH": self.db_path})
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.db_path)

    def test_voice_uses_configured_team_names(self):
        self.client.post(
            "/api/config",
            json={
                "team_a": "Dupla Azul",
                "team_b": "Dupla Verde",
            },
        )

        response = self.client.post("/api/command", json={"command": "ponto verde"})
        data = response.get_json()

        self.assertTrue(data["recognized"])
        self.assertEqual(data["result"], "Ponto para Dupla Verde")
        self.assertEqual(data["state"]["score"]["B"]["label"], "15")

    def test_unrecognized_command_is_reported(self):
        response = self.client.post("/api/command", json={"command": "banana"})
        data = response.get_json()

        self.assertFalse(data["recognized"])
        self.assertEqual(data["result"], "Comando nao reconhecido")


if __name__ == "__main__":
    unittest.main()
