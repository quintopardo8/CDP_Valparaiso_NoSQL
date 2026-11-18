#carga masiva 2

import random
from datetime import datetime, timedelta, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ID_BASE = 100
SEMILLA = 2026

NOMBRES = ["Tomás", "Javiera", "Mauricio", "Daniela", "Felipe", "Constanza", "Ignacio", "Marcela",
           "Esteban", "Lorena", "Cristián", "Paulina", "Matías", "Francisca", "Nicolás", "Catalina",
           "Sebastián", "Macarena", "Gonzalo", "Antonia", "Rodolfo", "Ximena", "Claudio", "Bárbara"]
APELLIDOS = ["Herrera", "Lagos", "Ortiz", "Reyes", "Araya", "Mella", "Vega", "Pinto", "Cortés",
             "Bustos", "Gallardo", "Figueroa", "Muñoz", "Contreras", "Sepúlveda", "Tapia",
             "Carrasco", "Espinoza", "Valenzuela", "Rivera", "Navarro", "Salinas", "Campos", "Parra"]

CLIENTES_EXTRA = [
    {"_id": 11, "nombre": "Ferretería Costa Norte",      "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 220},
    {"_id": 12, "nombre": "Inmobiliaria Cerro Alegre",   "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 135},
    {"_id": 13, "nombre": "Tienda Online Porteña",       "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 480},
    {"_id": 14, "nombre": "Laboratorio Andes Salud",     "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 175},
    {"_id": 15, "nombre": "Constructora Marga Marga",    "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 60},
    {"_id": 16, "nombre": "Valentina Rojas",             "tipo_cliente": "PARTICULAR", "volumen_mensual_est": 2},
    {"_id": 17, "nombre": "Pablo Aguirre",               "tipo_cliente": "PARTICULAR", "volumen_mensual_est": 1},
    {"_id": 18, "nombre": "Librería Mar y Cerro",        "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 95},
]

PERFIL = {
    13: (8, 3), 14: (7, 3), 9: (8, 2), 15: (8, 2),
    18: (3, 3), 22: (3, 3),
    2: (1, 1), 1: (2, 1), 53: (1, 1), 52: (3, 1), 38: (1, 1), 49: (3, 1),
}
SOBRECARGA = {18, 22}
NORMALES = [5, 6, 19, 20, 23, 24, 25, 26, 27, 28, 30, 32, 35, 36, 37, 39, 40, 42, 43, 44, 45, 46, 48, 50, 51, 57]


def _tipo_peso(rnd):
    if rnd.random() < 0.65:
        return "ENCOMIENDA", rnd.randint(500, 4500)
    return "CARTA", rnd.randint(60, 150)


def generar_envios(rnd, ahora, cartero_de, clientes_ids):
    """Función pura: devuelve la lista de documentos 'envios'. No usa la base."""
    perfil = dict(PERFIL)
    for cid in NORMALES:
        perfil[cid] = (rnd.randint(4, 5), rnd.randint(1, 2))

    docs, nid = [], ID_BASE
    for cid, (n_hist, n_pend) in perfil.items():
        cart = cartero_de[cid]

        for _ in range(n_pend):
            if cid in SOBRECARGA:
                tipo, peso = "ENCOMIENDA", rnd.randint(8200, 9000)
            else:
                tipo, peso = _tipo_peso(rnd)
            docs.append({
                "_id": nid, "cliente_id": rnd.choice(clientes_ids), "cuartel_id": cid,
                "tipo_envio": tipo, "peso_gramos": peso,
                "fecha_ingreso": ahora - timedelta(days=rnd.randint(0, 4), hours=rnd.randint(0, 5)),
                "estado": "PENDIENTE", "intentos_entrega": [],
            })
            nid += 1

        for _ in range(n_hist):
            tipo, peso = _tipo_peso(rnd)
            ingreso = ahora - timedelta(days=rnd.randint(8, 80))
            r = rnd.random()

            def intento(n, res):
                return {"intento_nro": n, "cartero_id": cart,
                        "fecha_entrega": ingreso + timedelta(days=n),
                        "resultado": res, "tiempo_minutos": rnd.randint(6, 20)}

            if r < 0.45:
                intentos, estado = [intento(1, "ENTREGADO")], "ENTREGADO"
            elif r < 0.75:
                intentos, estado = [intento(1, rnd.choice(["NO_UBICADO", "RECHAZADO"])),
                                    intento(2, "ENTREGADO")], "ENTREGADO"
            else:
                intentos, estado = [intento(1, rnd.choice(["NO_UBICADO", "RECHAZADO"])),
                                    intento(2, rnd.choice(["NO_UBICADO", "RECHAZADO"]))], "DEVUELTO"
            docs.append({
                "_id": nid, "cliente_id": rnd.choice(clientes_ids), "cuartel_id": cid,
                "tipo_envio": tipo, "peso_gramos": peso, "fecha_ingreso": ingreso,
                "estado": estado, "intentos_entrega": intentos,
            })
            nid += 1
    return docs


def cargar():
    from app.database import get_db
    db = get_db()
    ahora = datetime.now(timezone.utc)
    rnd_c, rnd_e = random.Random(SEMILLA), random.Random(SEMILLA + 1)

    for c in CLIENTES_EXTRA:
        db.clientes.replace_one({"_id": c["_id"]}, c, upsert=True)

    usados = {k["cartero_id"] for c in db.cuarteles.find({}) for k in c.get("carteros_asignados", [])}
    sig = max(usados, default=0) + 1
    nuevos = 0
    for c in db.cuarteles.find({"carteros_asignados.0": {"$exists": False}}).sort("_id", 1):
        db.cuarteles.update_one({"_id": c["_id"]}, {"$push": {"carteros_asignados": {
            "cartero_id": sig,
            "nombre": f"{rnd_c.choice(NOMBRES)} {rnd_c.choice(APELLIDOS)}",
            "tipo_movilidad": "A_PIE" if c["tipo_reparto"] == "A_PIE" else "MOTO",
            "antiguedad_anios": rnd_c.randint(1, 20)}}})
        sig += 1
        nuevos += 1

    cartero_de = {c["_id"]: c["carteros_asignados"][0]["cartero_id"]
                  for c in db.cuarteles.find({}) if c.get("carteros_asignados")}
    clientes_ids = sorted(c["_id"] for c in db.clientes.find({}, {"_id": 1}))

    docs = generar_envios(rnd_e, ahora, cartero_de, clientes_ids)
    db.envios.delete_many({"_id": {"$gte": ID_BASE}})
    db.envios.insert_many(docs)

    return {"clientes": len(CLIENTES_EXTRA), "carteros_nuevos": nuevos, "envios_generados": len(docs),
            "pendientes": sum(1 for d in docs if d["estado"] == "PENDIENTE")}


if __name__ == "__main__":
    print(cargar())
