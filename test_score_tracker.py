import unittest
from datetime import datetime
from decimal import Decimal
from flask import Flask
from app import db, create_app
from app.models import Usuario, Grupo, ParticipanteGrupo, Partido, Prediccion, PartidoParticipanteCaja
from app.logic import liquidar_partido_grupo

class TestScoreTrackerLogic(unittest.TestCase):
    """
    Casos de Prueba Unitarios y de Integracion para el Motor Financiero. [Willys_IA]
    Certifica la precision de la liquidacion contable de Balones e impuestos de App (ISO 9001).
    """
    
    def setUp(self):
        """Inicializacion del entorno de prueba en memoria SQLite. [Willys_IA]"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Creacion de la base de datos semilla para el test
        self.inicializar_datos_semilla()

    def tearDown(self):
        """Limpieza y destruccion del contexto de pruebas. [Willys_IA]"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def inicializar_datos_semilla(self):
        """Carga usuarios, grupos y partidos para simular el juego predictivo. [Willys_IA]"""
        # 1. Crear Usuarios (Administrador y Participantes)
        self.admin = Usuario(nombre="Admin Willys", email="admin@scoretracker.com")
        self.admin.set_password("segura123")
        
        self.user1 = Usuario(nombre="Socrates Gomez", email="sgomez@scoretracker.com")
        self.user1.set_password("segura123")
        
        self.user2 = Usuario(nombre="Juan Perez", email="jperez@scoretracker.com")
        self.user2.set_password("segura123")
        
        self.user3 = Usuario(nombre="Ana Maria", email="amaria@scoretracker.com")
        self.user3.set_password("segura123")
        
        db.session.add_all([self.admin, self.user1, self.user2, self.user3])
        db.session.commit()
        
        # 2. Crear Grupo de Juego predictivo
        # Configuraciones: 50 Balones de aporte, equivalencia 10.00 Bs, tipo Marcador Exacto, politica Acumular
        self.grupo = Grupo(
            nombre="Torneo Mundial 2026",
            descripcion="Grupo predictivo del Mundial de Futbol",
            admin_id=self.admin.id,
            tesorero_id=self.admin.id,
            balones_aporte=50,
            balon_equivalencia=10.00,
            moneda_codigo='Bs',
            comision_porcentaje=2.00,
            tipo_juego='Marcador',
            politica_pozo_vacio='Acumular',
            limite_pago_minutos=60,
            codigo_invitacion="MUNDIAL1",
            datos_pago_tesorero="Tesorero: Admin Willys - QR de Pago",
            estado_juego='Configuracion'
        )
        db.session.add(self.grupo)
        db.session.commit()
        
        # Registrar membresias de los usuarios en el grupo
        self.m_admin = ParticipanteGrupo(grupo_id=self.grupo.id, usuario_id=self.admin.id, reglas_aceptadas=True)
        self.m_u1 = ParticipanteGrupo(grupo_id=self.grupo.id, usuario_id=self.user1.id, reglas_aceptadas=True)
        self.m_u2 = ParticipanteGrupo(grupo_id=self.grupo.id, usuario_id=self.user2.id, reglas_aceptadas=True)
        self.m_u3 = ParticipanteGrupo(grupo_id=self.grupo.id, usuario_id=self.user3.id, reglas_aceptadas=True)
        
        db.session.add_all([self.m_admin, self.m_u1, self.m_u2, self.m_u3])
        db.session.commit()
        
        # 3. Crear Partido FIFA
        self.partido = Partido(
            equipo_local="Bolivia",
            equipo_visitante="Argentina",
            fecha_hora=datetime.utcnow(),
            fase="Eliminatorias",
            estado="Abierto"
        )
        db.session.add(self.partido)
        db.session.commit()

    def test_reparto_proporcional_exacto(self):
        """TEST: Reparto proporcional exacto con ganadores (Primer partido = 0% comision). [Willys_IA]"""
        # Cargar marcador oficial del partido
        self.partido.marcador = '2-1'
        
        # 4 Usuarios registran predicciones
        p1 = Prediccion(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.admin.id, valor_prediccion='2-1') # Acierta
        p2 = Prediccion(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user1.id, valor_prediccion='2-1') # Acierta
        p3 = Prediccion(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user2.id, valor_prediccion='0-0') # Falla
        p4 = Prediccion(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user3.id, valor_prediccion='1-3') # Falla
        db.session.add_all([p1, p2, p3, p4])
        
        # Tesorero concilia caja (Todos pagaron offline y pasan a Participa)
        c1 = PartidoParticipanteCaja(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.admin.id, estado_pago='Participa')
        c2 = PartidoParticipanteCaja(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user1.id, estado_pago='Participa')
        c3 = PartidoParticipanteCaja(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user2.id, estado_pago='Participa')
        c4 = PartidoParticipanteCaja(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user3.id, estado_pago='Participa')
        db.session.add_all([c1, c2, c3, c4])
        db.session.commit()
        
        # Disparar liquidacion
        resultado = liquidar_partido_grupo(self.grupo.id, self.partido.id)
        
        # Aseveraciones de la contabilidad (4 participantes * 50 balones = 200 balones totales)
        # Primer partido es gratis (0% comision) -> Pozo neto a repartir = 200 Balones
        # Hay 2 ganadores -> Cada uno recibe (1/2) * 200 = 100 Balones.
        # Ganancia neta ganadores = 100 - 50 = +50 Balones.
        # Perdida perdedores = -50 Balones.
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['balones_recaudados'], 200)
        self.assertEqual(resultado['comision_balones'], 0)
        self.assertEqual(resultado['ganadores'], 2)
        
        # Verificar balances virtuales guardados en base de datos
        self.assertEqual(self.m_admin.balance_balones, 100)
        self.assertEqual(self.m_u1.balance_balones, 100)
        self.assertEqual(self.m_u2.balance_balones, -50)
        self.assertEqual(self.m_u3.balance_balones, -50)

    def test_pozo_vacio_modalidad_acumular(self):
        """TEST: Pozo vacio (nadie acierta) en modalidad ACUMULAR. [Willys_IA]"""
        # Cargar marcador oficial del partido
        self.partido.marcador = '1-1'
        
        # Registrar predicciones erradas (Nadie predice '1-1')
        p1 = Prediccion(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.admin.id, valor_prediccion='2-0')
        p2 = Prediccion(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user1.id, valor_prediccion='0-0')
        db.session.add_all([p1, p2])
        
        # Conciliar pagos
        c1 = PartidoParticipanteCaja(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.admin.id, estado_pago='Participa')
        c2 = PartidoParticipanteCaja(partido_id=self.partido.id, grupo_id=self.grupo.id, usuario_id=self.user1.id, estado_pago='Participa')
        db.session.add_all([c1, c2])
        db.session.commit()
        
        # Disparar liquidacion (Primer partido comision 0%)
        # 2 participantes * 50 balones = 100 balones. Pozo neto = 100.
        # Nadie gana -> 100 balones acumulados en grupo.pozo_acumulado
        resultado = liquidar_partido_grupo(self.grupo.id, self.partido.id)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['ganadores'], 0)
        self.assertEqual(resultado['pozo_acumulado_restante'], 100)
        
        # Los balances de los jugadores quedan intactos en 0 para no debitar hasta que haya una resolucion
        self.assertEqual(self.m_admin.balance_balones, 0)
        self.assertEqual(self.m_u1.balance_balones, 0)

if __name__ == '__main__':
    unittest.main()
