import os
from tuneful import app
from tuneful.database import session
from tuneful import models

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def add_song():
    drones = models.File(filename="Drones.mp3")
    drones_id = models.Song(file_id=1)
    session.add_all([drones, drones_id])
    session.commit()
    
#Test = file = session.query(models.File.filename).filter_by(id=1).first()
#file = session.query(models.File).filter_by(id=1).first()

if __name__ == '__main__':
    run()

