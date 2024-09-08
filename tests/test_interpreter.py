import unittest
import json

from src.mediascan.interpreter import Interpreter


class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def test_find_year(self):
        self.assertEqual(
            self.interpreter.find_year("Movie Title 2020"), "2020"
        )
        self.assertEqual(
            self.interpreter.find_year("Movie Title (2020)"), "2020"
        )
        self.assertEqual(self.interpreter.find_year("Movie Title"), None)

    def test_find_episode(self):
        self.assertEqual(self.interpreter.find_episode("S01E05"), (1, 5))
        self.assertEqual(self.interpreter.find_episode("1x05"), (1, 5))
        self.assertEqual(
            self.interpreter.find_episode("Episode 5"), (None, None)
        )

    def test_find_season(self):
        self.assertEqual(self.interpreter.find_season("Season 3"), 3)
        self.assertEqual(self.interpreter.find_season("S03"), 3)
        self.assertEqual(self.interpreter.find_season("No season"), None)

    def test_find_date(self):
        self.assertEqual(
            self.interpreter.find_date("2020-01-15"),
            ("2020-01-15", "2020-01-15"),
        )
        self.assertEqual(self.interpreter.find_date("No date"), (None, None))

    def test_find_resolution(self):
        self.assertEqual(self.interpreter.find_resolution("1080p"), "1080p")
        self.assertEqual(self.interpreter.find_resolution("720p"), "720p")
        self.assertEqual(
            self.interpreter.find_resolution("No resolution"), None
        )

    def test_find_source(self):
        self.assertEqual(self.interpreter.find_source("BluRay"), "bluray")
        self.assertEqual(self.interpreter.find_source("WEB-DL"), "web")
        self.assertEqual(self.interpreter.find_source("No source"), None)

    def test_is_proper_or_repack(self):
        self.assertTrue(self.interpreter.is_proper_or_repack("PROPER"))
        self.assertTrue(self.interpreter.is_proper_or_repack("REPACK"))
        self.assertFalse(self.interpreter.is_proper_or_repack("Not proper"))

    def test_clean_title(self):
        self.assertEqual(
            self.interpreter.clean_title("Movie Title! ["), "Movie Title!"
        )
        self.assertEqual(
            self.interpreter.clean_title("Movie Title ("), "Movie Title"
        )

    def test_interpret(self):
        result = self.interpreter.interpret(
            "The.Matrix.1999.1080p.BluRay.x264-GROUP"
        )
        self.assertEqual(result["title"], "The Matrix")
        self.assertEqual(result["year"], "1999")
        self.assertEqual(result["resolution"], "1080p")
        self.assertEqual(result["source"], "bluray")
        self.assertEqual(result["video_codec"], "x264")

    def test_examples_from_jsonl(self):
        with open("tests/examples.jsonl", "r") as f:
            examples = [json.loads(line) for line in f]

        total_examples = len(examples)
        matches = 0

        for example in examples:
            name = example["name"]
            expected = example["expected"]
            result = self.interpreter.interpret(name)

            if (
                result["title"] == expected["title"]
                and result["year"] == expected["year"]
                and result["date"] == expected["date"]
                and result["episode"] == expected["episode"]
                and result["season"] == expected["season"]
            ):
                matches += 1
            else:
                print(f"Name: {name}")
                print(f"Expected: {expected}")
                print(f"Result: {result}")
                print()

        success_rate = matches / total_examples
        self.assertGreaterEqual(
            success_rate, 0.99, f"Success rate {success_rate:.2%} is below 99%"
        )


if __name__ == "__main__":
    unittest.main()
