import unittest

from blog.app import allowed_file, app, slugify, validate_payload


class BlogWebsiteTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("IGN Style: Hello World!"), "ign-style-hello-world")

    def test_validate_payload_review(self):
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

    def test_allowed_file(self):
        self.assertTrue(allowed_file("cover.jpg"))
        self.assertFalse(allowed_file("cover.exe"))

    def test_home_route(self):
        client = app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AGI", response.data)


if __name__ == "__main__":
    unittest.main()
