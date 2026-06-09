# GUÍA TÉCNICA DE DESARROLLO
## Apuestas Mundial 2026 - Sistema Flask

---

## 1. CONFIGURACIÓN INICIAL

### 1.1 Stack requerido
```bash
Python 3.9+
PostgreSQL 12+
pip
virtualenv
```

### 1.2 Instalación rápida
```bash
# Crear proyecto
mkdir apuestas-mundial && cd apuestas-mundial

# Entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Dependencias
pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug python-dotenv

# Versiones específicas (importante para estabilidad)
pip install Flask==2.3.2 Flask-SQLAlchemy==3.0.5 Flask-Login==0.6.2

# PostgreSQL driver
pip install psycopg2-binary

# Guardar
pip freeze > requirements.txt
```

---

## 2. ESTRUCTURA DEL PROYECTO

```
apuestas-mundial/
│
├── app/
│   ├── __init__.py          (Factory pattern)
│   ├── models.py            (Todas las tablas/relaciones BD)
│   ├── routes.py            (Todas las rutas HTTP)
│   ├── logic.py             (Lógica de liquidación, cálculos)
│   ├── auth.py              (Manejo de autenticación)
│   │
│   └── templates/
│       ├── base.html        (Layout base)
│       ├── login.html
│       ├── registro.html
│       ├── dashboard.html   (Panel principal)
│       ├── grupo.html       (Detalle grupo)
│       ├── partido.html     (Apuestas del partido)
│       ├── resultados.html  (Cargar resultados)
│       └── historial.html   (Historial de apuestas)
│
├── config.py                (Configuraciones por ambiente)
├── run.py                   (Punto de entrada)
├── .env                     (Variables de entorno - NO EN GIT)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 3. ARCHIVO DE CONFIGURACIÓN (config.py)

```python
import os
from datetime import timedelta

class Config:
    """Configuración base"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/apuestas_mundial')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    
    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    """Desarrollo (local)"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # HTTP local

