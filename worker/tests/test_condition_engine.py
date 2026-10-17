import unittest
from app.engine.condition_engine import ConditionEngine

class TestConditionEngine(unittest.TestCase):
    def test_follower_condition_following(self):
        cond = {"type": "FOLLOWER_STATUS", "expected": "FOLLOWING", "fallbackAction": "SEND_FOLLOW_GATE"}
        passed, action = ConditionEngine.evaluate_condition(cond, {"follower_status": "FOLLOWING"})
        self.assertTrue(passed)
        self.assertEqual(action, "CONTINUE")

    def test_follower_condition_not_following(self):
        cond = {"type": "FOLLOWER_STATUS", "expected": "FOLLOWING", "fallbackAction": "SEND_FOLLOW_GATE"}
        passed, action = ConditionEngine.evaluate_condition(cond, {"follower_status": "NOT_FOLLOWING"})
        self.assertFalse(passed)
        self.assertEqual(action, "SEND_FOLLOW_GATE")

    def test_follower_condition_unknown_safe_degradation(self):
        cond = {"type": "FOLLOWER_STATUS", "expected": "FOLLOWING", "fallbackAction": "SEND_FOLLOW_GATE"}
        passed, action = ConditionEngine.evaluate_condition(cond, {"follower_status": "UNKNOWN"})
        self.assertFalse(passed)
        self.assertEqual(action, "SEND_FOLLOW_GATE")

    def test_keyword_match_condition(self):
        cond = {"type": "KEYWORD_MATCH", "keyword": "PRICE", "fallbackAction": "STOP"}
        passed, action = ConditionEngine.evaluate_condition(cond, {"text": "what is the price please?"})
        self.assertTrue(passed)
        self.assertEqual(action, "CONTINUE")

        passed, action = ConditionEngine.evaluate_condition(cond, {"text": "nice photo!"})
        self.assertFalse(passed)
        self.assertEqual(action, "STOP")

if __name__ == "__main__":
    unittest.main()
