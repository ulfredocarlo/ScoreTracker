from decimal import Decimal
from datetime import datetime
from app import db
from app.models import (
    Grupo, Partido, Prediccion, PartidoParticipanteCaja, 
    ParticipanteGrupo, LiquidacionHistorial, ComisionHistorial
)

def liquidar_partido_grupo(grupo_id, partido_id):
    """
    Motor contable principal de liquidacion y reparto proporcional en Balones. [Willys_IA]
    
    Alineado a las politicas contables ISO 9001:2015 de ScoreTracker:
    1. Filtra solo participantes con pago confirmado ('Participa') en este partido.
    2. Suma el pozo total en Balones.
    3. Deduce el porcentaje de comision de la plataforma (primer partido gratis = 0%).
    4. Determina ganadores segun la modalidad del grupo.
    5. Distribuye proporcionalmente (o ejecuta politicas de Pozo Vacio: Acumular o Devolver).
    6. Mantiene auditoria transaccional de balances y comisiones.
    """
    try:
        grupo = Grupo.query.get(grupo_id)
        partido = Partido.query.get(partido_id)
        
        if not grupo or not partido:
            raise ValueError("Grupo o Partido inexistente.")
            
        if not partido.marcador:
            raise ValueError("El partido no posee marcador cargado para liquidar.")
            
        # 1. Obtener los participantes que registraron prediccion y su pago fue VALIDADO ('Participa')
        cajas_validas = PartidoParticipanteCaja.query.filter_by(
            grupo_id=grupo.id,
            partido_id=partido.id,
            estado_pago='Participa'
        ).all()
        
        if not cajas_validas:
            # Si nadie pago/participo, el partido se cierra sin transacciones
            return {
                'success': True,
                'mensaje': 'No hubo participantes validados para este partido. Sin transacciones.',
                'balones_recaudados': 0,
                'comision': 0,
                'ganadores': 0
            }
            
        N = len(cajas_validas) # Cantidad de jugadores activos
        B = Decimal(grupo.balones_aporte) # Aporte estandar en Balones
        
        # 2. Calcular pozo total
        P_total = N * B
        
        # 3. Calcular comision de la App (Si es el primer partido liquidado del grupo, es gratis = 0%)
        # Validar si ya existen comisiones previas pagadas/pendientes para este grupo
        comisiones_previas = ComisionHistorial.query.filter_by(grupo_id=grupo.id).count()
        
        if comisiones_previas == 0:
            C_porcentaje = Decimal(0.00) # Primer partido gratis (0% comision)
        else:
            C_porcentaje = Decimal(grupo.comision_porcentaje)
            
        Com = P_total * (C_porcentaje / Decimal(100.00)) # Comision en Balones
        P_neto = P_total - Com # Pozo neto a repartir
        
        # 4. Determinar Ganadores
        ganadores_predicciones = determinar_ganadores_partido(grupo, partido, cajas_validas)
        G_total = len(ganadores_predicciones) # Cantidad de ganadores
        
        # 5. Lógica de Reparto o Pozo Vacío
        if G_total > 0:
            # === CASO A: HAY GANADORES ===
            # Pozo neto total a distribuir (Pozo neto de este partido + acumulados de empates previos)
            pozo_distribuir = P_neto + Decimal(grupo.pozo_acumulado)
            
            # Reparto proporcional (en nuestro MVP, cada ganador aporto la cantidad estandar fija B)
            # Premio individual = (1 / G_total) * pozo_distribuir
            premio_individual = pozo_distribuir / Decimal(G_total)
            
            # Registrar ganadores y actualizar balances virtuales
            for pred in ganadores_predicciones:
                # Sumar premio individual en balance de Balones del miembro
                membresia = ParticipanteGrupo.query.filter_by(
                    grupo_id=grupo.id,
                    usuario_id=pred.usuario_id
                ).first()
                if membresia:
                    membresia.balance_balones += int(round(premio_individual))
                    
                # Registrar bitacora de auditoria contable
                liqui = LiquidacionHistorial(
                    partido_id=partido.id,
                    usuario_id=pred.usuario_id,
                    grupo_id=grupo.id,
                    monto_aportado=int(B),
                    gano=True,
                    ganancia_neta=int(round(premio_individual)) - int(B)
                )
                db.session.add(liqui)
                
            # Registrar perdedores activos
            usuarios_ganadores_ids = [g.usuario_id for g in ganadores_predicciones]
            for caja in cajas_validas:
                if caja.usuario_id not in usuarios_ganadores_ids:
                    # Descontar el aporte del balance de Balones
                    membresia = ParticipanteGrupo.query.filter_by(
                        grupo_id=grupo.id,
                        usuario_id=caja.usuario_id
                    ).first()
                    if membresia:
                        membresia.balance_balones -= int(B)
                        
                    # Registrar perdida en auditoria
                    liqui = LiquidacionHistorial(
                        partido_id=partido.id,
                        usuario_id=caja.usuario_id,
                        grupo_id=grupo.id,
                        monto_aportado=int(B),
                        gano=False,
                        ganancia_neta=int(B) * -1
                    )
                    db.session.add(liqui)
            
            # Restablecer el pozo acumulado del grupo a cero
            grupo.pozo_acumulado = 0
            
        else:
            # === CASO B: POZO VACÍO (NADIE ACERTÓ) ===
            if grupo.politica_pozo_vacio == 'Acumular':
                # Sumar pozo neto del partido al pozo acumulado de arrastre del grupo
                grupo.pozo_acumulado += int(round(P_neto))
                
                # Para los participantes, su balance virtual no cambia aun o se descuenta el aporte
                # Para transparencia, registramos que el dinero quedo retenido en el pozo del grupo
                for caja in cajas_validas:
                    liqui = LiquidacionHistorial(
                        partido_id=partido.id,
                        usuario_id=caja.usuario_id,
                        grupo_id=grupo.id,
                        monto_aportado=int(B),
                        gano=False,
                        ganancia_neta=0 # No pierde en balance aun, queda acumulado
                    )
                    db.session.add(liqui)
                    
            else: # Devolución
                # No se cobra comision a la plataforma por este partido fallido
                Com = Decimal(0.00)
                
                # Reverso contable: todos quedan en balance 0 de ganancia/perdida para este partido
                for caja in cajas_validas:
                    liqui = LiquidacionHistorial(
                        partido_id=partido.id,
                        usuario_id=caja.usuario_id,
                        grupo_id=grupo.id,
                        monto_aportado=int(B),
                        gano=False,
                        ganancia_neta=0
                    )
                    db.session.add(liqui)
                # El Tesorero del grupo realizara las devoluciones fisicas offline
                
        # 6. Registrar comision de la App en el historial
        comision_reg = None
        if Com > 0:
            comision_reg = ComisionHistorial(
                grupo_id=grupo.id,
                partido_id=partido.id,
                monto_balones=Com,
                monto_dinero_real=Com * Decimal(grupo.balon_equivalencia),
                estado_pago='Pendiente'
            )
            db.session.add(comision_reg)
            
        # Congelar la configuracion del grupo en caso de que sea el primer partido jugado
        if grupo.estado_juego == 'Configuracion':
            grupo.estado_juego = 'Activo'
            
        db.session.commit()
        
        return {
            'success': True,
            'balones_recaudados': float(P_total),
            'comision_balones': float(Com),
            'a_distribuir': float(P_neto),
            'ganadores': G_total,
            'pozo_acumulado_restante': grupo.pozo_acumulado,
            'comision_id': comision_reg.id if comision_reg else None
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def determinar_ganadores_partido(grupo, partido, cajas_validas):
    """
    Determina que predicciones de los participantes validados acertaron. [Willys_IA]
    Soporta modalidades:
    - 'Resultado': Gana local, Empate, Gana visitante.
    - 'Marcador': Acierto exacto del marcador (ej: 2-1).
    """
    usuarios_activos_ids = [c.usuario_id for c in cajas_validas]
    resultado_real = partido.marcador # Ej: '2-1'
    
    # Obtener todas las predicciones del partido en este grupo
    predicciones = Prediccion.query.filter(
        Prediccion.partido_id == partido.id,
        Prediccion.grupo_id == grupo.id,
        Prediccion.usuario_id.in_(usuarios_activos_ids)
    ).all()
    
    ganadores = []
    
    if grupo.tipo_juego == 'Resultado':
        # Parsear goles reales: '2-1' -> Local 2, Visita 1
        goles = resultado_real.split('-')
        goles_L = int(goles[0])
        goles_V = int(goles[1])
        
        if goles_L > goles_V:
            ganador_real = 'Local gana'
        elif goles_L < goles_V:
            ganador_real = 'Visitante gana'
        else:
            ganador_real = 'Empate'
            
        for pred in predicciones:
            if pred.valor_prediccion == ganador_real:
                ganadores.append(pred)
                
    else: # Modalidad 'Marcador' (Acierto Exacto)
        for pred in predicciones:
            if pred.valor_prediccion == resultado_real:
                ganadores.append(pred)
                
    return ganadores
