from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv() # Cargar variables de entorno del archivo .env

from app import create_app, db
from app.models import Partido

def cargar_partidos_semilla():
    """
    Carga partidos reales de prueba para el fixture del Mundial 2026 en PostgreSQL. [Willys_IA]
    Permite probar el ciclo de predicciones, conciliaciones y liquidaciones de inmediato.
    """
    app = create_app('development')
    
    with app.app_context():
        # Validar si ya existen partidos cargados para no duplicar datos
        partidos_existentes = Partido.query.count()
        if partidos_existentes > 0:
            print("El fixture ya contiene partidos de prueba. Omitiendo semilla.")
            return
            
        print("Cargando fixture de prueba del Mundial 2026 en PostgreSQL...")
        
        # === 1. PARTIDOS DE PREPARACIÓN (AMISTOSOS PRE-MUNDIAL) ===
        # México vs Serbia (4 de Junio 2026 - Toluca, México)
        partido1 = Partido(
            equipo_local="Mexico",
            equipo_visitante="Serbia",
            codigo_local="mx",
            codigo_visitante="rs",
            fecha_hora=datetime(2026, 6, 4, 20, 0), # 20:00 UTC
            fase="Amistoso de Preparacion",
            estado="Abierto"
        )
        
        # Argentina vs Islandia (9 de Junio 2026 - Alabama, EE.UU.)
        partido2 = Partido(
            equipo_local="Argentina",
            equipo_visitante="Islandia",
            codigo_local="ar",
            codigo_visitante="is",
            fecha_hora=datetime(2026, 6, 9, 19, 0), # 19:00 UTC
            fase="Amistoso de Preparacion",
            estado="Abierto"
        )
        
        # === 2. PARTIDOS DE FASE DE GRUPOS OFICIALES FIFA MUNDIAL 2026 ===
        # México vs Sudáfrica (Partido Inaugural del Mundial - 11 de Junio 2026 - Estadio Azteca)
        partido3 = Partido(
            equipo_local="Mexico",
            equipo_visitante="Sudafrica",
            codigo_local="mx",
            codigo_visitante="za",
            fecha_hora=datetime(2026, 6, 11, 18, 0), # 18:00 UTC (Inaugural)
            fase="Grupo A - Fecha 1",
            estado="Abierto"
        )
        
        # Canadá vs Bosnia y Herzegovina (12 de Junio 2026 - Toronto Stadium)
        partido4 = Partido(
            equipo_local="Canada",
            equipo_visitante="Bosnia",
            codigo_local="ca",
            codigo_visitante="ba",
            fecha_hora=datetime(2026, 6, 12, 16, 0), # 16:00 UTC
            fase="Grupo B - Fecha 1",
            estado="Programado"
        )
        
        # Estados Unidos vs Paraguay (12 de Junio 2026 - Los Angeles Stadium)
        partido5 = Partido(
            equipo_local="Estados Unidos",
            equipo_visitante="Paraguay",
            codigo_local="us",
            codigo_visitante="py",
            fecha_hora=datetime(2026, 6, 12, 21, 0), # 21:00 UTC
            fase="Grupo D - Fecha 1",
            estado="Programado"
        )
        
        # Brasil vs Marruecos (13 de Junio 2026 - New York/New Jersey Stadium)
        partido6 = Partido(
            equipo_local="Brasil",
            equipo_visitante="Marruecos",
            codigo_local="br",
            codigo_visitante="ma",
            fecha_hora=datetime(2026, 6, 13, 19, 0), # 19:00 UTC
            fase="Grupo C - Fecha 1",
            estado="Programado"
        )
        
        db.session.add_all([partido1, partido2, partido3, partido4, partido5, partido6])
        
        try:
            db.session.commit()
            print("¡Fixture de prueba del Mundial 2026 cargado con exito en PostgreSQL!")
        except Exception as e:
            db.session.rollback()
            print(f"Error al cargar la semilla de partidos: {str(e)}")

if __name__ == '__main__':
    cargar_partidos_semilla()
