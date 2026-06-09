import uuid
import re
import random
import string
import unicodedata
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario, Grupo, ParticipanteGrupo, Partido, Prediccion, PartidoParticipanteCaja, LiquidacionHistorial, ComisionHistorial

# Definicion del Blueprint para el ruteo principal
bp = Blueprint('main', __name__)

def slugificar(texto):
    """Convierte un texto en un slug limpio y amigable para URL y códigos de invitación. [Willys_IA]"""
    # Normalizar y quitar acentos
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    # Quitar caracteres especiales (dejar solo letras, números, espacios y guiones)
    texto = re.sub(r'[^a-zA-Z0-9\s-]', '', texto).strip().lower()
    # Reemplazar espacios y guiones múltiples por un solo guion
    texto = re.sub(r'[\s-]+', '-', texto)
    return texto

def generar_codigo_invitacion(nombre_grupo, partido=None):
    """Genera un código de invitación legible, único y con sufijo de países si corresponde. [Willys_IA]"""
    base = slugificar(nombre_grupo)
    if not base:
        base = "grupo"
        
    # Construir el sufijo de países o aleatorio
    if partido:
        def clean_name(name):
            # Quitar acentos y caracteres no alfanuméricos
            n = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
            return re.sub(r'[^a-zA-Z0-9]', '', n)
        
        c1 = clean_name(partido.equipo_local)
        c2 = clean_name(partido.equipo_visitante)
        sufijo = f"-{c1}-{c2}" # ej: -Mexico-Sudafrica
    else:
        # Si es un grupo creado sin partido específico, agregar sufijo aleatorio para evitar colisiones básicas
        sufijo = "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
    # Garantizar que el código total no exceda la limitación de 50 caracteres de la base de datos
    max_base_len = 50 - len(sufijo)
    base_truncada = base[:max_base_len].rstrip('-')
    
    codigo_propuesto = f"{base_truncada}{sufijo}".upper()
    
    # Resolver colisiones para garantizar unicidad en la base de datos
    contador = 1
    codigo_final = codigo_propuesto
    while Grupo.query.filter(db.func.upper(Grupo.codigo_invitacion) == codigo_final).first() is not None:
        sufijo_num = f"-{contador}"
        max_base_len = 50 - len(sufijo) - len(sufijo_num)
        base_truncada = base[:max_base_len].rstrip('-')
        codigo_final = f"{base_truncada}{sufijo}{sufijo_num}".upper()
        contador += 1
        
    return codigo_final


