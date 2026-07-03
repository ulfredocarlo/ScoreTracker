import os
from datetime import datetime
from app import create_app, db
from app.models import Partido

def agregar_partidos():
    app = create_app('production')
    with app.app_context():
        # Lista de partidos a insertar. [Willys_IA]
        # Formato: (Local, Visitante, cod_local, cod_visitante, Año, Mes, Dia, Hora, Minuto, Fase)
        # La hora debe ser en UTC (hora local de Bolivia + 4 horas aprox, dependiendo tu zona)
        partidos_nuevos = [
            ("Corea del Sur", "Republica Checa", "kr", "cz", 2026, 6, 11, 21, 0, "Grupo A - Fecha 1"),
            # Agrega más partidos aquí abajo copiando el formato de arriba:
            # ("Equipo A", "Equipo B", "codA", "codB", 2026, 6, 12, 15, 0, "Grupo X - Fecha 1"),
        ]

        insertados = 0
        for local, visitante, cod_l, cod_v, y, m, d, h, min, fase in partidos_nuevos:
            fecha = datetime(y, m, d, h, min)
            
            # Validar que no exista ya para evitar duplicados
            existe = Partido.query.filter_by(equipo_local=local, equipo_visitante=visitante).first()
            if not existe:
                p = Partido(
                    equipo_local=local,
                    equipo_visitante=visitante,
                    codigo_local=cod_l,
                    codigo_visitante=cod_v,
                    fecha_hora=fecha,
                    fase=fase,
                    estado="Programado"  # Se abrirá automáticamente si falta poco
                )
                db.session.add(p)
                insertados += 1
                print(f"[+] Preparado para insertar: {local} vs {visitante}")
            else:
                print(f"[-] Omitido (Ya existe): {local} vs {visitante}")

        if insertados > 0:
            try:
                db.session.commit()
                print(f"\n¡Éxito! Se inyectaron {insertados} partidos nuevos a la base de datos de producción.")
            except Exception as e:
                db.session.rollback()
                print(f"Error al guardar en BD: {str(e)}")
        else:
            print("\nNo se insertó ningún partido nuevo (ya existían todos los de la lista).")

if __name__ == '__main__':
    agregar_partidos()
