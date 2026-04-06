from  dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise Exception("MONGO_URL is not found in .env file")

client = MongoClient(MONGO_URL)
db = client["campusvoice"]
collection = db["issues"]

app = Flask(__name__)
CORS(app)


def is_toxic(text):
    bad_words = ["fuck", "shit", "bitch", "asshole", "damn"]
    text_lower = text.lower()
    for word in bad_words:
        if word in text_lower:
            return True
    return False

@app.route("/api/issues", methods=["GET"])
def get_issues():
    data = list(collection.find({}, {"_id": 0}))
    return jsonify(data)

@app.route("/api/issues", methods=["POST"])
def add_issue():
    data = request.json
    text = data.get("text")
    if is_toxic(text):
        return jsonify({"error": "Toxic content is not allowed"}), 400
    

    new_issue = {
        "id": int(collection.count_documents({})) + 1,
        "text": text,
        "category": data.get("category"),
        "votes": 0,
        "voterIds": []
    }

    result = collection.insert_one(new_issue)
    new_issue["_id"] = str(result.inserted_id)


    return jsonify(new_issue)

@app.route("/api/issues/<int:id>/upvote", methods=["POST"])
def upvote(id):
    data = request.json
    voter_id = data.get("voterId")

    issue = collection.find_one({"id": id})

    if not issue:
        return jsonify({"error": "Not found"}), 404
    voter_ids = issue.get("voterIds", [])
    
    if voter_id in voter_ids:
        voter_ids.remove(voter_id)
        votes = issue["votes"] - 1
    else:
        voter_ids.append(voter_id)
        votes = issue["votes"] + 1

    collection.update_one({"id": id}, {"$set": {"voterIds": voter_ids, "votes": votes}})

    updated = collection.find_one({"id": id}, {"_id": 0})
    return jsonify(updated)

   
if __name__ == "__main__":
    app.run(debug=True)