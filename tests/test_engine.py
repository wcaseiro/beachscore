import unittest

from beachscore import engine


class ScoreEngineTest(unittest.TestCase):
    def test_no_ad_game_after_four_points(self):
        state = engine.default_state()

        for _ in range(4):
            engine.add_point(state, "A")

        self.assertEqual(state["score"]["A"]["games"], 1)
        self.assertEqual(state["score"]["A"]["points"], 0)
        self.assertEqual(state["score"]["B"]["points"], 0)
        self.assertEqual(state["server"], "B")

    def test_advantage_scoring_requires_two_points(self):
        state = engine.default_state()
        state["no_ad"] = False

        for team in ("A", "B", "A", "B", "A", "B", "A"):
            engine.add_point(state, team)

        self.assertEqual(engine.point_label(state, "A"), "VANT")
        self.assertEqual(state["score"]["A"]["games"], 0)

        engine.add_point(state, "A")

        self.assertEqual(state["score"]["A"]["games"], 1)

    def test_set_and_match_finish(self):
        state = engine.default_state()

        for _ in range(24):
            engine.add_point(state, "A")

        self.assertEqual(state["score"]["A"]["sets"], 1)
        self.assertFalse(state["finished"])

        for _ in range(24):
            engine.add_point(state, "A")

        self.assertEqual(state["score"]["A"]["sets"], 2)
        self.assertTrue(state["finished"])


if __name__ == "__main__":
    unittest.main()
