from reuse_api import form


TEST_REPO: str = "git.fsfe.org/reuse/api"


def test_is_reachable() -> None:
    assert form.is_reachable(TEST_REPO)
    assert not form.is_reachable(TEST_REPO + "nonexistent-suffix")


def test_sanitize_url() -> None:
    assert form.sanitize_url("https://" + TEST_REPO) == TEST_REPO
    assert form.sanitize_url(TEST_REPO + ".git") == TEST_REPO
