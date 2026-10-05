from flask import Flask, jsonify, request

app = Flask(__name__)

# Simulated data
class Event:
    def __init__(self, id, title):
        self.id = id
        self.title = title

    def to_dict(self):
        return {"id": self.id, "title": self.title}

# In-memory "database"
events = [
    Event(1, "Tech Meetup"),
    Event(2, "Python Workshop")
]

def find_event(event_id):
    return next((event for event in events if event.id == event_id), None)


def get_title():
    # Reject malformed JSON, non-object payloads, and blank titles consistently.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    return title


@app.route("/events", methods=["GET"] )
def list_events():
    return jsonify([event.to_dict() for event in events])


@app.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = find_event(event_id)
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(event.to_dict())


@app.route("/events", methods=["POST"])
def create_event():
    title = get_title()
    if title is None:
        return jsonify({"error": "title must be a non-empty string"}), 400
    # Using the largest current ID avoids collisions after deletions.
    event_id = max((event.id for event in events), default=0) + 1
    event = Event(event_id, title)
    events.append(event)
    return jsonify(event.to_dict()), 201


@app.route("/events/<int:event_id>", methods=["PATCH"])
def update_event(event_id):
    event = find_event(event_id)
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    title = get_title()
    if title is None:
        return jsonify({"error": "title must be a non-empty string"}), 400
    event.title = title
    return jsonify(event.to_dict()), 200


@app.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    event = find_event(event_id)
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    events.remove(event)
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)
