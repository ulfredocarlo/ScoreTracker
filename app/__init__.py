import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instanciacion de extensiones globales de Flask
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    """Factory Pattern para inicializar la aplicacion ScoreTracker. [Willys_IA]"""
    app = Flask(__name__)
    
    # Cargar configuraciones del diccionario
    from config import config_dict
    app.config.from_object(config_dict.get(config_name, config_dict['default']))
    
    # Inicializacion de extensiones con el contexto de la app
    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor, inicia sesion para acceder a este juego.'
    login_manager.login_message_category = 'warning'
    
    # Registro de Blueprints
    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Registro del cargador de usuario para Flask-Login
    from app.models import Usuario
    
    @login_manager.user_loader
    def load_user(user_id):
        """Cargador de usuario requerido por Flask-Login. [Willys_IA]"""
        return Usuario.query.get(int(user_id))
        
    @app.context_processor
    def utility_processor():
        def render_jersey(equipo, size=44):
            """
            Genera un SVG vector premium representando la camiseta oficial de juego 2026. [Willys_IA]
            Contiene patrones de rayas, graficos aztecas, paneles laterales y sombras de neon.
            """
            import unicodedata
            def clean_name(s):
                if not s: return ""
                return "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()
            
            eq = clean_name(equipo)
            
            # Parametros de disenadores HSL y SVG
            body_fill = "#ffffff"
            sleeve_color = "#ffffff"
            cuff_color = "#ffffff"
            collar_color = "#ffffff"
            border_color = "#dddddd"
            side_panels = ""
            crest_color = "#FEDF00"
            glow_color = "transparent"
            
            if "mexico" in eq:
                body_fill = "url(#pattern-mx)"
                sleeve_color = "#006847"
                cuff_color = "#D52B1E"
                collar_color = "#D52B1E"
                border_color = "#003b28"
                glow_color = "#008f62"
            elif "argentina" in eq:
                body_fill = "url(#stripes-ar)"
                sleeve_color = "#75AADB"
                cuff_color = "#FFFFFF"
                collar_color = "#FFFFFF"
                border_color = "#4d8bbd"
                glow_color = "#75AADB"
            elif "estados unidos" in eq or "usa" in eq or "united states" in eq:
                body_fill = "#FFFFFF"
                sleeve_color = "#FFFFFF"
                cuff_color = "#0A2342"
                collar_color = "#0A2342"
                border_color = "#cccccc"
                side_panels = '<path d="M 29 50 L 32 50 L 32 85 L 29 85 Z" fill="#D52B1E" /><path d="M 71 50 L 68 50 L 68 85 L 71 85 Z" fill="#D52B1E" />'
                crest_color = "#0A2342"
                glow_color = "#0A2342"
            elif "canada" in eq:
                body_fill = "#FF0000"
                sleeve_color = "#FF0000"
                cuff_color = "#FFFFFF"
                collar_color = "#FFFFFF"
                border_color = "#aa0000"
                side_panels = '<path d="M 29 40 L 32 40 L 32 85 L 29 85 Z" fill="#FFFFFF" /><path d="M 71 40 L 68 40 L 68 85 L 71 85 Z" fill="#FFFFFF" />'
                crest_color = "#FFFFFF"
                glow_color = "#FF0000"
            elif "brasil" in eq or "brazil" in eq:
                body_fill = "#FEDF00"
                sleeve_color = "#FEDF00"
                cuff_color = "#009B3A"
                collar_color = "#009B3A"
                border_color = "#d4bc00"
                crest_color = "#002776"
                glow_color = "#FEDF00"
            elif "sudafrica" in eq or "south africa" in eq:
                body_fill = "#FFCC00"
                sleeve_color = "#FFCC00"
                cuff_color = "#006847"
                collar_color = "#006847"
                border_color = "#cfa500"
                side_panels = '<path d="M 33 28 L 50 85 L 45 85 Z" fill="#006847" />'
                crest_color = "#006847"
                glow_color = "#FFCC00"
            elif "serbia" in eq:
                body_fill = "#C60B1E"
                sleeve_color = "#C60B1E"
                cuff_color = "#FEDF00"
                collar_color = "#FFFFFF"
                border_color = "#940010"
                crest_color = "#FEDF00"
                glow_color = "#C60B1E"
            elif "islandia" in eq or "iceland" in eq:
                body_fill = "#005B94"
                sleeve_color = "#005B94"
                cuff_color = "#FFFFFF"
                collar_color = "#D52B1E"
                border_color = "#003e66"
                side_panels = '<path d="M 33 28 L 33 85 L 36 85 Z" fill="#D52B1E" />'
                crest_color = "#FFFFFF"
                glow_color = "#005B94"
            elif "paraguay" in eq:
                body_fill = "url(#stripes-py)"
                sleeve_color = "#D52B1E"
                cuff_color = "#FFFFFF"
                collar_color = "#002F6C"
                border_color = "#ab1d13"
                crest_color = "#FEDF00"
                glow_color = "#D52B1E"
            elif "marruecos" in eq or "morocco" in eq:
                body_fill = "#C1272D"
                sleeve_color = "#C1272D"
                cuff_color = "#006241"
                collar_color = "#006241"
                border_color = "#91181c"
                side_panels = '<path d="M 29 45 L 71 45 L 71 52 L 29 52 Z" fill="#006241" />'
                crest_color = "#FEDF00"
                glow_color = "#C1272D"
            elif "bosnia" in eq:
                body_fill = "#002F6C"
                sleeve_color = "#002F6C"
                cuff_color = "#FEDF00"
                collar_color = "#FEDF00"
                border_color = "#001d42"
                side_panels = '<path d="M 33 40 L 71 70 L 71 85 L 33 55 Z" fill="#FEDF00" opacity="0.8" />'
                crest_color = "#FFFFFF"
                glow_color = "#002F6C"
            else:
                # Caso generico
                body_fill = "#E2E8F0"
                sleeve_color = "#CBD5E1"
                cuff_color = "#94A3B8"
                collar_color = "#64748B"
                border_color = "#94A3B8"
                glow_color = "transparent"

            svg_str = f"""
            <svg viewBox="0 0 100 100" class="soccer-jersey" width="{size}" height="{size}" style="filter: drop-shadow(0 0 6px {glow_color}); vertical-align: middle; display: inline-block;">
                <defs>
                    <pattern id="stripes-ar" width="16" height="100" patternUnits="userSpaceOnUse">
                        <rect width="8" height="100" fill="#75AADB" />
                        <rect x="8" width="8" height="100" fill="#FFFFFF" />
                    </pattern>
                    <pattern id="stripes-py" width="16" height="100" patternUnits="userSpaceOnUse">
                        <rect width="8" height="100" fill="#D52B1E" />
                        <rect x="8" width="8" height="100" fill="#FFFFFF" />
                    </pattern>
                    <pattern id="pattern-mx" width="20" height="20" patternUnits="userSpaceOnUse">
                        <rect width="20" height="20" fill="#006847" />
                        <path d="M 0 10 L 10 0 L 20 10 L 10 20 Z" fill="none" stroke="#004e35" stroke-width="1.2" />
                        <path d="M 10 10 L 20 0 M 10 10 L 0 0 M 10 10 L 20 20 M 10 10 L 0 20" fill="none" stroke="#004e35" stroke-width="0.6" />
                    </pattern>
                </defs>
                <path d="M 33 28 L 15 45 L 25 55 L 38 40 Z" fill="{sleeve_color}" stroke="{border_color}" stroke-width="1.5" />
                <path d="M 67 28 L 85 45 L 75 55 L 62 40 Z" fill="{sleeve_color}" stroke="{border_color}" stroke-width="1.5" />
                <path d="M 15 45 L 25 55" stroke="{cuff_color}" stroke-width="3" stroke-linecap="round" />
                <path d="M 85 45 L 75 55" stroke="{cuff_color}" stroke-width="3" stroke-linecap="round" />
                <path d="M 33 28 L 67 28 L 71 85 L 29 85 Z" fill="{body_fill}" stroke="{border_color}" stroke-width="1.5" />
                {side_panels}
                <path d="M 43 28 Q 50 38 57 28" fill="none" stroke="{collar_color}" stroke-width="3.5" stroke-linecap="round" />
                <circle cx="39" cy="40" r="3.5" fill="{crest_color}" stroke="#FFFFFF" stroke-width="0.5" />
            </svg>
            """
            return svg_str
            
        def format_fecha_es(dt):
            """Formatea un datetime en espanol de forma independiente a la configuracion regional. [Willys_IA]"""
            dias = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            meses = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            dia_sem = dias.get(dt.strftime('%A'), dt.strftime('%A'))
            dia_num = dt.day
            mes_nom = meses.get(dt.month, '')
            return f"{dia_sem}, {dia_num} de {mes_nom}"
            
        return dict(render_jersey=render_jersey, format_fecha_es=format_fecha_es)

    return app
