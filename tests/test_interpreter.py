import unittest
import json

from src.mediascan.interpreter import Interpreter


class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()

    def test_find_year(self):
        self.assertEqual(
            self.interpreter.find_year("Movie Title 2020")['value'], 2020
        )
        self.assertEqual(
            self.interpreter.find_year("Movie Title (2020)")['value'], 2020
        )
        self.assertEqual(self.interpreter.find_year("Movie Title")['value'], None)

    def test_find_episode(self):
        self.assertEqual(self.interpreter.find_episode("S01E05")['value'], (1, 5))
        self.assertEqual(self.interpreter.find_episode("1x05")['value'], (1, 5))
        self.assertEqual(
            self.interpreter.find_episode("Episode 5")['value'], None
        )

    def test_find_season(self):
        self.assertEqual(self.interpreter.find_season("Season 3")['value'], 3)
        self.assertEqual(self.interpreter.find_season("S03")['value'], 3)
        self.assertEqual(self.interpreter.find_season("No season")['value'], None)

    def test_find_date(self):
        self.assertEqual(
            self.interpreter.find_date("2020-01-15")['value'], "2020-01-15"
        )
        self.assertEqual(self.interpreter.find_date("No date")['value'], None)

    def test_find_resolution(self):
        self.assertEqual(self.interpreter.find_resolution("1080p")['value'], "1080p")
        self.assertEqual(self.interpreter.find_resolution("720p")['value'], "720p")
        self.assertEqual(
            self.interpreter.find_resolution("No resolution")['value'], None
        )

    def test_find_source(self):
        self.assertEqual(self.interpreter.find_source("BluRay")['value'], "bluray")
        self.assertEqual(self.interpreter.find_source("WEB-DL")['value'], "web")
        self.assertEqual(self.interpreter.find_source("No source")['value'], None)

    def test_is_proper_or_repack(self):
        self.assertTrue(self.interpreter.is_proper_or_repack("PROPER")['value'])
        self.assertTrue(self.interpreter.is_proper_or_repack("REPACK")['value'])
        self.assertFalse(self.interpreter.is_proper_or_repack("Not proper")['value'])

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
        self.assertEqual(result["year"], 1999)
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
