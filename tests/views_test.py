from http import HTTPStatus

from reuse_api.db import register, update

from .conftest import TEST_REPO


def test_gets(client) -> None:
    """Tests simple GET requests."""
    for p in ("/", "/projects"):
        response = client.get(p)
        assert response.status_code == HTTPStatus.OK, f"GET ON {p} is not OK"


def test_register_with_parameter(client) -> None:
    response = client.get("/register?url=" + TEST_REPO)
    assert response.status_code == HTTPStatus.OK
    assert TEST_REPO in response.data.decode()


def test_info_and_badge_and_json(client, db_empty) -> None:
    """General endpoint test"""
    url: str = f"/info/{TEST_REPO}"

    # Unregistered
    response = client.get(url)
    assert (
        response.status_code == HTTPStatus.NOT_FOUND
    ), "Unregistered info is not NOT_FOUND"

    response = client.get(f"/badge/{TEST_REPO}")
    assert response.status_code == HTTPStatus.OK, "Unregistered badge is not OK"

    response = client.get(f"/status/{TEST_REPO}")
    assert (
        response.status_code == HTTPStatus.NOT_FOUND
    ), f"Uninitialised json is not NOT_FOUND ({response.status_code})"

    register(TEST_REPO)  # Uninitialised

    response = client.get(url)
    assert (
        response.status_code == HTTPStatus.FAILED_DEPENDENCY
    ), "Uninitialised info is not FAILED_DEPENDENCY"

    response = client.get(f"/badge/{TEST_REPO}")
    assert response.status_code == HTTPStatus.OK, "Uninitialised badge is not OK"

    update(TEST_REPO)  # Updated

    response = client.get(url)
    assert response.status_code == HTTPStatus.OK, "Updated info is not OK"

    response = client.get(f"/badge/{TEST_REPO}")
    assert response.status_code == HTTPStatus.OK, "Updated badge is not OK"

    response = client.get(f"/status/{TEST_REPO}")
    assert (
        response.status_code == HTTPStatus.OK
    ), f"Updated json is not OK ({response.status_code})"


def test_sbom(client, db_updated) -> None:
    response = client.get(f"/sbom/{TEST_REPO}.spdx")
    assert response.status_code == HTTPStatus.OK, "Updated SBOM is not OK"
