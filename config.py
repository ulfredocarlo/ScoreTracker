import os
from datetime import timedelta

class Config:
    """Configuracion base de la aplicacion ScoreTracker. [Willys_IA]"""
    # Clave secreta para sesiones y seguridad CSRF
    SECRET_KEY = os.getenv('SECRET_KEY', 'willys-ia-secure-mvp-secret-key-2026')
    
    # URI de Base de Datos - Soporta PostgreSQL (Neon/Supabase)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/score_tracker'
    )
    # Evita advertencias de rendimiento innecesarias de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Politica de Seguridad de Cookies de Sesion
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=15)
    
    # Credenciales de Autenticacion Google OAuth 2.0 [Willys_IA]
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # QR e Informacion del Administrador Global de la App para comisiones
    APP_ADMIN_QR_URL = os.getenv('APP_ADMIN_QR_URL', '')
    APP_ADMIN_TELEFONO = os.getenv('APP_ADMIN_TELEFONO', '+59100000000')
    APP_ADMIN_CUENTA = os.getenv('APP_ADMIN_CUENTA', 'Banco Union - Cta: 100000000')

class DevelopmentConfig(Config):
    """Configuracion especifica para ambiente de desarrollo local. [Willys_IA]"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Permite HTTP en entorno local

class ProductionConfig(Config):
    """Configuracion especifica para ambiente de produccion (Render). [Willys_IA]"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True   # Obliga el uso de HTTPS en produccion

class TestingConfig(Config):
    """Configuracion especifica para pruebas unitarias en memoria. [Willys_IA]"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False  # Permite HTTP en entorno local

# Mapeo de perfiles de ejecucion
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