class ProductionConfig(Config):
    """Producción"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

---

## 4. MODELOS (models.py)

```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

# ============ ENUMS ============
class EstadoGrupo(str, Enum):
    ACTIVO = "Activo"
    FINALIZADO = "Finalizado"

class EstadoPartido(str, Enum):
    ABIERTO = "Abierto"
    CERRADO = "Cerrado"
    LIQUIDADO = "Liquidado"

class EstadoPago(str, Enum):
    PAGO = "Pagó"
    NO_PAGO = "No Pagó"
    PENDIENTE = "Pendiente"

class TipoJuego(str, Enum):
    RESULTADO = "Resultado"
    MARCADOR = "Marcador"

class EstadoParticipante(str, Enum):
    ACTIVO = "Activo"
    EXCLUIDO = "Excluido"

# ============ TABLAS ============

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    grupos_admin_primario = db.relationship('Grupo', backref='admin_primario', foreign_keys='Grupo.admin_primario_id')
    grupos_admin_secundario = db.relationship('Grupo', backref='admin_secundario', foreign_keys='Grupo.admin_secundario_id')
    participaciones = db.relationship('ParticipanteGrupo', backref='usuario')
    apuestas = db.relationship('Apuesta', backref='usuario')
    
    def set_password(self, password):
        self.contraseña = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.contraseña, password)

class Grupo(db.Model):
    __tablename__ = 'grupos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    
    admin_primario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    admin_secundario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    monto_por_apuesta = db.Column(db.Numeric(10, 2), nullable=False)
    tipo_juego = db.Column(db.Enum(TipoJuego), nullable=False)
    porcentaje_comision = db.Column(db.Numeric(5, 2), default=2.00)
    
    responsable_pagos_qr = db.Column(db.String(500))  # URL o datos del QR
    responsable_pagos_telefono = db.Column(db.String(20))
    responsable_pagos_cuenta = db.Column(db.String(255))
    
    estado = db.Column(db.Enum(EstadoGrupo), default=EstadoGrupo.ACTIVO)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    participantes = db.relationship('ParticipanteGrupo', backref='grupo', cascade='all, delete-orphan')
    partidos = db.relationship('Partido', backref='grupo', cascade='all, delete-orphan')

class ParticipanteGrupo(db.Model):
    __tablename__ = 'participantes_grupo'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    estado = db.Column(db.Enum(EstadoParticipante), default=EstadoParticipante.ACTIVO)
    balance_acumulado = db.Column(db.Numeric(15, 2), default=0.00)
    fecha_union = db.Column(db.DateTime, default=datetime.utcnow)

class Partido(db.Model):
    __tablename__ = 'partidos'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    
    equipo_local = db.Column(db.String(255), nullable=False)
    equipo_visitante = db.Column(db.String(255), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    fase = db.Column(db.String(100))  # 'Grupos', 'Octavos', 'Cuartos', etc.
    
    estado = db.Column(db.Enum(EstadoPartido), default=EstadoPartido.ABIERTO)
    marcador = db.Column(db.String(10))  # Ej: '2-1'
    
    total_recaudado = db.Column(db.Numeric(15, 2), default=0.00)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    apuestas = db.relationship('Apuesta', backref='partido', cascade='all, delete-orphan')
    pagos = db.relationship('PartidoParticipante', backref='partido', cascade='all, delete-orphan')

class Apuesta(db.Model):
    __tablename__ = 'apuestas'
    
    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    prediccion = db.Column(db.String(100), nullable=False)  # Ej: 'Local gana', '2-1'
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class PartidoParticipante(db.Model):
    """Control de quién pagó en cada partido"""
    __tablename__ = 'partido_participante'
    
    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    estado_pago = db.Column(db.Enum(EstadoPago), default=EstadoPago.PENDIENTE)
    marcado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # Admin que marcó
    fecha_marcado = db.Column(db.DateTime)

class LiquidacionHistorial(db.Model):
    """Registro de cada liquidación"""
    __tablename__ = 'liquidacion_historial'
    
    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    monto_apostado = db.Column(db.Numeric(10, 2), nullable=False)
    gano = db.Column(db.Boolean, nullable=False)
    ganancia_neta = db.Column(db.Numeric(15, 2))  # Puede ser negativa
    
    fecha_liquidacion = db.Column(db.DateTime, default=datetime.utcnow)

class ComisionHistorial(db.Model):
    """Registro de comisiones por grupo"""
    __tablename__ = 'comision_historial'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    estado_pago = db.Column(db.Enum(EstadoPago), default=EstadoPago.PENDIENTE)
    qr_generado = db.Column(db.String(500))  # URL del QR
    
    fecha_liquidacion = db.Column(db.DateTime)
```

---

## 5. LÓGICA DE NEGOCIO (logic.py)

```python
from decimal import Decimal
from models import (
    Apuesta, Partido, PartidoParticipante, LiquidacionHistorial, 
    ComisionHistorial, ParticipanteGrupo, EstadoPago, EstadoPartido
)
from db import db

def liquidar_partido(partido_id):
    """
    Lógica principal de liquidación.
    
    Pasos:
    1. Obtener todos los que apostaron y pagaron
    2. Calcular total recaudado
    3. Calcular comisión
    4. Identificar ganadores
    5. Distribuir proporcionalmente
    6. Registrar en historial
    """
    
    try:
        partido = Partido.query.get(partido_id)
        if not partido or not partido.marcador:
            raise ValueError("Partido no existe o no tiene resultado")
        
        # 1. Obtener apuestas válidas (de usuarios que pagaron)
        apuestas_validas = db.session.query(Apuesta).join(
            PartidoParticipante,
            (Apuesta.usuario_id == PartidoParticipante.usuario_id) & 
            (Apuesta.partido_id == PartidoParticipante.partido_id)
        ).filter(
            Apuesta.partido_id == partido_id,
            PartidoParticipante.estado_pago == EstadoPago.PAGO
        ).all()
        
        if not apuestas_validas:
            raise ValueError("No hay apuestas válidas para este partido")
        
        # 2. Calcular totales
        total_recaudado = sum(Decimal(a.monto) for a in apuestas_validas)
        comision = total_recaudado * (Decimal(partido.grupo.porcentaje_comision) / Decimal(100))
        a_distribuir = total_recaudado - comision
        
        # 3. Determinar ganadores (según tipo de juego)
        ganadores = determinar_ganadores(apuestas_validas, partido)
        
        # 4. Distribuir
        if ganadores:
            total_apostado_ganadores = sum(Decimal(a.monto) for a in ganadores)
            
            for apuesta in ganadores:
                proporcion = Decimal(apuesta.monto) / total_apostado_ganadores
                ganancia = a_distribuir * proporcion
                
                # Registrar
                liqui = LiquidacionHistorial(
                    partido_id=partido_id,
                    usuario_id=apuesta.usuario_id,
                    monto_apostado=apuesta.monto,
                    gano=True,
                    ganancia_neta=ganancia
                )
                db.session.add(liqui)
                
                # Actualizar balance
                particip = ParticipanteGrupo.query.filter_by(
                    grupo_id=partido.grupo_id,
                    usuario_id=apuesta.usuario_id
                ).first()
                if particip:
                    particip.balance_acumulado += ganancia
        
        # 5. Registrar perdedores
        for apuesta in apuestas_validas:
            if apuesta not in ganadores:
                liqui = LiquidacionHistorial(
                    partido_id=partido_id,
                    usuario_id=apuesta.usuario_id,
                    monto_apostado=apuesta.monto,
                    gano=False,
                    ganancia_neta=Decimal(apuesta.monto) * Decimal(-1)
                )
                db.session.add(liqui)
                
                particip = ParticipanteGrupo.query.filter_by(
                    grupo_id=partido.grupo_id,
                    usuario_id=apuesta.usuario_id
                ).first()
                if particip:
                    particip.balance_acumulado -= Decimal(apuesta.monto)
        
        # 6. Registrar comisión
        comision_reg = ComisionHistorial(
            grupo_id=partido.grupo_id,
            partido_id=partido_id,
            monto=comision,
            estado_pago=EstadoPago.PENDIENTE
        )
        db.session.add(comision_reg)
        
        # 7. Actualizar estado del partido
        partido.estado = EstadoPartido.LIQUIDADO
        partido.total_recaudado = total_recaudado
        
        db.session.commit()
        
        return {
            'success': True,
            'total_recaudado': float(total_recaudado),
            'comision': float(comision),
            'a_distribuir': float(a_distribuir),
            'ganadores': len(ganadores),
            'perdedores': len(apuestas_validas) - len(ganadores)
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def determinar_ganadores(apuestas, partido):
    """
    Determina quiénes acertaron según el tipo de juego.
    
    Si tipo_juego == 'Resultado':
        - Resultados posibles: 'Local gana', 'Empate', 'Visitante gana'
        - Parseamos marcador y comparamos
    
    Si tipo_juego == 'Marcador':
        - Resultados posibles: '2-1', '3-0', etc.
        - Comparamos exactos
    """
    
    grupo = partido.grupo
    resultado_real = partido.marcador  # Ej: '2-1'
    
    if grupo.tipo_juego.value == 'Resultado':
        # Parseamos: '2-1' -> Local 2, Visitante 1
        goles = resultado_real.split('-')
        goles_local = int(goles[0])
        goles_visitante = int(goles[1])
        
        if goles_local > goles_visitante:
            resultado = 'Local gana'
        elif goles_local < goles_visitante:
            resultado = 'Visitante gana'
        else:
            resultado = 'Empate'
        
        ganadores = [a for a in apuestas if a.prediccion == resultado]
    
    else:  # Marcador
        ganadores = [a for a in apuestas if a.prediccion == resultado_real]
    
    return ganadores

def marcar_comision_pagada(comision_id):
    """Marca una comisión como pagada y abre siguiente apuesta"""
    
    comision = ComisionHistorial.query.get(comision_id)
    if not comision:
        return False
    
    comision.estado_pago = EstadoPago.PAGO
    db.session.commit()
    
    # Abrir siguiente apuesta del grupo
    abrir_siguiente_apuesta(comision.partido.grupo_id)
    
    return True

def abrir_siguiente_apuesta(grupo_id):
    """Abre apuesta del siguiente partido que esté en estado CERRADO"""
    
    # Buscar próximo partido cerrado
    proximo = Partido.query.filter_by(
        grupo_id=grupo_id,
        estado=EstadoPartido.CERRADO
    ).order_by(Partido.fecha_hora).first()
    
    if proximo:
        proximo.estado = EstadoPartido.ABIERTO
        db.session.commit()
```

---

## 6. RUTAS BÁSICAS (routes.py - Extracto)

```python
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from logic import liquidar_partido, determinar_ganadores
from models import Grupo, Partido, Apuesta, PartidoParticipante, EstadoPago

bp = Blueprint('main', __name__)

# ===== AUTENTICACIÓN =====
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        contraseña = request.form.get('contraseña')
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(contraseña):
            login_user(usuario)
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error='Email o contraseña incorrectos')
    
    return render_template('login.html')

# ===== DASHBOARD =====
@bp.route('/dashboard')
@login_required
def dashboard():
    grupos = current_user.participaciones
    return render_template('dashboard.html', grupos=grupos)

# ===== GRUPO =====
@bp.route('/grupo/<int:grupo_id>')
@login_required
def ver_grupo(grupo_id):
    grupo = Grupo.query.get_or_404(grupo_id)
    partidos = Partido.query.filter_by(grupo_id=grupo_id).order_by(Partido.fecha_hora).all()
    
    return render_template('grupo.html', grupo=grupo, partidos=partidos)

# ===== APUESTA =====
@bp.route('/partido/<int:partido_id>', methods=['GET', 'POST'])
@login_required
def ver_partido(partido_id):
    partido = Partido.query.get_or_404(partido_id)
    
    if request.method == 'POST':
        prediccion = request.form.get('prediccion')
        monto = request.form.get('monto')
        
        apuesta = Apuesta(
            partido_id=partido_id,
            usuario_id=current_user.id,
            prediccion=prediccion,
            monto=monto
        )
        db.session.add(apuesta)
        db.session.commit()
        
        return redirect(url_for('main.ver_partido', partido_id=partido_id))
    
    apuestas = Apuesta.query.filter_by(partido_id=partido_id).all()
    return render_template('partido.html', partido=partido, apuestas=apuestas)

# ===== LIQUIDACIÓN =====
@bp.route('/api/liquidar/<int:partido_id>', methods=['POST'])
@login_required
def liquidar(partido_id):
    """API que liquida un partido (solo admin)"""
    
    partido = Partido.query.get_or_404(partido_id)
    
    # Verificar que es admin
    if current_user.id != partido.grupo.admin_primario_id and \
       current_user.id != partido.grupo.admin_secundario_id:
        return jsonify({'error': 'No eres admin'}), 403
    
    resultado = liquidar_partido(partido_id)
    return jsonify(resultado)

# ===== HISTORIAL =====
@bp.route('/historial/<int:grupo_id>')
@login_required
def historial(grupo_id):
    grupo = Grupo.query.get_or_404(grupo_id)
    
    # Obtener todas las liquidaciones del usuario en ese grupo
    liquidaciones = db.session.query(LiquidacionHistorial).join(
        Partido,
        Partido.id == LiquidacionHistorial.partido_id
    ).filter(
        Partido.grupo_id == grupo_id,
        LiquidacionHistorial.usuario_id == current_user.id
    ).all()
    
    return render_template('historial.html', liquidaciones=liquidaciones)
```

---

## 7. VALIDACIONES CLAVE

### Validar antes de apostar
```python
# El partido debe estar ABIERTO
assert partido.estado == EstadoPartido.ABIERTO

# El usuario debe haber pagado
assert PartidoParticipante.query.filter_by(
    partido_id=partido_id,
    usuario_id=current_user.id,
    estado_pago=EstadoPago.PAGO
).first()

# Monto debe ser igual al configurado en el grupo
assert request.form.get('monto') == str(partido.grupo.monto_por_apuesta)
```

### Validar antes de liquidar
```python
# Solo admin puede liquidar
assert current_user.id in [partido.grupo.admin_primario_id, 
                           partido.grupo.admin_secundario_id]

# El partido debe estar CERRADO
assert partido.estado == EstadoPartido.CERRADO

# Debe haber resultado cargado
assert partido.marcador is not None
```

---

## 8. ESTRUCTURA HTML MÍNIMA

### base.html
```html
<!DOCTYPE html>
<html>
<head>
    <title>Apuestas Mundial 2026</title>
    <style>
        * { margin: 0; padding: 0; }
        body { font-family: Arial; background: #f0f0f0; }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        .header { background: #2E75B6; color: white; padding: 20px; }
        .btn { background: #2E75B6; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; background: white; margin: 20px 0; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #2E75B6; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Apuestas Mundial 2026</h1>
        {% if current_user.is_authenticated %}
            <p>Bienvenido, {{ current_user.nombre }} | <a href="/logout">Salir</a></p>
        {% endif %}
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

---

## 9. CASOS DE TEST (MÍNIMO)

```python
def test_liquidacion():
    """Test: 2 ganan, 2 pierden"""
    
    # Setup
    grupo = crear_grupo_test()
    partido = crear_partido_test(grupo)
    partido.marcador = '2-1'  # Local gana
    
    # Apostar
    apostar_test(usuario1, partido, '2-1', 50)  # Gana
    apostar_test(usuario2, partido, '2-1', 50)  # Gana
    apostar_test(usuario3, partido, '1-2', 50)  # Pierde
    apostar_test(usuario4, partido, '0-0', 50)  # Pierde
    
    # Marcar pagos
    marcar_pagado_test(usuario1, partido)
    marcar_pagado_test(usuario2, partido)
    marcar_pagado_test(usuario3, partido)
    marcar_pagado_test(usuario4, partido)
    
    # Liquidar
    resultado = liquidar_partido(partido.id)
    
    # Verificaciones
    assert resultado['success'] == True
    assert resultado['total_recaudado'] == 200
    assert resultado['comision'] == 4  # 2% de 200
    assert resultado['a_distribuir'] == 196
    assert resultado['ganadores'] == 2
    
    # Balances
    assert usuario1.balance == 98  # (50/100) * 196
    assert usuario2.balance == 98
    assert usuario3.balance == -50
    assert usuario4.balance == -50
```

---

## 10. DEPLOYMENT RÁPIDO (Heroku)

```bash
# Crear app
heroku create apuestas-mundial-2026

# Config vars
heroku config:set DATABASE_URL=postgresql://...
heroku config:set SECRET_KEY=tu-secret-key-aqui

# Archivo Procfile
echo "web: gunicorn run:app" > Procfile

# Deploy
git push heroku main

# Crear BD
heroku run python -c "from app import create_app, db; app = create_app(); db.create_all()"
```

---

## RESUMEN

Esta guía tiene lo mínimo necesario para:
1. Estructura clara
2. BD relacional correcta
3. Lógica de liquidación bulletproof
4. Validaciones esenciales
5. Rutas básicas
6. Deploy simple

**NO incluye**: Auth complejo, emails, APIs externas, admin panel sofisticado.

**Enfoque**: MVP rápido, funcional, escalable después.
