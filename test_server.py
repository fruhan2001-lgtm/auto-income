import unittest
from server import validate

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid = {"service": "Sadrokartón", "area": "Ružinov", "description": "TEST"}

    def test_valid(self):
        self.assertTrue(validate(self.valid))

    def test_invalid_fields(self):
        for field, value in [("service", "unknown"), ("area", []), ("description", ""), ("description", " "), ("description", "x"*1501), ("description", None)]:
            with self.subTest(field=field, value=value):
                self.assertFalse(validate(dict(self.valid, **{field: value})))

    def test_non_object(self):
        for value in [None, [], 42, "TEST"]:
            self.assertFalse(validate(value))

    def test_missing_fields(self):
        for field in self.valid:
            data = dict(self.valid)
            del data[field]
            self.assertFalse(validate(data))

if __name__ == "__main__":
    unittest.main()
