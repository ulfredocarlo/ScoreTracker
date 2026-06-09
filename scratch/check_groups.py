import sys
import os

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Grupo

app = create_app('development')
with app.app_context():
    try:
        grupos = Grupo.query.all()
        print("--- GRUPOS EN BASE DE DATOS ---")
        for g in grupos:
            print(f"ID: {g.id} | Nombre: {g.nombre} | Codigo: {g.codigo_invitacion}")
        print("-------------------------------")
    except Exception as e:
        print("Error al consultar grupos:", str(e))
