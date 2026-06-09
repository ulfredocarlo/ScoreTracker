import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Usuario
from seed_data import cargar_partidos_semilla

def reset_database():
    """
    Elimina todas las tablas e historiales de PostgreSQL local, las vuelve a crear vacías,
    y carga el fixture oficial de partidos junto con los 4 usuarios específicos de pruebas. [Willys_IA]
    """
    app = create_app('development')
    
    with app.app_context():
        print("[Willys_IA] Iniciando purga completa de PostgreSQL local...")
        
        # Eliminar todas las tablas existentes en orden de dependencia
        db.drop_all()
        print("[Willys_IA] Tablas eliminadas con éxito.")
        
        # Volver a crear todas las tablas en base a los modelos actuales
        db.create_all()
        print("[Willys_IA] Estructura relacional recreada exitosamente.")
        
        # === 3. SEMBRAR USUARIOS DE PRUEBAS COMTECO ===
        print("[Willys_IA] Sembrando los 4 usuarios de simulación Comteco...")
        
        correos_simulacion = {
            'ucarlo@comteco.com.bo': 'Ucarlo Admin',
            'ulfredoc@gmail.com': 'Ulfredoc Jugador 1',
            'ulfredo.carlo@gmail.com': 'Ulfredo Jugador 2',
            'willys@msn.com': 'Willys Jugador 3'
        }
        
        try:
            for email, nombre in correos_simulacion.items():
                u = Usuario(nombre=nombre, email=email)
                u.set_password('comteco123')
                db.session.add(u)
            db.session.commit()
            print("[Willys_IA] Los 4 usuarios de simulación sembrados con contraseña única 'comteco123'.")
        except Exception as e:
            db.session.rollback()
            print(f"[Willys_IA] Error al sembrar usuarios: {str(e)}")
        
    # Cargar fixture semilla de partidos para habilitar el juego
    print("[Willys_IA] Cargando partidos semilla oficiales del Mundial y Amistosos...")
    cargar_partidos_semilla()
    
    print("[Willys_IA] ¡Base de datos purgada, sembrada y lista para pruebas reales!")

if __name__ == '__main__':
    reset_database()
