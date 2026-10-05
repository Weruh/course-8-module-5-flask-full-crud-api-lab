from app import app, events, Event
import pytest

@pytest.fixture(autouse=True)
def reset_data():
    # Reset the in-memory "database" before each test
    events.clear()
    events.append(Event(1, "Tech Meetup"))
    events.append(Event(2, "Python Workshop"))

def test_create_event():
    client = app.test_client()
    response = client.post("/events", json={"title": "Hackathon"})
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data and data["title"] == "Hackathon"

def test_update_event():
    client = app.test_client()
    response = client.patch("/events/1", json={"title": "Hackathon 2025"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Hackathon 2025"

def test_update_event_not_found():
    client = app.test_client()
    response = client.patch("/events/99", json={"title": "Ghost Event"})
    assert response.status_code == 404

def test_delete_event():
    client = app.test_client()
    response = client.delete("/events/2")
    assert response.status_code == 204

def test_delete_event_not_found():
    client = app.test_client()
    response = client.delete("/events/99")
    assert response.status_code == 404


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"title": "   "},
                                     {"title": None}, {"title": 42}, [], "title"])
@pytest.mark.parametrize("method,path", [("post", "/events"), ("patch", "/events/1")])
def test_invalid_title_does_not_mutate_events(payload, method, path):
    before = [event.to_dict() for event in events]
    response = getattr(app.test_client(), method)(path, json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert [event.to_dict() for event in events] == before


@pytest.mark.parametrize("body,content_type", [("{", "application/json"),
                                               ("", "application/json"),
                                               ('{"title":"Test"}', "text/plain")])
def test_invalid_json(body, content_type):
    response = app.test_client().post("/events", data=body, content_type=content_type)
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert len(events) == 2


def test_create_after_deletion_has_unique_id():
    client = app.test_client()
    client.delete("/events/1")
    response = client.post("/events", json={"title": "New Event"})
    assert response.status_code == 201
    assert response.get_json()["id"] == 3
    assert len({event.id for event in events}) == len(events)


def test_create_in_empty_store():
    events.clear()
    response = app.test_client().post("/events", json={"title": "First Event"})
    assert response.status_code == 201
    assert response.get_json() == {"id": 1, "title": "First Event"}


def test_deleted_event_is_no_longer_available():
    client = app.test_client()
    response = client.delete("/events/2")
    assert response.status_code == 204
    assert response.data == b""
    assert client.patch("/events/2", json={"title": "Deleted"}).status_code == 404
    assert client.delete("/events/2").status_code == 404
