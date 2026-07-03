from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Partido
from datetime import datetime

app = create_app('development')
with app.app_context():
    # Insertamos todos los partidos reales para que la BD local sea idéntica a la de producción
    nuevos = [
        # --- JUEVES 18 DE JUNIO ---
        Partido(equipo_local='República Checa', equipo_visitante='Sudáfrica', codigo_local='cz', codigo_visitante='za', fecha_hora=datetime(2026, 6, 18, 16, 0), fase='Grupo A', estado='Programado', lugar='Mercedes-Benz Stadium · Atlanta'),
        Partido(equipo_local='Suiza', equipo_visitante='Bosnia y Herzegovina', codigo_local='ch', codigo_visitante='ba', fecha_hora=datetime(2026, 6, 18, 19, 0), fase='Grupo B', estado='Programado', lugar='SoFi Stadium · Los Angeles'),
        Partido(equipo_local='Canadá', equipo_visitante='Catar', codigo_local='ca', codigo_visitante='qa', fecha_hora=datetime(2026, 6, 18, 22, 0), fase='Grupo B', estado='Programado', lugar='BC Place · Vancouver'),
        Partido(equipo_local='México', equipo_visitante='Corea del Sur', codigo_local='mx', codigo_visitante='kr', fecha_hora=datetime(2026, 6, 19, 1, 0), fase='Grupo A', estado='Programado', lugar='Estadio Akron · Guadalajara'),

        # --- VIERNES 19 DE JUNIO ---
        Partido(equipo_local='Estados Unidos', equipo_visitante='Australia', codigo_local='us', codigo_visitante='au', fecha_hora=datetime(2026, 6, 19, 19, 0), fase='Grupo D', estado='Programado', lugar='Lumen Field · Seattle'),
        Partido(equipo_local='Escocia', equipo_visitante='Marruecos', codigo_local='gb', codigo_visitante='ma', fecha_hora=datetime(2026, 6, 19, 22, 0), fase='Grupo C', estado='Programado', lugar='Gillette Stadium · Boston'),
        Partido(equipo_local='Brasil', equipo_visitante='Haití', codigo_local='br', codigo_visitante='ht', fecha_hora=datetime(2026, 6, 20, 0, 30), fase='Grupo C', estado='Programado', lugar='Lincoln Financial Field · Philadelphia'),
        Partido(equipo_local='Turquía', equipo_visitante='Paraguay', codigo_local='tr', codigo_visitante='py', fecha_hora=datetime(2026, 6, 20, 3, 0), fase='Grupo D', estado='Programado', lugar='Levi\'s Stadium · San Francisco Bay Area'),

        # --- SÁBADO 20 DE JUNIO ---
        Partido(equipo_local='Países Bajos', equipo_visitante='Suecia', codigo_local='nl', codigo_visitante='se', fecha_hora=datetime(2026, 6, 20, 17, 0), fase='Grupo F', estado='Programado', lugar='NRG Stadium · Houston'),
        Partido(equipo_local='Alemania', equipo_visitante='Costa de Marfil', codigo_local='de', codigo_visitante='ci', fecha_hora=datetime(2026, 6, 20, 20, 0), fase='Grupo E', estado='Programado', lugar='BMO Field · Toronto'),
        Partido(equipo_local='Ecuador', equipo_visitante='Curazao', codigo_local='ec', codigo_visitante='cw', fecha_hora=datetime(2026, 6, 21, 0, 0), fase='Grupo E', estado='Programado', lugar='Arrowhead Stadium · Kansas City'),

        # --- DOMINGO 21 DE JUNIO ---
        Partido(equipo_local='Túnez', equipo_visitante='Japón', codigo_local='tn', codigo_visitante='jp', fecha_hora=datetime(2026, 6, 21, 4, 0), fase='Grupo F', estado='Programado', lugar='Estadio BBVA · Monterrey'),
        Partido(equipo_local='España', equipo_visitante='Arabia Saudita', codigo_local='es', codigo_visitante='sa', fecha_hora=datetime(2026, 6, 21, 16, 0), fase='Grupo H', estado='Programado', lugar='Mercedes-Benz Stadium · Atlanta'),
        Partido(equipo_local='Bélgica', equipo_visitante='Irán', codigo_local='be', codigo_visitante='ir', fecha_hora=datetime(2026, 6, 21, 19, 0), fase='Grupo G', estado='Programado', lugar='SoFi Stadium · Los Angeles'),
        Partido(equipo_local='Uruguay', equipo_visitante='Cabo Verde', codigo_local='uy', codigo_visitante='cv', fecha_hora=datetime(2026, 6, 21, 22, 0), fase='Grupo H', estado='Programado', lugar='Hard Rock Stadium · Miami'),

        # --- MIÉRCOLES 24 DE JUNIO ---
        Partido(equipo_local='Suiza', equipo_visitante='Canadá', codigo_local='ch', codigo_visitante='ca', fecha_hora=datetime(2026, 6, 24, 19, 0), fase='Grupo B', estado='Programado', lugar='BC Place · Vancouver'),
        Partido(equipo_local='Bosnia y Herzegovina', equipo_visitante='Catar', codigo_local='ba', codigo_visitante='qa', fecha_hora=datetime(2026, 6, 24, 19, 0), fase='Grupo B', estado='Programado', lugar='Lumen Field · Seattle'),
        Partido(equipo_local='Escocia', equipo_visitante='Brasil', codigo_local='gb', codigo_visitante='br', fecha_hora=datetime(2026, 6, 24, 22, 0), fase='Grupo C', estado='Programado', lugar='Hard Rock Stadium · Miami'),
        Partido(equipo_local='Marruecos', equipo_visitante='Haití', codigo_local='ma', codigo_visitante='ht', fecha_hora=datetime(2026, 6, 24, 22, 0), fase='Grupo C', estado='Programado', lugar='Mercedes-Benz Stadium · Atlanta'),
        Partido(equipo_local='República Checa', equipo_visitante='México', codigo_local='cz', codigo_visitante='mx', fecha_hora=datetime(2026, 6, 25, 1, 0), fase='Grupo A', estado='Programado', lugar='Estadio Azteca · Mexico City'),
        Partido(equipo_local='Sudáfrica', equipo_visitante='Corea del Sur', codigo_local='za', codigo_visitante='kr', fecha_hora=datetime(2026, 6, 25, 1, 0), fase='Grupo A', estado='Programado', lugar='Estadio BBVA · Monterrey'),

        # --- JUEVES 25 DE JUNIO ---
        Partido(equipo_local='Ecuador', equipo_visitante='Alemania', codigo_local='ec', codigo_visitante='de', fecha_hora=datetime(2026, 6, 25, 20, 0), fase='Grupo E', estado='Programado', lugar='MetLife Stadium · New York New Jersey'),
        Partido(equipo_local='Curazao', equipo_visitante='Costa de Marfil', codigo_local='cw', codigo_visitante='ci', fecha_hora=datetime(2026, 6, 25, 20, 0), fase='Grupo E', estado='Programado', lugar='Lincoln Financial Field · Philadelphia'),
        Partido(equipo_local='Túnez', equipo_visitante='Países Bajos', codigo_local='tn', codigo_visitante='nl', fecha_hora=datetime(2026, 6, 25, 23, 0), fase='Grupo F', estado='Programado', lugar='Arrowhead Stadium · Kansas City'),
        Partido(equipo_local='Japón', equipo_visitante='Suecia', codigo_local='jp', codigo_visitante='se', fecha_hora=datetime(2026, 6, 25, 23, 0), fase='Grupo F', estado='Programado', lugar='AT&T Stadium · Dallas'),
        Partido(equipo_local='Paraguay', equipo_visitante='Australia', codigo_local='py', codigo_visitante='au', fecha_hora=datetime(2026, 6, 26, 2, 0), fase='Grupo D', estado='Programado', lugar='Levi\'s Stadium · San Francisco Bay Area'),
        Partido(equipo_local='Turquía', equipo_visitante='Estados Unidos', codigo_local='tr', codigo_visitante='us', fecha_hora=datetime(2026, 6, 26, 2, 0), fase='Grupo D', estado='Programado', lugar='SoFi Stadium · Los Angeles'),

        # --- VIERNES 26 DE JUNIO ---
        Partido(equipo_local='Noruega', equipo_visitante='Francia', codigo_local='no', codigo_visitante='fr', fecha_hora=datetime(2026, 6, 26, 19, 0), fase='Grupo I', estado='Programado', lugar='Gillette Stadium · Boston'),
        Partido(equipo_local='Senegal', equipo_visitante='Irak', codigo_local='sn', codigo_visitante='iq', fecha_hora=datetime(2026, 6, 26, 19, 0), fase='Grupo I', estado='Programado', lugar='BMO Field · Toronto'),
        Partido(equipo_local='Uruguay', equipo_visitante='España', codigo_local='uy', codigo_visitante='es', fecha_hora=datetime(2026, 6, 27, 0, 0), fase='Grupo H', estado='Programado', lugar='Estadio Akron · Guadalajara'),
        Partido(equipo_local='Cabo Verde', equipo_visitante='Arabia Saudita', codigo_local='cv', codigo_visitante='sa', fecha_hora=datetime(2026, 6, 27, 0, 0), fase='Grupo H', estado='Programado', lugar='NRG Stadium · Houston'),
        Partido(equipo_local='Nueva Zelanda', equipo_visitante='Bélgica', codigo_local='nz', codigo_visitante='be', fecha_hora=datetime(2026, 6, 27, 3, 0), fase='Grupo G', estado='Programado', lugar='BC Place · Vancouver'),
        Partido(equipo_local='Egipto', equipo_visitante='Irán', codigo_local='eg', codigo_visitante='ir', fecha_hora=datetime(2026, 6, 27, 3, 0), fase='Grupo G', estado='Programado', lugar='Lumen Field · Seattle'),

        # --- VIERNES 3 DE JULIO ---
        Partido(equipo_local='Australia', equipo_visitante='Egipto', codigo_local='au', codigo_visitante='eg', fecha_hora=datetime(2026, 7, 3, 18, 0), fase='Grupo D', estado='Programado', lugar='AT&T Stadium · Dallas'),
        Partido(equipo_local='Argentina', equipo_visitante='Cabo Verde', codigo_local='ar', codigo_visitante='cv', fecha_hora=datetime(2026, 7, 3, 22, 0), fase='Grupo J', estado='Programado', lugar='Hard Rock Stadium · Miami'),
        Partido(equipo_local='Colombia', equipo_visitante='Ghana', codigo_local='co', codigo_visitante='gh', fecha_hora=datetime(2026, 7, 4, 1, 30), fase='Grupo K', estado='Programado', lugar='Arrowhead Stadium · Kansas City'),

        # --- SÁBADO 4 DE JULIO ---
        Partido(equipo_local='Canadá', equipo_visitante='Marruecos', codigo_local='ca', codigo_visitante='ma', fecha_hora=datetime(2026, 7, 4, 17, 0), fase='Grupo B', estado='Programado', lugar='NRG Stadium · Houston'),
        Partido(equipo_local='Paraguay', equipo_visitante='Francia', codigo_local='py', codigo_visitante='fr', fecha_hora=datetime(2026, 7, 4, 21, 0), fase='Grupo D', estado='Programado', lugar='Lincoln Financial Field · Philadelphia'),

        # --- DOMINGO 5 DE JULIO ---
        Partido(equipo_local='Brasil', equipo_visitante='Noruega', codigo_local='br', codigo_visitante='no', fecha_hora=datetime(2026, 7, 5, 20, 0), fase='Grupo C', estado='Programado', lugar='MetLife Stadium'),
        Partido(equipo_local='México', equipo_visitante='Inglaterra', codigo_local='mx', codigo_visitante='gb', fecha_hora=datetime(2026, 7, 6, 0, 0), fase='Grupo A', estado='Programado', lugar='Estadio Banorte · Mexico City'),
    ]

    insertados = 0
    for p in nuevos:
        existe = Partido.query.filter_by(equipo_local=p.equipo_local, equipo_visitante=p.equipo_visitante).first()
        if not existe:
            db.session.add(p)
            insertados += 1

    if insertados > 0:
        db.session.commit()
        print(f"¡{insertados} partidos cargados exitosamente en la BD local!")
    else:
        print("Los partidos ya estaban registrados localmente.")
