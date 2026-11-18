from datetime import datetime, timedelta, timezone
from pymongo.database import Database

PESO_MAX_GRAMOS = 25000        
UMBRAL_OPORTUNIDAD = 200       
VENTANA_DIAS = 90              
MIN_ENVIOS_ANALISIS = 2        
INDICE_ALTO = 150              
INDICE_BAJO = 50               
OBJETIVO_ENTREGA_DIAS = 2.0    
DIST_MAX_FUSION_METROS = 3000  

def registrar_entrega_pda(
    db: Database,
    envio_id: int,
    cartero_id: int,
    resultado: str,
    tiempo_min: int
) -> dict:
    envio = db.envios.find_one({"_id": envio_id})
    if not envio:
        raise ValueError(f"El envío {envio_id} no existe.")

    if envio.get("estado") != "PENDIENTE":
        raise ValueError(
            f"El envío {envio_id} no está pendiente (estado actual: {envio.get('estado')})."
        )

    intentos_previos = envio.get("intentos_entrega", [])
    intento_nro = len(intentos_previos) + 1

    if intento_nro > 2:
        raise ValueError(f"El envío {envio_id} ya alcanzó el máximo de 2 intentos permitidos.")

    nuevo_intento = {
        "intento_nro": intento_nro,
        "cartero_id": cartero_id,
        "fecha_entrega": datetime.now(timezone.utc),
        "resultado": resultado,
        "tiempo_minutos": tiempo_min
    }

    nuevo_estado = "PENDIENTE"
    if resultado == "ENTREGADO":
        nuevo_estado = "ENTREGADO"
    elif resultado in ("RECHAZADO", "NO_UBICADO") and intento_nro >= 2:
        nuevo_estado = "DEVUELTO"

    db.envios.update_one(
        {"_id": envio_id},
        {
            "$push": {"intentos_entrega": nuevo_intento},
            "$set": {"estado": nuevo_estado}
        }
    )

    return {
        "envio_id": envio_id,
        "intento_nro": intento_nro,
        "nuevo_estado": nuevo_estado,
        "devolucion_automatica": (nuevo_estado == "DEVUELTO")
    }


