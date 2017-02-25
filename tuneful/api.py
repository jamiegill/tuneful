import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from tuneful import app
from .database import session
from .utils import upload_path

song_schema = {
    "properties": {
        "file": {
            "properties": {
                "id": {"type": "number"}
            },
        },
    },
    "required": ["file"]
}

@app.route("/api/songs", methods=['GET'])
@decorators.accept("application/json")
def songs_get():
    
    """ Return a list of songs as json """
    songs = session.query(models.Song).all()
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["GET"])
def song_get(id):
    """ Single song endpoint """
    # Get the song from the database
    song = session.query(models.Song).get(id)
    
    # Check whether the post exists
    # If not return a 404 with a helful message
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
        
    # Return the post as json
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")    
    
@app.route("/api/songs", methods=['POST'])
@decorators.accept("application/json")
def songs_post():
    """ Add a new song """
    data = request.json
    
    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        validate(data, song_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    # Look for post in the {"file": {"id": 7}} format
    song = models.Song(file_id=data["file"]["id"])
    session.add(song)
    session.commit()
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("songs_get")}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")
                    
@app.route("/api/songs/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def song_modify(id):
    """ Single song modification """
    data = request.json
    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        validate(data, song_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")

    # Get the post from the database
    song = session.query(models.Song).get(id)
    
        # Check whether the song exists
    if not song:
        message = "Could not find song with id {} so cannot UPDATE song".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
    song = session.query(models.Song).filter(models.Song.id == id).first()
    song.file_id = data["file"]["id"]
    session.commit()
    message = "successfully UPDATED song {}".format(id)
    data = json.dumps({"message": message})
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["DELETE"])
def song_delete(id):
    """ Delete single song """
    # Get the song from the database
    song = session.query(models.Song).get(id)
    
    # Check whether the song exists
    # If not return a 404 with a helful message
    if not song:
        message = "Could not find song with id {} so cannot DELETE song".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
        
    session.query(models.Song.id).filter(models.Song.id == id).delete()
    session.commit()
    message = "successfully DELETED song {}".format(id)
    data = json.dumps({"message": message})
    return Response(data, 200, mimetype="application/json")
    
@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(upload_path(), filename)
    
@app.route("/api/files", methods=["POST"])    
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")
        
    filename = secure_filename(file.filename)
    db_file = models.File(filename=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))
    
    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")
    