def guardar_imagen_optimizada(file, folder, max_width=800, quality=75):
    """
    Guarda y comprime una captura de pantalla/recibo o QR en disco a formato JPEG. [Willys_IA]
    Reduce el peso en un 98% (de ~5MB a ~120KB) manteniendo legibilidad excelente.
    """
    import os
    import uuid
    from PIL import Image
    
    if not file:
        return None
        
    filename = file.filename
    if not filename or '.' not in filename:
        return None
        
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        return None
        
    # Ruta absoluta en el workspace
    upload_path = os.path.join(os.path.dirname(__file__), 'static', 'uploads', folder)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        
    # Nombre único para evitar colisiones
    nuevo_nombre = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(upload_path, nuevo_nombre)
    
    try:
        # Abrir imagen con Pillow
        img = Image.open(file)
        
        # Convertir a RGB si es PNG/GIF con transparencia para poder guardarla como JPEG
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Redimensionar si supera el ancho máximo
        width, height = img.size
        if width > max_width:
            ratio = max_width / float(width)
            new_height = int(float(height) * float(ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        # Guardar en formato JPEG optimizado
        img.save(filepath, 'JPEG', quality=quality, optimize=True)
        return f"uploads/{folder}/{nuevo_nombre}"
    except Exception as e:
        print(f"[Willys_IA] Error al optimizar imagen: {str(e)}")
        return None


# ==========================================
# 1. RUTAS DE AUTENTICACION [Willys_IA]
# ==========================================

@bp.route('/')
def index():
    """Ruta raiz: muestra el fixture completo e interactivo para todos los usuarios. [Willys_IA]"""
    # Obtener todos los partidos ordenados cronológicamente
    partidos_publicos = Partido.query.order_by(Partido.fecha_hora.asc()).all()
    
    # Obtener predicciones del usuario autenticado para mostrar sus grupos activos
    predicciones_usuario = {}
    if current_user.is_authenticated:
        from app.models import Prediccion
        preds = Prediccion.query.filter_by(usuario_id=current_user.id).all()
        for p in preds:
            if p.partido_id not in predicciones_usuario:
                predicciones_usuario[p.partido_id] = []
            predicciones_usuario[p.partido_id].append({
                'grupo_id': p.grupo_id,
                'grupo_nombre': p.grupo.nombre
            })
            
    colores_uniformes = {
        'Argentina': '#75AADB',
        'Mexico': '#006847',
        'Estados Unidos': '#0A2342',
        'Canada': '#FF0000',
        'Brasil': '#FEDF00',
        'Sudafrica': '#FFCC00',
        'Paraguay': '#D52B1E',
        'Marruecos': '#C1272D',
        'Bosnia': '#002F6C',
        'Serbia': '#C60B1E',
        'Islandia': '#005B94'
    }
    
    return render_template(
        'index.html', 
        partidos=partidos_publicos, 
        predicciones_usuario=predicciones_usuario,
        colores_uniformes=colores_uniformes
    )


@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Maneja el registro de nuevos usuarios en el sistema. [Willys_IA]"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        contrasena = request.form.get('contrasena', '')
        
        # Validaciones de campos
        if not nombre or not email or not contrasena:
            flash('Por favor, completa todos los campos del formulario.', 'danger')
            return render_template('registro.html')
            
        # Validar si el usuario ya existe en base de datos
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este correo electronico ya se encuentra registrado.', 'warning')
            return render_template('registro.html')
            
        # Creacion y almacenamiento seguro del nuevo usuario
        nuevo_usuario = Usuario(nombre=nombre, email=email)
        nuevo_usuario.set_password(contrasena)
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('¡Cuenta creada con exito! Ahora puedes iniciar sesion.', 'success')
            next_page = request.args.get('next')
            return redirect(url_for('main.login', next=next_page))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrio un error al registrar la cuenta: {str(e)}', 'danger')
            
    return render_template('registro.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesion seguro del usuario. [Willys_IA]"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        contrasena = request.form.get('contrasena', '')
        
        if not email or not contrasena:
            flash('Por favor, ingresa tu correo y contrasena.', 'danger')
            return render_template('login.html')
            
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verificacion de credenciales
        if usuario and usuario.check_password(contrasena):
            login_user(usuario, remember=True)
            flash(f'¡Bienvenido de vuelta, {usuario.nombre}!', 'success')
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Credenciales incorrectas. Intentalo de nuevo.', 'danger')
            
    return render_template('login.html')


@bp.route('/login/google/mock')
def login_google_mock():
    """Simula el retorno de Google OAuth 2.0 y registra/ingresa al usuario al instante. [Willys_IA]"""
    # Identidad simulada provista de Google
    email_simulado = "willys.mock@scoretracker.com"
    nombre_simulado = "Willys (Google)"
    
    # Buscar si ya existe este usuario
    usuario = Usuario.query.filter_by(email=email_simulado).first()
    
    if not usuario:
        # Registrar de forma automatica en base de datos PostgreSQL local
        usuario = Usuario(nombre=nombre_simulado, email=email_simulado)
        # Contrasena mock aleatoria por seguridad interna
        usuario.set_password(str(uuid.uuid4()))
        db.session.add(usuario)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error en la simulacion de Google: {str(e)}', 'danger')
            return redirect(url_for('main.login'))
            
    # Autenticar sesion en Flask-Login
    login_user(usuario, remember=True)
    flash('¡Has iniciado sesion con tu cuenta de Google de forma exitosa (Modo Simulado)!', 'success')
    next_page = request.args.get('next')
    if not next_page or not next_page.startswith('/'):
        next_page = url_for('main.index')
    return redirect(next_page)


@bp.route('/login/switch')
def login_switch():
    """Permite cambiar instantáneamente de usuario para pruebas y simulación del flujo de juego. [Willys_IA]"""
    email = request.args.get('email', '').strip().lower()
    if not email:
        flash('Email no especificado para el cambio de usuario.', 'warning')
        return redirect(url_for('main.login'))
    
    # Lista de correos permitidos para simulación y sus apodos premium
    correos_simulacion = {
        'ucarlo@comteco.com.bo': 'Ucarlo Admin',
        'ulfredoc@gmail.com': 'Ulfredoc Jugador 1',
        'ulfredo.carlo@gmail.com': 'Ulfredo Jugador 2',
        'willys@msn.com': 'Willys Jugador 3'
    }
    
    if email not in correos_simulacion:
        flash('El correo ingresado no está habilitado para simulación rápida.', 'danger')
        return redirect(url_for('main.login'))
        
    nombre = correos_simulacion[email]
    
    # Buscar si ya existe este usuario
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        # Registrar de forma automática en base de datos PostgreSQL local
        usuario = Usuario(nombre=nombre, email=email)
        usuario.set_password('comteco123')
        db.session.add(usuario)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario de simulación: {str(e)}', 'danger')
            return redirect(url_for('main.login'))
            
    # Autenticar sesión en Flask-Login
    login_user(usuario, remember=True)
    flash(f'Sesión cambiada con éxito. Ahora actúas como: {nombre} ({email})', 'success')
    
    next_page = request.args.get('next')
    if not next_page or not next_page.startswith('/'):
        next_page = url_for('main.index')
    return redirect(next_page)


@bp.route('/logout')
@login_required
def logout():
    """Cierra la sesion activa del usuario actual de forma segura. [Willys_IA]"""
    logout_user()
    flash('Has cerrado sesion correctamente. ¡Vuelve pronto!', 'success')
    return redirect(url_for('main.login'))

# ==========================================
# 2. PANEL DE CONTROL (DASHBOARD) [Willys_IA]
# ==========================================

@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Vista principal del usuario. Lista sus grupos y permite creacion de nuevos. [Willys_IA]"""
    if request.method == 'POST':
        # Procesar creacion de un nuevo grupo de juego
        nombre_grupo = request.form.get('nombre_grupo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        balones_aporte = request.form.get('balones_aporte', 10, type=int)
        balon_equivalencia = request.form.get('balon_equivalencia', 1.0, type=float)
        moneda_codigo = request.form.get('moneda_codigo', 'Bs').strip()
        tipo_juego = request.form.get('tipo_juego', 'Marcador')
        politica_pozo = request.form.get('politica_pozo', 'Acumular')
        limite_pago = request.form.get('limite_pago', 60, type=int)
        acuerdos_especiales = request.form.get('acuerdos_especiales', '').strip()
        datos_pago = request.form.get('datos_pago', '').strip()
        
        if not nombre_grupo:
            flash('El nombre del grupo es obligatorio.', 'danger')
            return redirect(url_for('main.dashboard'))
            
        # Generar codigo de invitacion unico
        codigo_invitacion = generar_codigo_invitacion(nombre_grupo)
        
        # Procesar código QR bancario de cobro [Willys_IA]
        qr_file = request.files.get('qr_image')
        qr_path = None
        if qr_file and qr_file.filename != '':
            qr_path = guardar_imagen_optimizada(qr_file, 'qrs')
            
        nuevo_grupo = Grupo(
            nombre=nombre_grupo,
            descripcion=descripcion,
            admin_id=current_user.id,
            tesorero_id=current_user.id, # Por defecto el creador es Tesorero
            balones_aporte=balones_aporte,
            balon_equivalencia=balon_equivalencia,
            moneda_codigo=moneda_codigo,
            tipo_juego=tipo_juego,
            politica_pozo_vacio=politica_pozo,
            limite_pago_minutos=limite_pago,
            acuerdos_especiales=acuerdos_especiales,
            codigo_invitacion=codigo_invitacion,
            datos_pago_tesorero=datos_pago,
            qr_pago_path=qr_path
        )
        
        try:
            db.session.add(nuevo_grupo)
            db.session.flush() # Obtener el ID generado para el grupo
            
            # El administrador del grupo es inscrito automaticamente como participante activo
            membresia_admin = ParticipanteGrupo(
                grupo_id=nuevo_grupo.id,
                usuario_id=current_user.id,
                reglas_aceptadas=True # El admin acepta automaticamente sus propias reglas
            )
            db.session.add(membresia_admin)
            db.session.commit()
            flash(f'¡Grupo "{nuevo_grupo.nombre}" creado exitosamente! Comparte el codigo de invitacion: {nuevo_grupo.codigo_invitacion}', 'success')
            return redirect(url_for('main.ver_grupo', grupo_id=nuevo_grupo.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el grupo: {str(e)}', 'danger')
            
    # Listar las membresias activas del usuario (grupos donde participa)
    mis_grupos = ParticipanteGrupo.query.filter_by(usuario_id=current_user.id).all()
    
    return render_template('dashboard.html', mis_grupos=mis_grupos)


@bp.route('/unirse', methods=['POST'])
@login_required
def unirse_grupo():
    """Permite unirse a un grupo mediante su codigo unico de invitacion. [Willys_IA]"""
    codigo = request.form.get('codigo_invitacion', '').strip()
    print(f"[Willys_IA] INICIANDO UNIÓN A GRUPO. Codigo ingresado original: '{codigo}'")
    
    if not codigo:
        flash('Por favor, ingresa un codigo de invitacion.', 'warning')
        return redirect(url_for('main.dashboard'))
        
    grupo = Grupo.query.filter(db.func.upper(Grupo.codigo_invitacion) == codigo.upper()).first()
    print(f"[Willys_IA] Resultado busqueda grupo en DB: {grupo}")
    
    if not grupo:
        flash('El codigo de invitacion no es valido o el grupo no existe.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    # Verificar si ya es miembro del grupo
    membresia_existente = ParticipanteGrupo.query.filter_by(
        grupo_id=grupo.id, 
        usuario_id=current_user.id
    ).first()
    
    if membresia_existente:
        flash('Ya eres miembro de este grupo de juego.', 'warning')
        return redirect(url_for('main.ver_grupo', grupo_id=grupo.id))
        
    # Crear membresia en estado Por Pagar (aun no acepta reglas obligatoriamente)
    nueva_membresia = ParticipanteGrupo(
        grupo_id=grupo.id,
        usuario_id=current_user.id,
        reglas_aceptadas=False # Debe aceptar las reglas antes de jugar
    )
    
    try:
        db.session.add(nueva_membresia)
        db.session.commit()
        flash(f'¡Te has unido con exito al grupo "{grupo.nombre}"! Revisa y acepta las consideraciones para empezar.', 'success')
        return redirect(url_for('main.ver_grupo', grupo_id=grupo.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al unirse al grupo: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))


@bp.route('/invitacion/<string:codigo>', methods=['GET', 'POST'])
@login_required
def invitacion_flujo(codigo):
    """
    Flujo de Invitación Express [Willys_IA]:
    Al hacer clic en el enlace compartido, obliga a loguearse y muestra inmediatamente
    los datos del grupo en modo visual (sin poder cambiar) y le solicita el pronóstico del partido.
    """
    grupo = Grupo.query.filter(db.func.upper(Grupo.codigo_invitacion) == codigo.upper()).first_or_404()
    
    # Verificar si ya es miembro
    membresia_existente = ParticipanteGrupo.query.filter_by(
        grupo_id=grupo.id, 
        usuario_id=current_user.id
    ).first()
    
    # Obtener el partido específico desde los parámetros o el primer abierto por defecto [Willys_IA]
    partido_id = request.args.get('partido_id', type=int)
    if partido_id:
        partido = Partido.query.get_or_404(partido_id)
    else:
        partido = Partido.query.filter_by(estado='Abierto').order_by(Partido.fecha_hora.asc()).first()
    
    if request.method == 'POST':
        # Procesar unión y predicción
        aceptar_reglas = request.form.get('aceptar_reglas') == 'on'
        goles_local = request.form.get('goles_local', '').strip()
        goles_visitante = request.form.get('goles_visitante', '').strip()
        comprobante = request.form.get('comprobante_pago', '').strip()
        
        # Procesar y optimizar la imagen del recibo de transferencia subido por el jugador [Willys_IA]
        recibo_file = request.files.get('comprobante_image')
        recibo_path = None
        if recibo_file and recibo_file.filename != '':
            recibo_path = guardar_imagen_optimizada(recibo_file, 'comprobantes')
            
        if not aceptar_reglas:
            flash('Debes aceptar las consideraciones del grupo para unirte.', 'warning')
            return redirect(url_for('main.invitacion_flujo', codigo=codigo))
            
        try:
            # 1. Crear membresía aceptando las reglas automáticamente
            if not membresia_existente:
                nueva_membresia = ParticipanteGrupo(
                    grupo_id=grupo.id,
                    usuario_id=current_user.id,
                    reglas_aceptadas=True
                )
                db.session.add(nueva_membresia)
            else:
                membresia_existente.reglas_aceptadas = True
                
            # 2. Registrar predicción si hay partido abierto y goles ingresados
            if partido and goles_local != '' and goles_visitante != '':
                valor_prediccion = f"{goles_local}-{goles_visitante}"
                
                # Evitar predicciones duplicadas
                from app.models import Prediccion
                prediccion_previa = Prediccion.query.filter_by(
                    partido_id=partido.id,
                    usuario_id=current_user.id,
                    grupo_id=grupo.id
                ).first()
                
                if prediccion_previa:
                    prediccion_previa.valor_prediccion = valor_prediccion
                    if comprobante:
                        prediccion_previa.comprobante_pago = comprobante
                    if recibo_path:
                        prediccion_previa.comprobante_path = recibo_path
                else:
                    nueva_prediccion = Prediccion(
                        partido_id=partido.id,
                        usuario_id=current_user.id,
                        grupo_id=grupo.id,
                        valor_prediccion=valor_prediccion,
                        comprobante_pago=comprobante,
                        comprobante_path=recibo_path
                    )
                    db.session.add(nueva_prediccion)
                    
                    # Inicializar caja
                    from app.models import PartidoParticipanteCaja
                    nueva_caja = PartidoParticipanteCaja(
                        partido_id=partido.id,
                        grupo_id=grupo.id,
                        usuario_id=current_user.id,
                        estado_pago='Por Validar' if recibo_path or comprobante == 'Efectivo' else 'Por Pagar'
                    )
                    db.session.add(nueva_caja)
            
            db.session.commit()
            flash(f'¡Bienvenido al grupo "{grupo.nombre}"! Tu pronóstico ha sido registrado exitosamente.', 'success')
            
            # Redirigir al partido unificado
            if partido:
                return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
            return redirect(url_for('main.ver_grupo', grupo_id=grupo.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al procesar tu unión express: {str(e)}', 'danger')
            return redirect(url_for('main.invitacion_flujo', codigo=codigo))
            
    # Si es GET, mostrar el formulario premium read-only y el pronóstico
    return render_template('invitacion.html', grupo=grupo, partido=partido, membresia_existente=membresia_existente)


@bp.route('/jugar/<int:partido_id>', methods=['GET'])
@login_required
def jugar_flujo(partido_id):
    """Página despachadora principal: permite elegir entre jugar en grupo existente o crear nuevo grupo. [Willys_IA]"""
    partido = Partido.query.get_or_404(partido_id)
    
    # Si el partido no está abierto, no se permiten nuevas predicciones
    if partido.estado != 'Abierto':
        flash('Las predicciones para este partido ya están cerradas.', 'warning')
        return redirect(url_for('main.index'))
        
    return render_template('jugar_flujo.html', partido=partido)


@bp.route('/jugar/<int:partido_id>/existente', methods=['GET', 'POST'])
@login_required
def jugar_existente(partido_id):
    """Permite registrar o modificar la predicción del partido en un grupo existente o unirse con código. [Willys_IA]"""
    partido = Partido.query.get_or_404(partido_id)
    
    if partido.estado != 'Abierto':
        flash('Las predicciones para este partido ya están cerradas.', 'warning')
        return redirect(url_for('main.index'))
        
    # Obtener las membresías del usuario para listar todos sus grupos
    membresias = ParticipanteGrupo.query.filter_by(usuario_id=current_user.id).all()
    mis_grupos = [m.grupo for m in membresias]
    
    # Obtener todas las predicciones del usuario para este partido para pre-cargar datos [Willys_IA]
    from app.models import Prediccion
    preds = Prediccion.query.filter_by(partido_id=partido.id, usuario_id=current_user.id).all()
    preds_map = {p.grupo_id: {
        'valor': p.valor_prediccion,
        'comprobante': p.comprobante_pago or ''
    } for p in preds}
            
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'unirse':
            # Flujo de unión express a un grupo existente con predicción integrada
            codigo = request.form.get('codigo_invitacion', '').strip()
            print(f"[Willys_IA] INICIANDO UNIÓN EXPRESS. Codigo ingresado original: '{codigo}'")
            goles_local = request.form.get('goles_local', '').strip()
            goles_visitante = request.form.get('goles_visitante', '').strip()
            aceptar_reglas = request.form.get('aceptar_reglas') == 'on'
            
            if not codigo:
                flash('Por favor, ingresa el código de invitación.', 'warning')
                return redirect(url_for('main.jugar_existente', partido_id=partido.id))
                
            grupo = Grupo.query.filter(db.func.upper(Grupo.codigo_invitacion) == codigo.upper()).first()
            print(f"[Willys_IA] Resultado busqueda express en DB: {grupo}")
            
            if not grupo:
                flash('El código de invitación no es válido o el grupo no existe.', 'danger')
                return redirect(url_for('main.jugar_existente', partido_id=partido.id))
                
            # Verificar si ya es miembro
            membresia_existente = ParticipanteGrupo.query.filter_by(
                grupo_id=grupo.id, 
                usuario_id=current_user.id
            ).first()
            
            if membresia_existente:
                flash('Ya eres miembro de este grupo de juego.', 'warning')
                return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
                
            if goles_local == '' or goles_visitante == '':
                flash('Debes ingresar tu pronóstico de goles.', 'warning')
                return redirect(url_for('main.jugar_existente', partido_id=partido.id))
                
            if not aceptar_reglas:
                flash('Para registrar tu predicción debes marcar la casilla aceptando el reglamento del grupo.', 'warning')
                return redirect(url_for('main.jugar_existente', partido_id=partido.id))
                
            # Crear membresía activa
            nueva_membresia = ParticipanteGrupo(
                grupo_id=grupo.id,
                usuario_id=current_user.id,
                reglas_aceptadas=True
            )
            db.session.add(nueva_membresia)
            
            # Insertar la predicción
            valor_prediccion = f"{goles_local}-{goles_visitante}"
            nueva_prediccion = Prediccion(
                partido_id=partido.id,
                usuario_id=current_user.id,
                grupo_id=grupo.id,
                valor_prediccion=valor_prediccion
            )
            db.session.add(nueva_prediccion)
            
            # Inicializar la caja del jugador en Por Pagar
            nueva_caja = PartidoParticipanteCaja(
                partido_id=partido.id,
                grupo_id=grupo.id,
                usuario_id=current_user.id,
                estado_pago='Por Pagar'
            )
            db.session.add(nueva_caja)
            
            try:
                db.session.commit()
                flash(f'¡Te has unido con éxito al grupo "{grupo.nombre}" y tu predicción fue registrada! Informa a tu Tesorero.', 'success')
                return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al unirse al grupo: {str(e)}', 'danger')
                return redirect(url_for('main.jugar_existente', partido_id=partido.id))
                
        elif action == 'predecir_existente':
            # Registrar o Modificar predicción en grupo propio
            grupo_id = request.form.get('grupo_id', type=int)
            goles_local = request.form.get('goles_local', '').strip()
            goles_visitante = request.form.get('goles_visitante', '').strip()
            comprobante = request.form.get('comprobante_pago', '').strip()
            aceptar_reglas = request.form.get('aceptar_reglas') == 'on'
            
            # Procesar la subida y compresión del recibo de transferencia bancaria [Willys_IA]
            recibo_file = request.files.get('comprobante_image')
            recibo_path = None
            if recibo_file and recibo_file.filename != '':
                recibo_path = guardar_imagen_optimizada(recibo_file, 'comprobantes')
                
            if not grupo_id or goles_local == '' or goles_visitante == '':
                flash('Datos incompletos para registrar tu predicción.', 'danger')
                return redirect(url_for('main.jugar_existente', partido_id=partido.id))
                
            membresia = ParticipanteGrupo.query.filter_by(grupo_id=grupo_id, usuario_id=current_user.id).first_or_404()
            
            if not membresia.reglas_aceptadas:
                if aceptar_reglas:
                    membresia.reglas_aceptadas = True
                else:
                    flash('Debes aceptar el reglamento del grupo antes de predecir.', 'warning')
                    return redirect(url_for('main.jugar_existente', partido_id=partido.id))
                
            valor_prediccion = f"{goles_local}-{goles_visitante}"
            
            # Buscar si ya existe una predicción previa para este grupo
            prediccion_previa = Prediccion.query.filter_by(
                partido_id=partido.id,
                usuario_id=current_user.id,
                grupo_id=grupo_id
            ).first()
            
            if prediccion_previa:
                prediccion_previa.valor_prediccion = valor_prediccion
                if comprobante:
                    prediccion_previa.comprobante_pago = comprobante
                if recibo_path:
                    prediccion_previa.comprobante_path = recibo_path
                mensaje = '¡Tu predicción ha sido modificada exitosamente!'
            else:
                nueva_prediccion = Prediccion(
                    partido_id=partido.id,
                    usuario_id=current_user.id,
                    grupo_id=grupo_id,
                    valor_prediccion=valor_prediccion,
                    comprobante_pago=comprobante,
                    comprobante_path=recibo_path
                )
                db.session.add(nueva_prediccion)
                
                # Inicializar caja en Por Pagar o Por Validar
                nueva_caja = PartidoParticipanteCaja(
                    partido_id=partido.id,
                    grupo_id=grupo_id,
                    usuario_id=current_user.id,
                    estado_pago='Por Validar' if recibo_path or comprobante == 'Efectivo' else 'Por Pagar'
                )
                db.session.add(nueva_caja)
                mensaje = '¡Tu predicción ha sido registrada exitosamente! Informa a tu Tesorero.'
            
            try:
                db.session.commit()
                flash(mensaje, 'success')
                return redirect(url_for('main.ver_partido', grupo_id=grupo_id, partido_id=partido.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al procesar la predicción: {str(e)}', 'danger')
                return redirect(url_for('main.jugar_existente', partido_id=partido.id))

    return render_template(
        'jugar_existente.html',
        partido=partido,
        grupos_disponibles=mis_grupos,
        preds_map=preds_map
    )

    return render_template(
        'jugar_existente.html',
        partido=partido,
        grupos_disponibles=grupos_disponibles
    )


@bp.route('/jugar/<int:partido_id>/crear', methods=['GET', 'POST'])
@login_required
def jugar_crear(partido_id):
    """Permite fundar una nueva comunidad cerrada y registrar la predicción del partido. [Willys_IA]"""
    partido = Partido.query.get_or_404(partido_id)
    
    if partido.estado != 'Abierto':
        flash('Las predicciones para este partido ya están cerradas.', 'warning')
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        # Creación express
        nombre_visual = request.form.get('nombre_visual', '').strip()
        nombre_grupo = request.form.get('nombre_grupo', '').strip()
        balones_aporte = request.form.get('balones_aporte', 10, type=int)
        balon_equivalencia = request.form.get('balon_equivalencia', 1.0, type=float)
        moneda_codigo = request.form.get('moneda_codigo', 'Bs').strip()
        tipo_juego = request.form.get('tipo_juego', 'Marcador')
        politica_pozo = request.form.get('politica_pozo', 'Acumular')
        limite_pago = request.form.get('limite_pago', 60, type=int)
        acuerdos_especiales = request.form.get('acuerdos_especiales', '').strip()
        datos_pago = request.form.get('datos_pago', '').strip()
        
        # Goles de la predicción express
        goles_local = request.form.get('goles_local', '').strip()
        goles_visitante = request.form.get('goles_visitante', '').strip()
        aceptar_reglas = request.form.get('aceptar_reglas') == 'on'
        
        if not nombre_visual:
            flash('Tu apodo o nombre de juego es obligatorio.', 'danger')
            return redirect(url_for('main.jugar_crear', partido_id=partido.id))
            
        if not nombre_grupo:
            flash('El nombre del grupo es obligatorio.', 'danger')
            return redirect(url_for('main.jugar_crear', partido_id=partido.id))
            
        # Actualizar apodo o nombre de juego del usuario en su perfil
        current_user.nombre = nombre_visual
            
        if goles_local == '' or goles_visitante == '':
            flash('Debes ingresar tu pronóstico de goles para el partido.', 'danger')
            return redirect(url_for('main.jugar_crear', partido_id=partido.id))
            
        if not aceptar_reglas:
            flash('Debes aceptar el reglamento del grupo para crearlo y jugar.', 'danger')
            return redirect(url_for('main.jugar_crear', partido_id=partido.id))
            
        codigo_invitacion = generar_codigo_invitacion(nombre_grupo, partido=partido)
        
        # Procesar la subida y compresión del código QR de cobro bancario [Willys_IA]
        qr_file = request.files.get('qr_image')
        qr_path = None
        if qr_file and qr_file.filename != '':
            qr_path = guardar_imagen_optimizada(qr_file, 'qrs')
            
        nuevo_grupo = Grupo(
            nombre=nombre_grupo,
            descripcion=f"Grupo express creado para el partido {partido.equipo_local} vs {partido.equipo_visitante}",
            admin_id=current_user.id,
            tesorero_id=current_user.id,
            balones_aporte=balones_aporte,
            balon_equivalencia=balon_equivalencia,
            moneda_codigo=moneda_codigo,
            tipo_juego=tipo_juego,
            politica_pozo_vacio=politica_pozo,
            limite_pago_minutos=limite_pago,
            acuerdos_especiales=acuerdos_especiales,
            codigo_invitacion=codigo_invitacion,
            datos_pago_tesorero=datos_pago,
            estado_juego='Activo',
            qr_pago_path=qr_path
        )
        
        try:
            db.session.add(nuevo_grupo)
            db.session.flush()
            
            # Inscribir al admin
            membresia = ParticipanteGrupo(
                grupo_id=nuevo_grupo.id,
                usuario_id=current_user.id,
                reglas_aceptadas=True
            )
            db.session.add(membresia)
            
            # Crear predicción
            valor_prediccion = f"{goles_local}-{goles_visitante}"
            nueva_prediccion = Prediccion(
                partido_id=partido.id,
                usuario_id=current_user.id,
                grupo_id=nuevo_grupo.id,
                valor_prediccion=valor_prediccion
            )
            db.session.add(nueva_prediccion)
            
            # Registrar caja para el tesorero (admin) en estado Por Pagar
            nueva_caja = PartidoParticipanteCaja(
                partido_id=partido.id,
                grupo_id=nuevo_grupo.id,
                usuario_id=current_user.id,
                estado_pago='Por Pagar'
            )
            db.session.add(nueva_caja)
            
            db.session.commit()
            flash(f'¡Grupo "{nuevo_grupo.nombre}" y predicción creados con éxito! Comparte el código de invitación: {nuevo_grupo.codigo_invitacion}', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al procesar el grupo express: {str(e)}', 'danger')
            return redirect(url_for('main.jugar_crear', partido_id=partido.id))

    return render_template(
        'jugar_crear.html',
        partido=partido
    )

# ==========================================
# RUTAS DE SOPORTE PARA VISTAS (FUTURAS FASES)
# ==========================================

@bp.route('/grupo/<int:grupo_id>')
@login_required
def ver_grupo(grupo_id):
    """Vista detallada del grupo de juego predictivo. [Willys_IA]"""
    grupo = Grupo.query.get_or_404(grupo_id)
    
    # Obtener membresia del usuario actual en este grupo
    membresia_usuario = ParticipanteGrupo.query.filter_by(
        grupo_id=grupo.id, 
        usuario_id=current_user.id
    ).first_or_404()
    
    # Obtener todos los participantes ordenados por su balance de Balones (Ranking)
    participantes = ParticipanteGrupo.query.filter_by(grupo_id=grupo.id).order_by(
        ParticipanteGrupo.balance_balones.desc()
    ).all()
    
    # Obtener todos los partidos del sistema para el fixture global
    # En produccion se cargaria el fixture oficial del mundial
    partidos = Partido.query.order_by(Partido.fecha_hora.asc()).all()
    
    colores_uniformes = {
        'Bolivia': '#007A33',
        'Argentina': '#75AADB',
        'Mexico': '#006847',
        'Estados Unidos': '#0A2342',
        'Espana': '#C60B1E',
        'Alemania': '#FFFFFF',
        'Brasil': '#FEDF00',
        'Italia': '#002F6C'
    }
    
    return render_template(
        'grupo.html', 
        grupo=grupo, 
        membresia=membresia_usuario, 
        participantes=participantes,
        partidos=partidos,
        colores_uniformes=colores_uniformes
    )


@bp.route('/grupo/<int:grupo_id>/editar-reglas', methods=['GET', 'POST'])
@login_required
def editar_reglas(grupo_id):
    """Permite al administrador modificar las consideraciones y el reglamento del grupo. [Willys_IA]"""
    grupo = Grupo.query.get_or_404(grupo_id)
    
    # Validar que el usuario actual sea el administrador o tesorero del grupo
    if current_user.id != grupo.admin_id and current_user.id != grupo.tesorero_id:
        flash('No tienes permisos para modificar las reglas de este grupo.', 'danger')
        return redirect(url_for('main.ver_grupo', grupo_id=grupo.id))
        
    if request.method == 'POST':
        balones_aporte = request.form.get('balones_aporte', type=int)
        balon_equivalencia = request.form.get('balon_equivalencia', type=float)
        moneda_codigo = request.form.get('moneda_codigo', '').strip()
        tipo_juego = request.form.get('tipo_juego', '').strip()
        politica_pozo = request.form.get('politica_pozo', '').strip()
        limite_pago = request.form.get('limite_pago', type=int)
        datos_pago = request.form.get('datos_pago', '').strip()
        acuerdos_especiales = request.form.get('acuerdos_especiales', '').strip()
        
        # Validar y actualizar
        if balones_aporte is not None:
            grupo.balones_aporte = balones_aporte
        if balon_equivalencia is not None:
            grupo.balon_equivalencia = balon_equivalencia
        if moneda_codigo:
            grupo.moneda_codigo = moneda_codigo
        if tipo_juego:
            grupo.tipo_juego = tipo_juego
        if politica_pozo:
            grupo.politica_pozo_vacio = politica_pozo
        if limite_pago is not None:
            grupo.limite_pago_minutos = limite_pago
        grupo.datos_pago_tesorero = datos_pago
        grupo.acuerdos_especiales = acuerdos_especiales
        
        # Procesar la subida y compresión del código QR de pagos bancarios [Willys_IA]
        qr_file = request.files.get('qr_image')
        if qr_file and qr_file.filename != '':
            ruta_optimizada = guardar_imagen_optimizada(qr_file, 'qrs')
            if ruta_optimizada:
                grupo.qr_pago_path = ruta_optimizada
                
        partido_id = request.form.get('partido_id', type=int) or request.args.get('partido_id', type=int)
        
        try:
            db.session.commit()
            flash('¡El reglamento del grupo ha sido actualizado exitosamente!', 'success')
            if partido_id:
                return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido_id))
            return redirect(url_for('main.ver_grupo', grupo_id=grupo.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar los cambios: {str(e)}', 'danger')
            
    return render_template('editar_reglas.html', grupo=grupo)


@bp.route('/grupo/<int:grupo_id>/aceptar-reglas', methods=['POST'])
@login_required
def aceptar_reglas(grupo_id):
    """Registra la firma de aceptacion de consideraciones del reglamento del grupo. [Willys_IA]"""
    membresia = ParticipanteGrupo.query.filter_by(
        grupo_id=grupo_id, 
        usuario_id=current_user.id
    ).first_or_404()
    
    membresia.reglas_aceptadas = True
    
    try:
        db.session.commit()
        flash('¡Has aceptado las consideraciones del grupo! Ya estas habilitado para registrar predicciones.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al aceptar las reglas: {str(e)}', 'danger')
        
    return redirect(url_for('main.ver_grupo', grupo_id=grupo_id))


# ==========================================
# 3. CICLO DE PREDICCIONES Y CONCILIACION [Willys_IA]
# ==========================================

@bp.route('/grupo/<int:grupo_id>/partido/<int:partido_id>', methods=['GET', 'POST'])
@login_required
def ver_partido(grupo_id, partido_id):
    """Vista detallada de un partido, predicciones e interfaces del administrador. [Willys_IA]"""
    grupo = Grupo.query.get_or_404(grupo_id)
    partido = Partido.query.get_or_404(partido_id)
    
    # Validar membresia del usuario
    membresia = ParticipanteGrupo.query.filter_by(
        grupo_id=grupo.id, 
        usuario_id=current_user.id
    ).first_or_404()
    
    # Procesar registro o edicion de la prediccion del usuario
    if request.method == 'POST':
        # Validar si el jugador ya acepto el reglamento
        if not membresia.reglas_aceptadas:
            flash('Debes aceptar el reglamento del grupo antes de predecir.', 'danger')
            return redirect(url_for('main.ver_grupo', grupo_id=grupo.id))
            
        # El partido debe estar Abierto para registrar predicciones
        if partido.estado != 'Abierto':
            flash('Las predicciones para este partido ya estan cerradas.', 'warning')
            return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
            
        valor_prediccion = request.form.get('valor_prediccion', '').strip()
        comprobante = request.form.get('comprobante_pago', '').strip()
        
        # Procesar y optimizar la imagen del recibo de transferencia subido por el jugador [Willys_IA]
        recibo_file = request.files.get('comprobante_image')
        recibo_path = None
        if recibo_file and recibo_file.filename != '':
            recibo_path = guardar_imagen_optimizada(recibo_file, 'comprobantes')
            
        if not valor_prediccion:
            flash('Debes ingresar tu prediccion.', 'warning')
            return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
            
        # Buscar si ya existe una prediccion previa para este partido
        prediccion_previa = Prediccion.query.filter_by(
            partido_id=partido.id,
            usuario_id=current_user.id,
            grupo_id=grupo.id
        ).first()
        
        # Obtener o crear el registro de caja para este partido
        caja_existente = PartidoParticipanteCaja.query.filter_by(
            partido_id=partido.id,
            grupo_id=grupo.id,
            usuario_id=current_user.id
        ).first()
        
        if prediccion_previa:
            prediccion_previa.valor_prediccion = valor_prediccion
            prediccion_previa.comprobante_pago = comprobante
            if recibo_path:
                prediccion_previa.comprobante_path = recibo_path
            
            # Si el usuario modifica su predicción o comprobante, reiniciamos el estado de caja por auditoría [Willys_IA]
            if caja_existente:
                caja_existente.estado_pago = 'Por Validar' if recibo_path or comprobante == 'Efectivo' else 'Por Pagar'
        else:
            nueva_prediccion = Prediccion(
                partido_id=partido.id,
                usuario_id=current_user.id,
                grupo_id=grupo.id,
                valor_prediccion=valor_prediccion,
                comprobante_pago=comprobante,
                comprobante_path=recibo_path
            )
            db.session.add(nueva_prediccion)
            
            # Inicializar caja del jugador en Por Pagar o Por Validar para este partido (espera conciliacion)
            if not caja_existente:
                nueva_caja = PartidoParticipanteCaja(
                    partido_id=partido.id,
                    grupo_id=grupo.id,
                    usuario_id=current_user.id,
                    estado_pago='Por Validar' if recibo_path or comprobante == 'Efectivo' else 'Por Pagar'
                )
                db.session.add(nueva_caja)
            else:
                caja_existente.estado_pago = 'Por Validar' if recibo_path or comprobante == 'Efectivo' else 'Por Pagar'
                
        try:
            db.session.commit()
            flash('¡Tu prediccion ha sido registrada exitosamente! Informa a tu Tesorero.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la prediccion: {str(e)}', 'danger')
            
        return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
        
    # Obtener la prediccion del usuario actual para este partido
    mi_prediccion = Prediccion.query.filter_by(
        partido_id=partido.id,
        usuario_id=current_user.id,
        grupo_id=grupo.id
    ).first()
    
    # Obtener todas las predicciones registradas para el partido en este grupo
    todas_predicciones = Prediccion.query.filter_by(
        partido_id=partido.id,
        grupo_id=grupo.id
    ).all()
    
    # Obtener la planilla de caja (conciliaciones)
    planilla_caja = PartidoParticipanteCaja.query.filter_by(
        partido_id=partido.id,
        grupo_id=grupo.id
    ).all()
    
    # Obtener todas las membresías activas del grupo para listar a todos en la tabla única [Willys_IA]
    participantes_grupo = ParticipanteGrupo.query.filter_by(grupo_id=grupo.id).all()
    
    # Mapeo de estado de pago para la vista
    caja_map = {c.usuario_id: c.estado_pago for c in planilla_caja}
    
    colores_uniformes = {
        'Bolivia': '#007A33',
        'Argentina': '#75AADB',
        'Mexico': '#006847',
        'Estados Unidos': '#0A2342',
        'Espana': '#C60B1E',
        'Alemania': '#FFFFFF',
        'Brasil': '#FEDF00',
        'Italia': '#002F6C'
    }
    
    # Verificar si el partido ya fue liquidado en este grupo
    liquidaciones = LiquidacionHistorial.query.filter_by(
        partido_id=partido.id,
        grupo_id=grupo.id
    ).all()
    partido_liquidado = len(liquidaciones) > 0
    resumen_liquidacion = {
        'ganadores': len([l for l in liquidaciones if l.gano]),
        'premio_total': sum([l.ganancia_neta + l.monto_aportado for l in liquidaciones if l.gano]) if liquidaciones else 0
    } if partido_liquidado else None

    return render_template(
        'partido.html',
        grupo=grupo,
        partido=partido,
        mi_prediccion=mi_prediccion,
        todas_predicciones=todas_predicciones,
        caja_map=caja_map,
        planilla_caja=planilla_caja,
        participantes_grupo=participantes_grupo,
        colores_uniformes=colores_uniformes,
        partido_liquidado=partido_liquidado,
        resumen_liquidacion=resumen_liquidacion
    )


@bp.route('/grupo/<int:grupo_id>/partido/<int:partido_id>/retirar', methods=['POST'])
@login_required
def retirar_prediccion(grupo_id, partido_id):
    """Permite al participante retirar su predicción y registro de caja para este partido (No jugar). [Willys_IA]"""
    grupo = Grupo.query.get_or_404(grupo_id)
    partido = Partido.query.get_or_404(partido_id)
    
    # Validar que el partido esté abierto
    if partido.estado != 'Abierto':
        flash('No puedes retirar tu predicción si las predicciones ya están cerradas.', 'warning')
        return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
        
    # Eliminar la predicción del usuario
    from app.models import Prediccion
    prediccion = Prediccion.query.filter_by(
        partido_id=partido.id,
        usuario_id=current_user.id,
        grupo_id=grupo.id
    ).first()
    
    if prediccion:
        db.session.delete(prediccion)
        
    # Eliminar el registro de caja para este partido
    caja = PartidoParticipanteCaja.query.filter_by(
        partido_id=partido.id,
        grupo_id=grupo.id,
        usuario_id=current_user.id
    ).first()
    
    if caja:
        db.session.delete(caja)
        
    try:
        db.session.commit()
        flash('Has retirado tu participación (No jugar) para este partido.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al retirar la participación: {str(e)}', 'danger')
        
    return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))


@bp.route('/api/grupo/<int:grupo_id>/partido/<int:partido_id>/conciliar', methods=['POST'])
@login_required
def conciliar_pago(grupo_id, partido_id):
    """API asincrona para que el Tesorero concilie pagos de aportes offline en Balones. [Willys_IA]"""
    grupo = Grupo.query.get_or_404(grupo_id)
    partido = Partido.query.get_or_404(partido_id)
    
    # Validar que el usuario actual sea el administrador o tesorero del grupo
    if current_user.id != grupo.admin_id and current_user.id != grupo.tesorero_id:
        return jsonify({'success': False, 'error': 'No posees permisos de Tesorero.'}), 403
        
    data = request.get_json() or {}
    usuario_id = data.get('usuario_id')
    nuevo_estado = data.get('estado') # 'Por Pagar', 'Por Validar', o 'Participa'
    
    if not usuario_id or nuevo_estado not in ['Por Pagar', 'Por Validar', 'Participa']:
        return jsonify({'success': False, 'error': 'Parametros invalidos.'}), 400
        
    caja = PartidoParticipanteCaja.query.filter_by(
        partido_id=partido.id,
        grupo_id=grupo.id,
        usuario_id=usuario_id
    ).first()
    
    if not caja:
        return jsonify({'success': False, 'error': 'No existe un registro de caja para este participante.'}), 404
        
    caja.estado_pago = nuevo_estado
    caja.marcado_por = current_user.id
    caja.fecha_marcado = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'estado': nuevo_estado, 'marcado_por': current_user.nombre})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/grupo/<int:grupo_id>/partido/<int:partido_id>/subir_comprobante', methods=['POST'])
@login_required
def subir_comprobante(grupo_id, partido_id):
    """API para que el jugador suba su comprobante o reporte pago en efectivo. [Willys_IA]"""
    grupo = Grupo.query.get_or_404(grupo_id)
    partido = Partido.query.get_or_404(partido_id)
    
    caja = PartidoParticipanteCaja.query.filter_by(
        partido_id=partido.id,
        grupo_id=grupo.id,
        usuario_id=current_user.id
    ).first()
    
    if not caja:
        return jsonify({'success': False, 'error': 'No tienes participación en este partido.'}), 404
        
    metodo = request.form.get('metodo') # 'efectivo' o 'qr'
    
    from app.models import Prediccion
    prediccion = Prediccion.query.filter_by(
        partido_id=partido.id,
        usuario_id=current_user.id,
        grupo_id=grupo.id
    ).first()
    
    if not prediccion:
        return jsonify({'success': False, 'error': 'No tienes predicción registrada.'}), 404

    if metodo == 'efectivo':
        prediccion.comprobante_pago = 'Pago en Efectivo (Pendiente de entrega)'
        caja.estado_pago = 'Por Validar'
    else:
        recibo_file = request.files.get('comprobante_image')
        if recibo_file and recibo_file.filename != '':
            recibo_path = guardar_imagen_optimizada(recibo_file, 'comprobantes')
            if recibo_path:
                prediccion.comprobante_path = recibo_path
                prediccion.comprobante_pago = 'Transferencia Digital/QR'
                caja.estado_pago = 'Por Validar'
            else:
                return jsonify({'success': False, 'error': 'Error al procesar la imagen.'}), 400
        else:
            return jsonify({'success': False, 'error': 'No se recibió ninguna imagen.'}), 400
            
    try:
        db.session.commit()
        return jsonify({'success': True, 'estado': 'Por Validar', 'mensaje': 'Comprobante enviado al Tesorero.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# 4. MOTOR DE LIQUIDACION Y COMISIONES [Willys_IA]
# ==========================================

@bp.route('/api/grupo/<int:grupo_id>/partido/<int:partido_id>/liquidar', methods=['POST'])
@login_required
def liquidar_partido_endpoint(grupo_id, partido_id):
    """Permite al Admin del Grupo ingresar el marcador y liquidar el partido de forma automatica. [Willys_IA]"""
    grupo = Grupo.query.get_or_404(grupo_id)
    partido = Partido.query.get_or_404(partido_id)
    
    # Validar permisos (Solo el admin del grupo puede liquidar)
    if current_user.id != grupo.admin_id:
        return jsonify({'success': False, 'error': 'No tienes permisos de Administrador del Grupo para liquidar.'}), 403
        
    marcador = request.form.get('marcador', '').strip()
    
    if not marcador or '-' not in marcador:
        flash('Debes ingresar un marcador valido (Ej: 2-1).', 'warning')
        return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
        
    # Guardar marcador oficial y cambiar estado
    partido.marcador = marcador
    partido.estado = 'Terminado' # Primero pasa a Terminado para liquidar
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar el marcador: {str(e)}', 'danger')
        return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))
        
    # Invocar al motor de liquidacion
    from app.logic import liquidar_partido_grupo
    resultado = liquidar_partido_grupo(grupo.id, partido.id)
    
    if resultado['success']:
        partido.estado = 'Liquidado'
        db.session.commit()
        flash(f'¡Partido liquidado con exito! Balones distribuidos: {resultado["balones_recaudados"]} ⚽. Comision generada: {resultado["comision_balones"]} ⚽.', 'success')
    else:
        flash(f'Error al procesar la liquidacion contable: {resultado["error"]}', 'danger')
        
    return redirect(url_for('main.ver_partido', grupo_id=grupo.id, partido_id=partido.id))


@bp.route('/admin/comisiones', methods=['GET'])
@login_required
def admin_comisiones():
    """Panel global de control de comisiones de ScoreTracker (Exclusivo App Admin). [Willys_IA]"""
    # En produccion se validaria que el current_user sea Administrador Global del sistema.
    # Para el MVP, asumimos que todos los usuarios registrados pueden consultar para pruebas,
    # pero limitamos a que sea visible la planilla.
    from app.models import ComisionHistorial
    
    comisiones_pendientes = ComisionHistorial.query.filter_by(estado_pago='Pendiente').all()
    comisiones_pagadas = ComisionHistorial.query.filter_by(estado_pago='Pagado').all()
    
    return render_template(
        'admin_comisiones.html',
        pendientes=comisiones_pendientes,
        pagadas=comisiones_pagadas
    )


@bp.route('/admin/comisiones/<int:comision_id>/pagar', methods=['POST'])
@login_required
def conciliar_comision_app(comision_id):
    """Marca una comision de grupo como PAGADA y desbloquea el grupo para el siguiente partido. [Willys_IA]"""
    from app.models import ComisionHistorial
    
    comision = ComisionHistorial.query.get_or_404(comision_id)
    comision.estado_pago = 'Pagado'
    
    # BUSCAR EL SIGUIENTE PARTIDO PROGRAMADO DEL GRUPO Y PASARLO A 'ABIERTO'
    # Esta es la automatizacion radical para abrir apuestas sucesivas una vez pagada la comision.
    grupo_id = comision.grupo_id
    
    # Buscar el proximo partido en estado Programado
    proximo_partido = Partido.query.filter(
        Partido.estado == 'Programado'
    ).order_by(Partido.fecha_hora.asc()).first()
    
    if proximo_partido:
        proximo_partido.estado = 'Abierto'
        
    try:
        db.session.commit()
        flash(f'¡Comision #{comision.id} validada con exito! Se ha habilitado y abierto el siguiente partido para predicciones.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al conciliar la comision: {str(e)}', 'danger')
        
    return redirect(url_for('main.admin_comisiones'))

@bp.route('/fix-lugar', methods=['GET'])
def fix_lugar():
    partidos = Partido.query.all()
    for p in partidos:
        if not p.lugar:
            p.lugar = 'Estadio ' + p.equipo_local
    db.session.commit()
    return "Fix aplicado exitosamente"

@bp.route('/clear-data', methods=['GET'])
def clear_data():
    from app.models import Grupo, ParticipanteGrupo, Prediccion, PartidoParticipanteCaja, LiquidacionHistorial, ComisionHistorial
    db.session.query(LiquidacionHistorial).delete()
    db.session.query(ComisionHistorial).delete()
    db.session.query(PartidoParticipanteCaja).delete()
    db.session.query(Prediccion).delete()
    db.session.query(ParticipanteGrupo).delete()
    db.session.query(Grupo).delete()
    db.session.commit()
    return "Datos de juego limpiados exitosamente."

@bp.route('/api/grupo/<int:grupo_id>/partido/<int:partido_id>/liquidar', methods=['POST'])
@login_required
def liquidar_partido(grupo_id, partido_id):
    """
    Motor central contable. Finaliza el partido, consolida el pozo y lo distribuye
    entre los ganadores. Si no hay ganadores o nadie adivina el marcador exacto,
    acumula el pozo de acuerdo a las consideraciones de la empresa. [Willys_IA]
    """
    grupo = Grupo.query.get_or_404(grupo_id)
    if current_user.id not in [grupo.admin_id, grupo.tesorero_id]:
        return jsonify({'success': False, 'error': 'No tienes permiso para liquidar este partido.'})
        
    partido = Partido.query.get_or_404(partido_id)
    
    ya_liquidado = LiquidacionHistorial.query.filter_by(partido_id=partido.id, grupo_id=grupo.id).first()
    if ya_liquidado:
        return jsonify({'success': False, 'error': 'Este partido ya fue liquidado en este grupo.'})
        
    datos = request.json
    goles_local_real = datos.get('goles_local')
    goles_visitante_real = datos.get('goles_visitante')
    
    if goles_local_real is None or goles_visitante_real is None:
        return jsonify({'success': False, 'error': 'Faltan los goles del partido.'})
        
    try:
        goles_local_real = int(goles_local_real)
        goles_visitante_real = int(goles_visitante_real)
    except ValueError:
        return jsonify({'success': False, 'error': 'Los goles deben ser números válidos.'})
        
    marcador_real = f"{goles_local_real}-{goles_visitante_real}"
    
    cajas_validas = PartidoParticipanteCaja.query.filter_by(partido_id=partido.id, grupo_id=grupo.id, estado_pago='Participa').all()
    if not cajas_validas:
        return jsonify({'success': False, 'error': 'No hay jugadores con pago validado para participar del pozo.'})
        
    usuarios_validos_ids = [c.usuario_id for c in cajas_validas]
    aporte = int(grupo.balones_aporte)
    pozo_base = len(usuarios_validos_ids) * aporte
    pozo_total = pozo_base + int(grupo.pozo_acumulado)
    
    comision_porcentaje = float(grupo.comision_porcentaje) / 100.0
    comision_balones = int(pozo_total * comision_porcentaje)
    pozo_neto = pozo_total - comision_balones
    
    predicciones = Prediccion.query.filter(
        Prediccion.partido_id == partido.id,
        Prediccion.grupo_id == grupo.id,
        Prediccion.usuario_id.in_(usuarios_validos_ids)
    ).all()
    
    ganadores = []
    for pred in predicciones:
        if pred.valor_prediccion == marcador_real:
            ganadores.append(pred)
            
    if len(ganadores) > 0:
        premio_por_ganador = pozo_neto // len(ganadores)
        sobrante = pozo_neto % len(ganadores)
        comision_real = comision_balones + sobrante
        
        nueva_comision = ComisionHistorial(
            grupo_id=grupo.id,
            partido_id=partido.id,
            monto_balones=comision_real,
            monto_dinero_real=float(comision_real) * float(grupo.balon_equivalencia)
        )
        db.session.add(nueva_comision)
        grupo.pozo_acumulado = 0
    else:
        grupo.pozo_acumulado = pozo_total
        premio_por_ganador = 0
        comision_real = 0
        
    ganadores_ids = [g.usuario_id for g in ganadores]
    
    for c in cajas_validas:
        usuario_id = c.usuario_id
        pg = ParticipanteGrupo.query.filter_by(grupo_id=grupo.id, usuario_id=usuario_id).first()
        
        if usuario_id in ganadores_ids:
            ganancia_neta = premio_por_ganador - aporte
            gano = True
        else:
            ganancia_neta = -aporte
            gano = False
            
        pg.balance_balones += ganancia_neta
        
        historial = LiquidacionHistorial(
            partido_id=partido.id,
            usuario_id=usuario_id,
            grupo_id=grupo.id,
            monto_aportado=aporte,
            gano=gano,
            ganancia_neta=ganancia_neta
        )
        db.session.add(historial)
        
    try:
        if not partido.marcador:
            partido.marcador = marcador_real
            partido.estado = 'Terminado'
        db.session.commit()
        return jsonify({
            'success': True, 
            'mensaje': 'Liquidación procesada con éxito.',
            'ganadores': len(ganadores),
            'premio_individual': premio_por_ganador,
            'pozo_acumulado_resultante': grupo.pozo_acumulado
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})