def verificar_alertas_sobrecarga(db: Database) -> list:
    
    pipeline = [
        {"$match": {"estado": "PENDIENTE"}},
        {
            "$group": {
                "_id": "$cuartel_id",
                "peso_total_g": {"$sum": "$peso_gramos"},
                "cantidad_envios": {"$sum": 1}
            }
        },
        {"$match": {"peso_total_g": {"$gt": PESO_MAX_GRAMOS}}},
        {
            "$lookup": {
                "from": "cuarteles",
                "localField": "_id",
                "foreignField": "_id",
                "as": "info_cuartel"
            }
        },
        {"$unwind": "$info_cuartel"},
        {
            "$match": {
                "info_cuartel.activo": "S",
                "info_cuartel.tipo_reparto": "A_PIE"
            }
        }
    ]

    sobrecargados = list(db.envios.aggregate(pipeline))
    hoy_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for item in sobrecargados:
        cuartel_id = item["_id"]
        peso = item["peso_total_g"]

        db.alertas_carga_cuartel.update_one(
            {"fecha": hoy_str, "cuartel_id": cuartel_id},
            {
                "$set": {
                    "peso_gramos": peso,
                    "limite_gramos": PESO_MAX_GRAMOS,
                    "fecha_registro": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )

    return sobrecargados


def detectar_oportunidades_b2b(db: Database, umbral: int = UMBRAL_OPORTUNIDAD) -> dict:
   
    if umbral < 0:
        raise ValueError("El umbral debe ser mayor o igual a 0.")

    filtro = {
        "tipo_cliente": "EMPRESA",
        "volumen_mensual_est": {"$gt": umbral},
        "oportunidad_b2b.detectada": {"$ne": True}
    }

    candidatos = list(db.clientes.find(filtro))
    nuevas = 0

    for cli in candidatos:
        motivo = (
            f"Detección masiva: cliente empresa con volumen mensual estimado de "
            f"{cli['volumen_mensual_est']} envíos (umbral {umbral}): evaluar contrato B2B."
        )
        db.clientes.update_one(
            {"_id": cli["_id"]},
            {
                "$set": {
                    "oportunidad_b2b": {
                        "detectada": True,
                        "fecha_deteccion": datetime.now(timezone.utc),
                        "motivo": motivo
                    }
                }
            }
        )
        nuevas += 1

    return {"umbral_aplicado": umbral, "nuevas_oportunidades": nuevas}


def diagnosticar_cuarteles(db: Database) -> dict:
    
    verificar_alertas_sobrecarga(db)

    fecha_corte = datetime.now(timezone.utc) - timedelta(days=VENTANA_DIAS)

    pipeline_metricas = [
        {
            "$facet": {
                "pendientes": [
                    {"$match": {"estado": "PENDIENTE"}},
                    {
                        "$group": {
                            "_id": "$cuartel_id",
                            "envios_pendientes": {"$sum": 1},
                            "peso_pendiente_g": {"$sum": "$peso_gramos"}
                        }
                    }
                ],
                "ventana_90d": [
                    {"$match": {"fecha_ingreso": {"$gte": fecha_corte}}},
                    {
                        "$lookup": {
                            "from": "clientes",
                            "localField": "cliente_id",
                            "foreignField": "_id",
                            "as": "cliente"
                        }
                    },
                    {"$unwind": {"path": "$cliente", "preserveNullAndEmptyArrays": True}},
                    {
                        "$group": {
                            "_id": "$cuartel_id",
                            "envios_ventana": {"$sum": 1},
                            "envios_empresas": {
                                "$sum": {
                                    "$cond": [{"$eq": ["$cliente.tipo_cliente", "EMPRESA"]}, 1, 0]
                                }
                            }
                        }
                    }
                ]
            }
        }
    ]

    agg_res = list(db.envios.aggregate(pipeline_metricas))[0]
    map_pendientes = {x["_id"]: x for x in agg_res["pendientes"]}
    map_ventana = {x["_id"]: x for x in agg_res["ventana_90d"]}

    cuarteles_validos = [
        v["envios_ventana"] for v in map_ventana.values()
        if v["envios_ventana"] >= MIN_ENVIOS_ANALISIS
    ]
    promedio_comunal = (
        sum(cuarteles_validos) / len(cuarteles_validos) if cuarteles_validos else 0
    )

    cuarteles_activos = list(db.cuarteles.find({"activo": "S"}).sort("_id", 1))
    diagnosticos = []
    contadores = {"MOTORIZAR": 0, "SUBDIVIDIR": 0, "FUSIONAR": 0, "MANTENER": 0, "SIN_DATOS": 0}

    for c in cuarteles_activos:
        cid = c["_id"]
        tipo = c["tipo_reparto"]
        dif = c["nivel_dificultad"]

        pend = map_pendientes.get(cid, {"envios_pendientes": 0, "peso_pendiente_g": 0})
        vent = map_ventana.get(cid, {"envios_ventana": 0, "envios_empresas": 0})

        n_pend = pend["envios_pendientes"]
        peso_g = pend["peso_pendiente_g"]
        n_vent = vent["envios_ventana"]

        estado_carga = "SIN_ENVIOS" if n_pend == 0 else (
            "SOBRECARGADO" if (tipo == "A_PIE" and peso_g > PESO_MAX_GRAMOS) else "OK"
        )

        accion = "MANTENER"
        motivo = ""
        vecino_id = None
        indice_demanda = None
        pct_empresas = round((vent["envios_empresas"] / n_vent) * 100) if n_vent > 0 else 0

        if n_vent < MIN_ENVIOS_ANALISIS:
            accion = "SIN_DATOS"
            motivo = f"Solo {n_vent} envío(s) en los últimos {VENTANA_DIAS} días: sin base suficiente."
        else:
            indice_demanda = round((100 * n_vent) / promedio_comunal) if promedio_comunal > 0 else 100

            if tipo == "A_PIE" and peso_g > PESO_MAX_GRAMOS:
                if dif != "ALTA":
                    accion = "MOTORIZAR"
                    motivo = f"La carga pendiente ({peso_g} g) supera el límite legal a pie y la pendiente permite moto."
                else:
                    accion = "SUBDIVIDIR"
                    motivo = f"La carga pendiente ({peso_g} g) supera los 25 kg y la pendiente ALTA limita la moto: subdividir cuartel."

            elif indice_demanda >= INDICE_ALTO:
                if tipo == "A_PIE" and dif != "ALTA":
                    accion = "MOTORIZAR"
                    motivo = f"Presión de demanda ({indice_demanda}% del promedio comunal); pendiente permite moto."
                else:
                    accion = "SUBDIVIDIR"
                    motivo = f"Presión de demanda ({indice_demanda}% del promedio comunal); pendiente alta limita moto."

            elif indice_demanda <= INDICE_BAJO and "ubicacion" in c:
                vecinos = list(db.cuarteles.aggregate([
                    {
                        "$geoNear": {
                            "near": c["ubicacion"],
                            "distanceField": "distancia_metros",
                            "maxDistance": DIST_MAX_FUSION_METROS,
                            "query": {"activo": "S", "_id": {"$ne": cid}},
                            "spherical": True
                        }
                    }
                ]))

                fusion_encontrada = False
                for vec in vecinos:
                    vid = vec["_id"]
                    v_vent = map_ventana.get(vid, {"envios_ventana": 0})["envios_ventana"]
                    v_peso = map_pendientes.get(vid, {"peso_pendiente_g": 0})["peso_pendiente_g"]
                    idx_combinado = round(100 * (n_vent + v_vent) / promedio_comunal) if promedio_comunal > 0 else 100
                    peso_combinado = peso_g + v_peso

                    if idx_combinado < INDICE_ALTO and not (tipo == "A_PIE" and peso_combinado > PESO_MAX_GRAMOS):
                        accion = "FUSIONAR"
                        vecino_id = vid
                        dist_km = round(vec["distancia_metros"] / 1000, 2)
                        motivo = (
                            f"Demanda baja ({indice_demanda}%); fusionar con cuartel {vid} "
                            f"(a {dist_km} km) dejaría demanda combinada de {idx_combinado}%."
                        )
                        fusion_encontrada = True
                        break

                if not fusion_encontrada:
                    motivo = f"Demanda baja ({indice_demanda}%), pero ningún vecino cercano puede absorberla sin sobrecargarse."
            else:
                motivo = f"Demanda de {indice_demanda}% del promedio comunal, sin presión de carga."

        contadores[accion] += 1
        diagnosticos.append({
            "cuartel_id": cid,
            "fecha_diagnostico": datetime.now(timezone.utc),
            "tipo_reparto": tipo,
            "nivel_dificultad": dif,
            "ubicacion": c.get("ubicacion"),
            "envios_pendientes": n_pend,
            "peso_pendiente_g": peso_g,
            "estado": estado_carga,
            "envios_ventana": n_vent,
            "indice_demanda": indice_demanda,
            "pct_empresas": pct_empresas,
            "accion_sugerida": accion,
            "motivo": motivo,
            "cuartel_vecino": vecino_id
        })

    db.diagnostico_cuarteles.delete_many({})
    if diagnosticos:
        db.diagnostico_cuarteles.insert_many(diagnosticos)

    return {
        "total_procesados": len(diagnosticos),
        "resumen": contadores
    }