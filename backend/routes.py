from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, Response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))


######################################################################
# RETURN HEALTH OF THE APP
######################################################################
@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200


######################################################################
# COUNT THE NUMBER OF PICTURES
######################################################################
@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})
    return {"count": count}, 200


######################################################################
# GET method for the endpoint /song
######################################################################
@app.route("/song")
def songs():
    songs = list(db.songs.find({}))
    return json_util.dumps({"songs": songs}),200
    

######################################################################
# GET method for the endpoint /song/<int:id>
######################################################################
@app.route("/song/<int:id>")
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    if song:
        return json_util.dumps(song), 200

    return {"message": "song with id not found"}, 404


######################################################################
# POST method for the endpoint /song
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    new_song = request.json
    if db.songs.find_one({'id': new_song['id']}):
        return jsonify({"Message": f"song with id {new_song['id']} already present"}), 302

    inserted_song = db.songs.insert_one(new_song)

    # Serialize the ObjectId properly
    return json_util.dumps({"inserted id": inserted_song.inserted_id}), 201


######################################################################
# PUT method for the endpoint /song/<int:id>
######################################################################
@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    changes = request.json
    song = db.songs.find_one({'id': id})
    if song:
        is_different = any(song[key] != changes[key] for key in changes if key in song)

        if is_different:
            song_update = db.songs.update_one({"id": id}, {'$set': changes})
            if song_update.modified_count == 0:
                return {"message": "song found, but nothing updated"}, 200
            else:
                updated_song = db.songs.find_one({"id": id})
                return json_util.dumps(updated_song), 201
        else:
            return jsonify({"message": "There are no changes to be made"}), 200
    else:
        return jsonify({"message": "Song not found"}), 404
    

######################################################################
# DELETE method for the endpoint /song/<int:id>
######################################################################
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    deleted = db.songs.delete_one({"id": id})
    if deleted.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    else:
        return "", 204

    






# @app.route("/song", methods=["POST"])
# def create_song():
#     # get data from the json body
#     song_in = request.json
#     print(song_in["id"])
#     # if the id is already there, return 303 with the URL for the resource
#     song = db.songs.find_one({"id": song_in["id"]})
#     if song:
#         return {
#             "Message": f"song with id {song_in['id']} already present"
#         }, 302
#     insert_id: InsertOneResult = db.songs.insert_one(song_in)
#     return {"inserted id": parse_json(insert_id.inserted_id)}, 201