import base64

from serpscrap.result_normalizer import normalize_result_url


def test_google_redirect_and_tracking_parameters_are_canonicalized():
    result = normalize_result_url(
        "https://www.google.com/url?q=https%3A%2F%2FExample.com%2Fpage%3Futm_source%3Dgoogle%26keep%3D1&ved=abc"
    )
    assert result["canonical_url"] == "https://example.com/page?keep=1"
    assert result["source_url"].startswith("https://www.google.com/url")


def test_bing_base64_redirect_is_unwrapped():
    target = "https://example.org/article?utm_medium=cpc&item=7"
    encoded = "a1" + base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")
    result = normalize_result_url(f"https://www.bing.com/ck/a?u={encoded}")
    assert result["canonical_url"] == "https://example.org/article?item=7"


def test_image_result_is_typed_and_invalid_urls_are_not_guessed():
    image = normalize_result_url(
        "https://images.example/search?mediaurl=https%3A%2F%2Fcdn.example%2Fphoto.jpg",
        "image",
    )
    assert image["result_kind"] == "image"
    assert image["canonical_url"] == "https://cdn.example/photo.jpg"
    assert normalize_result_url("javascript:alert(1)")["canonical_url"] is None
