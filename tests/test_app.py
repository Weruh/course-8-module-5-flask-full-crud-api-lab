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


def test_read_events():
    client = app.test_client()
    response = client.get('/events')
    assert response.status_code == 200
    assert response.get_json() == [event.to_dict() for event in events]
    response = client.get('/events/1')
    assert response.status_code == 200
    assert response.get_json() == {'id': 1, 'title': 'Tech Meetup'}
    response = client.get('/events/99')
    assert response.status_code == 404
    assert response.get_json() == {'error': 'Event not found'}


@pytest.mark.parametrize('method,url', [('post', '/events'), ('patch', '/events/1')])
@pytest.mark.parametrize('payload', [
    {}, {'title': None}, {'title': ''}, {'title': '   '},
    {'title': 42}, {'title': False}, {'title': []}, [], 'title',
])
def test_invalid_title_does_not_change_data(method, url, payload):
    before = [event.to_dict() for event in events]
    response = getattr(app.test_client(), method)(url, json=payload)
    assert response.status_code == 400
    assert 'error' in response.get_json()
    assert [event.to_dict() for event in events] == before


@pytest.mark.parametrize('method,url', [('post', '/events'), ('patch', '/events/1')])
@pytest.mark.parametrize('body,content_type', [
    ('{', 'application/json'), ('null', 'application/json'),
    ('', 'application/json'), ('title=Example', 'text/plain'),
])
def test_invalid_json(method, url, body, content_type):
    before = [event.to_dict() for event in events]
    response = getattr(app.test_client(), method)(
        url, data=body, content_type=content_type,
    )
    assert response.status_code == 400
    assert 'error' in response.get_json()
    assert [event.to_dict() for event in events] == before


def test_full_crud_lifecycle():
    client = app.test_client()
    created = client.post('/events', json={'title': 'New event'}).get_json()
    url = f"/events/{created['id']}"
    assert client.get(url).get_json() == created
    updated = client.patch(url, json={'title': 'Updated', 'id': 99})
    assert updated.get_json() == {'id': created['id'], 'title': 'Updated'}
    assert client.get(url).get_json() == updated.get_json()
    deleted = client.delete(url)
    assert deleted.status_code == 204
    assert deleted.data == b''
    assert client.get(url).status_code == 404
    assert client.delete(url).status_code == 404


def test_creation_after_deletion_uses_unique_ids():
    client = app.test_client()
    client.delete('/events/1')
    response = client.post('/events', json={'title': 'New event'})
    assert response.status_code == 201
    assert response.get_json()['id'] == 3
    assert len({event.id for event in events}) == len(events)


def test_empty_store():
    client = app.test_client()
    client.delete('/events/1')
    client.delete('/events/2')
    assert client.get('/events').get_json() == []
    response = client.post('/events', json={'title': 'First event'})
    assert response.status_code == 201
    assert response.get_json() == {'id': 1, 'title': 'First event'}
