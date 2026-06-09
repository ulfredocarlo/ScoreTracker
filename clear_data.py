import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Grupo, ParticipanteGrupo, Prediccion, PartidoParticipanteCaja, LiquidacionHistorial, ComisionHistorial

app = create_app(os.getenv('FLASK_ENV', 'development'))
with app.app_context():
    print("Limpiando datos de juego...")
    db.session.query(LiquidacionHistorial).delete()
    db.session.query(ComisionHistorial).delete()
    db.session.query(PartidoParticipanteCaja).delete()
    db.session.query(Prediccion).delete()
    db.session.query(ParticipanteGrupo).delete()
    db.session.query(Grupo).delete()
    db.session.commit()
    print("Datos de jugadores y grupos limpiados exitosamente. (Usuarios y Partidos mantenidos).")
