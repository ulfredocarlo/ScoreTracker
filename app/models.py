from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Usuario(UserMixin, db.Model):
    """
    Modelo representativo de los Usuarios globales en ScoreTracker. [Willys_IA]
    Maneja credenciales y relaciones a grupos, predicciones y conciliaciones.
    """
    __tablename__ = 'usuarios'
    
    # Identificador unico del usuario
    id = db.Column(db.Integer, primary_key=True)
    
    # Email institucional o personal de acceso unico
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Hash de seguridad de la contrasena
    contrasena = db.Column(db.String(255), nullable=False)
    
    # Nombre visible y perfil del usuario
    nombre = db.Column(db.String(255), nullable=False)
    
    # Fecha automatica de auditoria de registro
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # === RELACIONES DE INTEGRIDAD ===
    # Grupos administrados por este usuario
    grupos_administrados = db.relationship('Grupo', backref='administrador', foreign_keys='Grupo.admin_id')
    
    # Grupos donde este usuario es designado Responsable de Pagos (Tesorero)
    grupos_tesoreria = db.relationship('Grupo', backref='tesorero', foreign_keys='Grupo.tesorero_id')
    
    # Membresias en grupos cerrados de amigos
    membresias = db.relationship('ParticipanteGrupo', backref='usuario', cascade='all, delete-orphan')
    
    # Predicciones realizadas por el usuario
    predicciones = db.relationship('Prediccion', backref='usuario', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashea de forma segura la contrasena provista. [Willys_IA]"""
        self.contrasena = generate_password_hash(password)
        
    def check_password(self, password):
        """Verifica la contrasena contra el hash almacenado. [Willys_IA]"""
        return check_password_hash(self.contrasena, password)


class Grupo(db.Model):
    """
    Modelo representativo de las Comunidades o Grupos de Juego. [Willys_IA]
    Almacena las consideraciones (reglas del juego) fijadas por los participantes.
    """
    __tablename__ = 'grupos'
    
    # Identificador unico del grupo
    id = db.Column(db.Integer, primary_key=True)
    
    # Nombre del torneo o grupo (ej: 'Los Amigos del Mundial')
    nombre = db.Column(db.String(255), nullable=False)
    
    # Descripcion informativa o propositos del grupo
    descripcion = db.Column(db.Text)
    
    # Clave foranea del Administrador (Organizador)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Clave foranea del Tesorero (Responsable de recaudar y devolver aportes)
    tesorero_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # CONSIDERACION: Valor estandar de cada participacion por partido expresado en Balones
    balones_aporte = db.Column(db.Integer, default=10, nullable=False)
    
    # CONSIDERACION: Equivalencia del Balon en dinero real
    balon_equivalencia = db.Column(db.Numeric(10, 2), default=1.00, nullable=False)
    
    # CONSIDERACION: Codigo de la Moneda del pais (ej: 'Bs', 'ARS', '$')
    moneda_codigo = db.Column(db.String(10), default='Bs', nullable=False)
    
    # Porcentaje de comision estandar de la app (ej: 2.00%)
    comision_porcentaje = db.Column(db.Numeric(5, 2), default=2.00, nullable=False)
    
    # CONSIDERACION: Modalidad de pronostico ('Resultado' o 'Marcador')
    tipo_juego = db.Column(db.String(50), default='Marcador', nullable=False)
    
    # CONSIDERACION: Que hacer en caso de pozo vacio ('Acumular' o 'Devolver')
    politica_pozo_vacio = db.Column(db.String(50), default='Acumular', nullable=False)
    
    # CONSIDERACION: Tiempo limite en minutos antes del juego para conciliar pagos
    limite_pago_minutos = db.Column(db.Integer, default=60, nullable=False)
    
    # CONSIDERACION: Acuerdos Especiales redactados en texto libre (asados, comodines)
    acuerdos_especiales = db.Column(db.Text)
    
    # Balones de arrastre acumulados de partidos anteriores sin ganadores
    pozo_acumulado = db.Column(db.Integer, default=0, nullable=False)
    
    # Estado de avance del grupo ('Configuracion' [permite cambios], 'Activo' [congelado])
    estado_juego = db.Column(db.String(20), default='Configuracion', nullable=False)
    
    # Codigo de invitacion unico al grupo
    codigo_invitacion = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Datos de pago offline provistos por el Tesorero (Cuenta, QR texto, Tel)
    datos_pago_tesorero = db.Column(db.Text)
    
    # Ruta de la imagen del código QR bancario de cobro subida por el Tesorero [Willys_IA]
    qr_pago_path = db.Column(db.String(255), nullable=True)
    
    # Auditoria de creacion
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # === RELACIONES ===
    # Participantes activos en el grupo
    participantes = db.relationship('ParticipanteGrupo', backref='grupo', cascade='all, delete-orphan')
    
    # Predicciones asociadas al grupo
    predicciones = db.relationship('Prediccion', backref='grupo', cascade='all, delete-orphan')
    
    # Caja de validaciones de pago por partido
    caja_pagos = db.relationship('PartidoParticipanteCaja', backref='grupo', cascade='all, delete-orphan')
    
    # Historial de comisiones del grupo con la app
    comisiones = db.relationship('ComisionHistorial', backref='grupo', cascade='all, delete-orphan')


class ParticipanteGrupo(db.Model):
    """
    Modelo de Membresia e Historial Financiero del Jugador en el Grupo. [Willys_IA]
    Controla el balance acumulado de Balones y la aceptacion del reglamento del grupo.
    """
    __tablename__ = 'participantes_grupo'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacion al grupo
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id', ondelete='CASCADE'), nullable=False)
    
    # Relacion al usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Balance acumulado neto de Balones en este grupo (Suma de ganados - perdidos)
    balance_balones = db.Column(db.Integer, default=0, nullable=False)
    
    # Check obligatorio de aceptacion de consideraciones del grupo para poder jugar
    reglas_aceptadas = db.Column(db.Boolean, default=False, nullable=False)
    
    # Auditoria de union al grupo
    fecha_union = db.Column(db.DateTime, default=datetime.utcnow)


class Partido(db.Model):
    """
    Modelo representativo del Calendario Global de Partidos. [Willys_IA]
    Gestionado centralmente por el Administrador de la App.
    """
    __tablename__ = 'partidos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Nombres de los seleccionados de futbol
    equipo_local = db.Column(db.String(100), nullable=False)
    equipo_visitante = db.Column(db.String(100), nullable=False)
    
    # Codigos ISO de pais de 2 letras para renderizar las banderas oficiales (ej: 'bo', 'ar')
    codigo_local = db.Column(db.String(5), default='', nullable=False)
    codigo_visitante = db.Column(db.String(5), default='', nullable=False)
    
    # Fecha y hora oficial del partido (UTC)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    
    # Fase del Mundial (ej: 'Grupos', 'Octavos', 'Final')
    fase = db.Column(db.String(50))
    
    # Marcador final registrado (ej: '2-1')
    marcador = db.Column(db.String(10))
    
    # Sede/Estadio oficial del partido (ej: 'Estadio Azteca, CDMX') [Willys_IA]
    lugar = db.Column(db.String(255), default='', nullable=False)
    
    # Estado del ciclo de vida del partido
    # 'Programado', 'Abierto', 'EnVerificacion', 'Cerrado', 'Terminado', 'Liquidado'
    estado = db.Column(db.String(20), default='Programado', nullable=False)
    
    # === RELACIONES ===
    # Predicciones ingresadas para este partido
    predicciones = db.relationship('Prediccion', backref='partido', cascade='all, delete-orphan')
    
    # Caja de conciliaciones asociadas a este partido
    caja_pagos = db.relationship('PartidoParticipanteCaja', backref='partido', cascade='all, delete-orphan')
    
    # Comisiones generadas por este partido
    comisiones = db.relationship('ComisionHistorial', backref='partido', cascade='all, delete-orphan')


class Prediccion(db.Model):
    """
    Modelo de Predicciones o Pronosticos de Juego. [Willys_IA]
    Almacena los balones aportados y el resultado o marcador predicho.
    """
    __tablename__ = 'predicciones'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencia al partido
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id', ondelete='CASCADE'), nullable=False)
    
    # Referencia al usuario predictor
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Referencia al grupo de juego
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id', ondelete='CASCADE'), nullable=False)
    
    # Valor del pronostico (ej: 'Local gana' o '2-1')
    valor_prediccion = db.Column(db.String(50), nullable=False)
    
    # Campo de texto opcional para reportar datos del comprobante offline al Tesorero
    comprobante_pago = db.Column(db.String(500))
    
    # Ruta de la imagen del recibo/captura de transferencia cargada por el jugador [Willys_IA]
    comprobante_path = db.Column(db.String(255), nullable=True)
    
    # Fecha de registro
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


class PartidoParticipanteCaja(db.Model):
    """
    Modelo contable para la Conciliacion Offline. [Willys_IA]
    Controla si el aporte en Balones del usuario para un partido fue verificado en caja por el Tesorero.
    """
    __tablename__ = 'partidos_participantes_caja'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias relacionales
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id', ondelete='CASCADE'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Estado del jugador en esta conciliacion:
    # 'Por Pagar' (Aun no paga), 'Por Validar' (Comprobante/efectivo reportado) o 'Participa' (Pago confirmado offline, pozo neto activo)
    estado_pago = db.Column(db.String(20), default='Por Pagar', nullable=False)
    # Identificador del administrador o tesorero del grupo que audito el pago
    marcado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Fecha de la conciliacion bancaria offline
    fecha_marcado = db.Column(db.DateTime)
    
    # === RELACIONES ===
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    auditor = db.relationship('Usuario', foreign_keys=[marcado_por])


class LiquidacionHistorial(db.Model):
    """
    Modelo de Auditoria Contable de Liquidaciones. [Willys_IA]
    Guarda el registro de cada transaccion de Balones en un partido (ganancia o perdida neta).
    """
    __tablename__ = 'liquidacion_historial'
    
    id = db.Column(db.Integer, primary_key=True)
    
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    
    # Balones aportados
    monto_aportado = db.Column(db.Integer, nullable=False)
    
    # Indicador de acierto
    gano = db.Column(db.Boolean, nullable=False)
    
    # Balance contable resultante en Balones (puede ser negativo ej: -10 por haber perdido)
    ganancia_neta = db.Column(db.Integer, nullable=False)
    
    # Fecha de liquidacion del sistema
    fecha_liquidacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones de auditoria
    partido = db.relationship('Partido')
    usuario = db.relationship('Usuario')
    grupo = db.relationship('Grupo')


class ComisionHistorial(db.Model):
    """
    Modelo representativo de la Facturacion de la Plataforma. [Willys_IA]
    Controla las comisiones acumuladas que los grupos adeudan a ScoreTracker para desbloquear el juego.
    """
    __tablename__ = 'comisiones_historial'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias al grupo y al partido liquidado
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    
    # Comision en Balones virtuales deducida del pozo
    monto_balones = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Equivalencia financiera real a transferir a los admins de la app (monto_balones * balon_equivalencia)
    monto_dinero_real = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Estado de la cobranza de la app ('Pendiente', 'Pagado')
    estado_pago = db.Column(db.String(20), default='Pendiente', nullable=False)
    
    # Registro de auditoria
    fecha_liquidacion = db.Column(db.DateTime, default=datetime.utcnow)
