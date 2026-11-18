from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.logica_reparto import (
    registrar_entrega_pda,
    verificar_alertas_sobrecarga,
    detectar_oportunidades_b2b,
    diagnosticar_cuarteles,
    PESO_MAX_GRAMOS,
)
from app.seed_mongo import poblar_base_datos

app = FastAPI(title="CDP Valparaíso API NoSQL")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def iniciar():
    db = get_db()
    db.command("ping")  
    if db.cuarteles.count_documents({}) == 0:
        poblar_base_datos()


@app.get("/")
def read_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/index.html")
def read_index_alt():
    return read_index()

@app.get("/pda.html")
def read_pda():
    return FileResponse(str(STATIC_DIR / "pda.html"))

@app.get("/api.js")
def read_apijs():
    return FileResponse(str(STATIC_DIR / "api.js"), media_type="application/javascript")


class OportunidadRequest(BaseModel):
    umbral: int = 100

class EntregaRequest(BaseModel):
    envio_id: int
    cartero_id: int
    resultado: str
    tiempo_min: int


def _dias_pendiente(fecha):
    if not fecha:
        return 0
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - fecha).days


def _fila_diagnostico(d):
    return {
        "cuartel": d["cuartel_id"],
        "tipo": d["tipo_reparto"],
        "dificultad": d["nivel_dificultad"],
        "peso_g": d["peso_pendiente_g"],
        "demanda": d.get("indice_demanda"),
        "dias": d.get("dias", 0),
        "accion": d["accion_sugerida"],
        "motivo": d["motivo"],
    }


@app.get("/api/kpis")
def get_kpis():
    db = get_db()
    diag = list(db.diagnostico_cuarteles.find({}))
    return {
        "status": "OK",
        "pendientes": db.envios.count_documents({"estado": "PENDIENTE"}),
        "sobrecargados_hoy": db.alertas_carga_cuartel.count_documents(
            {"fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
        ),
        "limite_g": PESO_MAX_GRAMOS,
        "hay_diagnostico": len(diag) > 0,
        "motorizar": sum(1 for d in diag if d["accion_sugerida"] == "MOTORIZAR"),
        "subdividir": sum(1 for d in diag if d["accion_sugerida"] == "SUBDIVIDIR"),
        "fusionar": sum(1 for d in diag if d["accion_sugerida"] == "FUSIONAR"),
        "oportunidades": db.clientes.count_documents({"oportunidad_b2b.detectada": True}),
        "devueltos": db.envios.count_documents({"estado": "DEVUELTO"}),
    }


@app.get("/api/alertas")
def get_alertas():
    db = get_db()
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    diag = {d["cuartel_id"]: d for d in db.diagnostico_cuarteles.find({})}
    filas = []
    for a in db.alertas_carga_cuartel.find({"fecha": hoy}):
        d = diag.get(a["cuartel_id"], {})
        mas_antiguo = db.envios.find_one(
            {"cuartel_id": a["cuartel_id"], "estado": "PENDIENTE"},
            sort=[("fecha_ingreso", 1)],
        )
        filas.append({
            "cuartel": a["cuartel_id"],
            "peso_g": a["peso_gramos"],
            "dias": _dias_pendiente(mas_antiguo["fecha_ingreso"]) if mas_antiguo else 0,
            "accion": d.get("accion_sugerida", "-"),
        })
    return {"status": "OK", "filas": filas}


@app.get("/api/mapa")
def get_mapa():
    db = get_db()
    diag = {d["cuartel_id"]: d for d in db.diagnostico_cuarteles.find({})}
    filas = []
    for c in db.cuarteles.find({"activo": "S"}):
        d = diag.get(c["_id"])
        filas.append({
            "cuartel": c["_id"],
            "tipo": c["tipo_reparto"],
            "dificultad": c["nivel_dificultad"],
            "lat": c["latitud_centro"],
            "lon": c["longitud_centro"],
            "accion": d["accion_sugerida"] if d else None,
            "motivo": d["motivo"] if d else None,
            "demanda": d.get("indice_demanda") if d else None,
        })
    return {"status": "OK", "filas": filas}


@app.post("/api/diagnostico")
def ejecutar_diagnostico():
    db = get_db()
    res = diagnosticar_cuarteles(db)
    filas = [_fila_diagnostico(d) for d in db.diagnostico_cuarteles.find({}).sort("cuartel_id", 1)]
    return {
        "status": "OK",
        "msg": f"Diagnóstico actualizado: {res['total_procesados']} cuarteles procesados.",
        "filas": filas,
    }


@app.post("/api/oportunidades")
def detectar_oportunidades(body: OportunidadRequest):
    db = get_db()
    try:
        res = detectar_oportunidades_b2b(db, body.umbral)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    filas = [
        {
            "cliente": c["nombre"],
            "volumen": c["volumen_mensual_est"],
            "fecha": c["oportunidad_b2b"]["fecha_deteccion"].strftime("%Y-%m-%d"),
        }
        for c in db.clientes.find({"oportunidad_b2b.detectada": True,
                                   "volumen_mensual_est": {"$gt": body.umbral}})
    ]
    return {
        "status": "OK",
        "msg": f"B2B analizado (umbral > {body.umbral}): {res['nuevas_oportunidades']} nuevas, {len(filas)} en total.",
        "filas": filas,
    }


@app.get("/api/carteros/{cartero_id}/envios-pendientes")
def listar_envios_pendientes(cartero_id: int):
    db = get_db()
    cuartel = db.cuarteles.find_one({"carteros_asignados.cartero_id": cartero_id})
    if not cuartel:
        return {"status": "OK", "filas": []}
    filas = [
        {
            "envio": e["_id"],
            "tipo": e["tipo_envio"],
            "peso_g": e["peso_gramos"],
            "intentos": len(e.get("intentos_entrega", [])),
        }
        for e in db.envios.find({"cuartel_id": cuartel["_id"], "estado": "PENDIENTE"}).sort("_id", 1)
    ]
    return {"status": "OK", "filas": filas}


@app.post("/api/entregas")
def registrar_entrega(body: EntregaRequest):
    if body.resultado not in ("ENTREGADO", "RECHAZADO", "NO_UBICADO"):
        raise HTTPException(status_code=400, detail="Resultado no válido.")
    db = get_db()
    try:
        res = registrar_entrega_pda(db, body.envio_id, body.cartero_id,
                                    body.resultado, body.tiempo_min)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    envio = db.envios.find_one({"_id": body.envio_id})
    historial = [
        {"intento": i["intento_nro"], "resultado": i["resultado"], "min": i["tiempo_minutos"]}
        for i in envio.get("intentos_entrega", [])
    ]
    return {
        "status": "OK",
        "msg": f"Visita registrada para el envío {body.envio_id}.",
        "estado": res["nuevo_estado"],
        "historial": historial,
    }

@app.get("/explicacion.html")
def read_explicacion():
    return FileResponse(str(STATIC_DIR / "explicacion.html"))