import os
from dotenv import load_dotenv
from app import create_app, db

# Carga de variables de entorno desde el archivo .env
load_dotenv()

# Seleccion del ambiente (development por defecto)
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    # Creacion inicial de tablas de base de datos en Neon/Supabase si no existen
    with app.app_context():
        try:
            db.create_all()
            print("Tablas de base de datos inicializadas/verificadas con exito en PostgreSQL.")
            
            # Seeding automatico de los 4 usuarios de simulacion Comteco [Willys_IA]
            from app.models import Usuario
            correos_simulacion = {
                'ucarlo@comteco.com.bo': 'Ucarlo Admin',
                'ulfredoc@gmail.com': 'Ulfredoc Jugador 1',
                'ulfredo.carlo@gmail.com': 'Ulfredo Jugador 2',
                'willys@msn.com': 'Willys Jugador 3'
            }
            usuarios_creados = 0
            for email, nombre in correos_simulacion.items():
                if not Usuario.query.filter_by(email=email).first():
                    u = Usuario(nombre=nombre, email=email)
                    u.set_password('comteco123')
                    db.session.add(u)
                    usuarios_creados += 1
            if usuarios_creados > 0:
                db.session.commit()
                print(f"Se crearon {usuarios_creados} nuevos usuarios de simulacion Comteco.")
            else:
                print("Todos los usuarios de simulacion Comteco ya se encuentran registrados.")
                
        except Exception as e:
            print(f"Error al inicializar la base de datos: {str(e)}")
            
    # Ejecucion local de la aplicacion
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
