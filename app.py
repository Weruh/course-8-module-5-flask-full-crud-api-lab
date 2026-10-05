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


def read_title():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    return title


@app.route("/events", methods=["POST"])
def create_event():
    title = read_title()
    if title is None:
        return jsonify(error="Provide a non-empty title string in a JSON object."), 400
    # Using the largest ID avoids collisions after deleting an event.
    event_id = max((event.id for event in events), default=0) + 1
    event = Event(event_id, title)
    events.append(event)
    return jsonify(event.to_dict()), 201

@app.route("/events/<int:event_id>", methods=["PATCH"])
def update_event(event_id):
    event = find_event(event_id)
    if event is None:
        return jsonify(error="Event not found."), 404
    title = read_title()
    if title is None:
        return jsonify(error="Provide a non-empty title string in a JSON object."), 400
    event.title = title
    return jsonify(event.to_dict()), 200

@app.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    event = find_event(event_id)
    if event is None:
        return jsonify(error="Event not found."), 404
    events.remove(event)
    # A 204 response must have an empty body.
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)
