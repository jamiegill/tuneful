import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO, BytesIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        #return
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def test_get_songs(self):
        """ Getting songs from a populated database """
        songA = models.File(filename="Drones.mp3")
        songA_id = models.Song(file_id=1)
        songB = models.File(filename="Californication.mp3")
        songB_id = models.Song(file_id=2)
        
        session.add_all([songA, songB, songA_id, songB_id])
        session.commit()
        
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(data), 2)
        
        songA = data[0]
        self.assertEqual(songA["file"]["filename"], "Drones.mp3")
        self.assertEqual(songA["id"], 1)
        
        songB = data[1]
        self.assertEqual(songB["file"]["filename"], "Californication.mp3")
        self.assertEqual(songB["id"], 2)
        
    def test_post_song(self):
        """ Posting a new song """
        songA = models.File(filename="Drones.mp3")
        session.add(songA)
        session.commit()
        data = {"file": {"id": 1}}
        
        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

                        
        data=json.loads(response.data.decode("ascii"))
        self.assertEqual(data["file"]["id"], 1)
        self.assertEqual(data["file"]["filename"], "Drones.mp3")
        
        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)
        
        song = songs[0]
        self.assertEqual(song.file_id, 1)
        
    def test_delete_song(self):
        """ Deleting a single song from a populated database """
        songA = models.File(filename="Drones.mp3")
        songA_id = models.Song(file_id=1)
        songB = models.File(filename="Californication.mp3")
        songB_id = models.Song(file_id=2)
        
        session.add_all([songA, songB, songA_id, songB_id])
        session.commit()
        
        
        response = self.client.get("/api/songs/{}".format(songA.id),
            headers=[("Accept", "application/json")] )
        
        session.delete(songA_id)    
        session.delete(songA)
        session.commit()
        
        response = self.client.get("/api/songs/{}".format(songB.id))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)
        files = session.query(models.File).all()
        self.assertEqual(len(files), 1)
        
        song = json.loads(response.data.decode("ascii"))
        print(song)
        self.assertEqual(song["file"]["filename"], "Californication.mp3")
        
    def test_get_uploaded_file(self):
        path = upload_path("test.txt")
        with open(path, "wb") as f:
            f.write(b"File contents")
        
        response = self.client.get("/uploads/test.txt")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, b"File contents")
        
    def test_file_upload(self):
        data = {"file": (BytesIO(b"File contents"), "test.txt")}
        
        response = self.client.post("/api/files",
            data = data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")
        
        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as f:
            contents = f.read()
        self.assertEqual(contents, b"File contents")