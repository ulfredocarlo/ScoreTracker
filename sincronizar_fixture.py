import sys
import os

# Esto se ejecutara dentro de Docker, el contexto de Flask estara disponible
from app import create_app, db
from app.models import Partido
from datetime import datetime

def sincronizar_fixture():
    app = create_app('production')
    app.app_context().push()

    try:
        print("Iniciando sincronización del Fixture Oficial...")

        # 1. COREA DEL SUR VS REP CHECA (Actualizar hora a 22:00 Bolivia = 02:00 UTC del día siguiente)
        corea = Partido.query.filter_by(codigo_local='kr', codigo_visitante='cz').first()
        if corea:
            corea.fecha_hora = datetime(2026, 6, 12, 2, 0) # 02:00 UTC = 22:00 Bolivia (Jueves 11)
            print("✔ Corea del Sur vs Rep Checa actualizado a las 22:00")

        # 2. ESPAÑA VS NIGERIA -> CANADÁ VS BOSNIA (15:00 Bolivia = 19:00 UTC)
        dummy1 = Partido.query.filter_by(equipo_local='Espana').first()
        if dummy1:
            dummy1.equipo_local = 'Canada'
            dummy1.equipo_visitante = 'Bosnia'
            dummy1.codigo_local = 'ca'
            dummy1.codigo_visitante = 'ba'
            dummy1.fecha_hora = datetime(2026, 6, 12, 19, 0)
            dummy1.fase = 'Grupo B'
            print("✔ España vs Nigeria reciclado a Canadá vs Bosnia")

        # 3. INGLATERRA VS USA -> ESTADOS UNIDOS VS PARAGUAY (21:00 Bolivia = 01:00 UTC del Sábado)
        dummy2 = Partido.query.filter_by(equipo_local='Inglaterra').first()
        if dummy2:
            dummy2.equipo_local = 'Estados Unidos'
            dummy2.equipo_visitante = 'Paraguay'
            dummy2.codigo_local = 'us'
            dummy2.codigo_visitante = 'py'
            dummy2.fecha_hora = datetime(2026, 6, 13, 1, 0)
            dummy2.fase = 'Grupo D'
            print("✔ Inglaterra vs USA reciclado a Estados Unidos vs Paraguay")

        # 4. ALEMANIA VS JAPON -> QATAR VS SUIZA (15:00 Bolivia = 19:00 UTC Sábado)
        dummy3 = Partido.query.filter_by(equipo_local='Alemania', equipo_visitante='Japon').first()
        if dummy3:
            dummy3.equipo_local = 'Qatar'
            dummy3.equipo_visitante = 'Suiza'
            dummy3.codigo_local = 'qa'
            dummy3.codigo_visitante = 'ch'
            dummy3.fecha_hora = datetime(2026, 6, 13, 19, 0)
            dummy3.fase = 'Grupo B'
            print("✔ Alemania vs Japón reciclado a Qatar vs Suiza")

        # 5. INSERTAR LOS FALTANTES DEL SÁBADO Y DOMINGO
        nuevos_partidos = [
            # Sábado 13
            Partido(equipo_local='Brasil', equipo_visitante='Marruecos', codigo_local='br', codigo_visitante='ma', fecha_hora=datetime(2026, 6, 13, 22, 0), fase='Grupo C', estado='Programado', lugar='Nueva York/Nueva Jersey'), # 18:00 Bolivia
            Partido(equipo_local='Haiti', equipo_visitante='Escocia', codigo_local='ht', codigo_visitante='gb-sct', fecha_hora=datetime(2026, 6, 14, 1, 0), fase='Grupo C', estado='Programado', lugar='Boston'), # 21:00 Bolivia
            
            # Domingo 14
            Partido(equipo_local='Australia', equipo_visitante='Turquia', codigo_local='au', codigo_visitante='tr', fecha_hora=datetime(2026, 6, 14, 4, 0), fase='Grupo D', estado='Programado', lugar='Vancouver'), # 00:00 Bolivia
            Partido(equipo_local='Alemania', equipo_visitante='Curazao', codigo_local='de', codigo_visitante='cw', fecha_hora=datetime(2026, 6, 14, 17, 0), fase='Grupo E', estado='Programado', lugar='Houston'), # 13:00 Bolivia
            Partido(equipo_local='Paises Bajos', equipo_visitante='Japon', codigo_local='nl', codigo_visitante='jp', fecha_hora=datetime(2026, 6, 14, 20, 0), fase='Grupo F', estado='Programado', lugar='Dallas'), # 16:00 Bolivia
            Partido(equipo_local='Costa de Marfil', equipo_visitante='Ecuador', codigo_local='ci', codigo_visitante='ec', fecha_hora=datetime(2026, 6, 14, 23, 0), fase='Grupo E', estado='Programado', lugar='Filadelfia'), # 19:00 Bolivia
            Partido(equipo_local='Suecia', equipo_visitante='Tunez', codigo_local='se', codigo_visitante='tn', fecha_hora=datetime(2026, 6, 15, 2, 0), fase='Grupo F', estado='Programado', lugar='Monterrey'), # 22:00 Bolivia
            
            # Lunes 15 (Continuación)
            Partido(equipo_local='Francia', equipo_visitante='Croacia', codigo_local='fr', codigo_visitante='hr', fecha_hora=datetime(2026, 6, 15, 16, 0), fase='Grupo G', estado='Programado', lugar='Los Angeles'), # 12:00 Bolivia
            Partido(equipo_local='Inglaterra', equipo_visitante='Uruguay', codigo_local='gb-eng', codigo_visitante='uy', fecha_hora=datetime(2026, 6, 15, 20, 0), fase='Grupo H', estado='Programado', lugar='Toronto'), # 16:00 Bolivia
            
            # Martes 16
            Partido(equipo_local='Italia', equipo_visitante='Senegal', codigo_local='it', codigo_visitante='sn', fecha_hora=datetime(2026, 6, 16, 17, 0), fase='Grupo A', estado='Programado', lugar='Atlanta'), # 13:00 Bolivia
            Partido(equipo_local='Portugal', equipo_visitante='Colombia', codigo_local='pt', codigo_visitante='co', fecha_hora=datetime(2026, 6, 16, 22, 0), fase='Grupo B', estado='Programado', lugar='Miami'), # 18:00 Bolivia

            # Miércoles 17
            Partido(equipo_local='Espana', equipo_visitante='Nigeria', codigo_local='es', codigo_visitante='ng', fecha_hora=datetime(2026, 6, 17, 16, 0), fase='Grupo C', estado='Programado', lugar='Seattle'), # 12:00 Bolivia
            Partido(equipo_local='Belgica', equipo_visitante='Japon', codigo_local='be', codigo_visitante='jp', fecha_hora=datetime(2026, 6, 17, 21, 0), fase='Grupo D', estado='Programado', lugar='San Francisco'), # 17:00 Bolivia

            # Jueves 18
            Partido(equipo_local='Argentina', equipo_visitante='Gales', codigo_local='ar', codigo_visitante='gb-wls', fecha_hora=datetime(2026, 6, 18, 17, 0), fase='Grupo E', estado='Programado', lugar='Houston'), # 13:00 Bolivia
            Partido(equipo_local='Brasil', equipo_visitante='Suiza', codigo_local='br', codigo_visitante='ch', fecha_hora=datetime(2026, 6, 18, 22, 0), fase='Grupo F', estado='Programado', lugar='Nueva York'), # 18:00 Bolivia
        ]

        # Validamos que no existan duplicados antes de insertar (por seguridad de re-ejecucion)
        for p in nuevos_partidos:
            existe = Partido.query.filter_by(equipo_local=p.equipo_local, equipo_visitante=p.equipo_visitante).first()
            if not existe:
                db.session.add(p)
                print(f"✔ Insertado nuevo partido: {p.equipo_local} vs {p.equipo_visitante}")

        db.session.commit()
        print("==================================================")
        print("¡ÉXITO TOTAL! EL FIXTURE HA SIDO SINCRONIZADO")
        print("==================================================")

    except Exception as e:
        db.session.rollback()
        print(f"ERROR DURANTE LA SINCRONIZACIÓN: {str(e)}")

if __name__ == '__main__':
    sincronizar_fixture()
