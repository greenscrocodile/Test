import unittest

from blog.app import slugify, validate_payload


class BlogAppTests(unittest.TestCase):
    def test_slugify_removes_symbols_and_normalizes_spaces(self):
        self.assertEqual(slugify("  Elden Ring: Night-Reign!!!  "), "elden-ring-night-reign")

    def test_validate_payload_requires_title_and_template_fields(self):
        payload = {
            "title": "",
            "summary": "",
            "content": "",
            "score": "",
            "pros": [],
            "cons": [],
        }
        missing = validate_payload(payload, "Review")
        self.assertEqual(missing, ["title", "summary", "content", "score", "pros", "cons"])

    def test_validate_payload_accepts_complete_news_payload(self):
        payload = {
            "title": "Switch 2 launches",
            "summary": "Nintendo confirms launch date.",
            "content": "The console launches this year.",
        }
        self.assertEqual(validate_payload(payload, "News"), [])


if __name__ == "__main__":
    unittest.main()
