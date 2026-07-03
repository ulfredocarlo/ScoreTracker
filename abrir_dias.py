import os
import sys

# Forzar encoding para evitar problemas en Windows con psycopg2
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import create_app, db
from app.models import Partido

def abrir_siguientes_dias(dias=4):
    app = create_app('production')
    app.app_context().push()
    
    try:
        # Obtener todos los partidos en estado 'Programado' ordenados por fecha
        partidos_programados = Partido.query.filter_by(estado='Programado').order_by(Partido.fecha_hora.asc()).all()
        
        if not partidos_programados:
            print("No hay partidos programados para abrir.")
            return

        # Encontrar las proximas N fechas unicas
        fechas_unicas = set()
        fechas_a_abrir = []
        
        for p in partidos_programados:
            fecha_dia = p.fecha_hora.date()
            if fecha_dia not in fechas_unicas:
                fechas_unicas.add(fecha_dia)
                fechas_a_abrir.append(fecha_dia)
            if len(fechas_a_abrir) >= dias:
                break
                
        print(f"Fechas a abrir: {fechas_a_abrir}")
        
        # Abrir partidos que coincidan con esas fechas
        partidos_abiertos = 0
        for p in partidos_programados:
            if p.fecha_hora.date() in fechas_a_abrir:
                p.estado = 'Abierto'
                partidos_abiertos += 1
                print(f"Abriendo partido: {p.equipo_local} vs {p.equipo_visitante} ({p.fecha_hora})")
                
        db.session.commit()
        print(f"\nExito: Se han abierto {partidos_abiertos} partidos correspondientes a los siguientes {dias} dias con partidos programados.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al abrir partidos: {str(e)}")

if __name__ == '__main__':
    abrir_siguientes_dias()
