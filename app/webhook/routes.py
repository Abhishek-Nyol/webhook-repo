from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timezone
from pymongo import MongoClient

webhook_bp = Blueprint("webhook", __name__)

# ------------------ MongoDB ------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["github_webhook"]
collection = db["events"]

# ------------------ WEBHOOK ENDPOINT ------------------
@webhook_bp.route("/webhook", methods=["POST"])
def github_webhook():
    payload = request.get_json()

    if not payload:
        return jsonify({"error": "Invalid or missing JSON"}), 415

    timestamp = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M:%S UTC")

    # ---------------- PUSH ----------------
    if payload.get("ref"):
        action = "PUSH"
        request_id = payload.get("after")
        author = payload.get("pusher", {}).get("name")
        branch = payload.get("ref", "").replace("refs/heads/", "")

        document = {
            "request_id": request_id,
            "author": author,
            "action": action,
            "from_branch": branch,
            "to_branch": branch,
            "timestamp": timestamp
        }

        collection.insert_one(document)
        return jsonify({"status": "push stored"}), 200

    # ---------------- PULL REQUEST ----------------
    if payload.get("pull_request") and payload.get("action") == "opened":
        action = "PULL_REQUEST"
        pr = payload["pull_request"]

        document = {
            "request_id": str(pr["id"]),
            "author": pr["user"]["login"],
            "action": action,
            "from_branch": pr["head"]["ref"],
            "to_branch": pr["base"]["ref"],
            "timestamp": timestamp
        }

        collection.insert_one(document)
        return jsonify({"status": "pull request stored"}), 200

    # ---------------- MERGE ----------------
    if payload.get("pull_request") and payload.get("action") == "closed" and payload["pull_request"]["merged"]:
        action = "MERGE"
        pr = payload["pull_request"]

        document = {
            "request_id": str(pr["id"]),
            "author": pr["merged_by"]["login"],
            "action": action,
            "from_branch": pr["head"]["ref"],
            "to_branch": pr["base"]["ref"],
            "timestamp": timestamp
        }

        collection.insert_one(document)
        return jsonify({"status": "merge stored"}), 200

    return jsonify({"status": "ignored"}), 200


# ------------------ UI ------------------
@webhook_bp.route("/")
def ui():
    events = list(collection.find().sort("_id", -1))
    return render_template("ui.html", events=events)