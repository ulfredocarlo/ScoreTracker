import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from app.models import Partido

def insertar_faltante():
    app = create_app('development')
    with app.app_context():
        # Verificar si ya existe para evitar duplicados
        existe = Partido.query.filter_by(equipo_local="Corea del Sur", equipo_visitante="Republica Checa").first()
        if existe:
            print("El partido ya existe en la base de datos.")
            return

        print("Insertando el segundo partido del 11 de Junio...")
        partido = Partido(
            equipo_local="Corea del Sur",
            equipo_visitante="Republica Checa",
            codigo_local="kr",
            codigo_visitante="cz",
            fecha_hora=datetime(2026, 6, 11, 21, 0), # 21:00 UTC
            fase="Grupo A - Fecha 1",
            estado="Programado"
        )
        db.session.add(partido)
        
        try:
            db.session.commit()
            print("¡Partido insertado exitosamente!")
        except Exception as e:
            db.session.rollback()
            print(f"Error al insertar el partido: {e}")

if __name__ == '__main__':
    insertar_faltante()
