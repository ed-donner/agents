import unittest

from flow_engineering_team.trigger import FlowTriggerError, parse_trigger_payload


class TestParseTriggerPayload(unittest.TestCase):
    def test_accepts_json_object(self):
        self.assertEqual(parse_trigger_payload('{"app_name":"demo"}'), {"app_name": "demo"})

    def test_rejects_non_object_json(self):
        for raw_payload in ("[1]", '"text"', "true", "42", "null"):
            with self.subTest(raw_payload=raw_payload):
                with self.assertRaisesRegex(FlowTriggerError, "must be a JSON object"):
                    parse_trigger_payload(raw_payload)

    def test_reports_invalid_json(self):
        with self.assertRaisesRegex(FlowTriggerError, "Invalid JSON payload"):
            parse_trigger_payload("{")


if __name__ == "__main__":
    unittest.main()
