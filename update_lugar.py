from app import create_app, db
from app.models import Partido

app = create_app('development')
with app.app_context():
    partidos = Partido.query.all()
    for p in partidos:
        if not p.lugar:
            p.lugar = 'Estadio de ' + p.equipo_local
    db.session.commit()
    print('OK')
