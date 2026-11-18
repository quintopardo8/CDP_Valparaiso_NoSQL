#carga masiva 1

from datetime import datetime, timedelta, timezone
from app.database import get_db

def poblar_base_datos():
    db = get_db()

    for col in ["cuarteles", "clientes", "envios", "diagnostico_cuarteles", "alertas_carga_cuartel"]:
        db[col].delete_many({})

    cdp_info = {
        "cdp_id": 1,
        "nombre": "Centro de Distribución Postal Valparaíso",
        "direccion": "Victoria 2479"
    }

    carteros_por_cuartel = {
        9:  [{"cartero_id": 1,  "nombre": "Juan Pérez",      "tipo_movilidad": "A_PIE", "antiguedad_anios": 12}],
        15: [{"cartero_id": 2,  "nombre": "María Soto",      "tipo_movilidad": "A_PIE", "antiguedad_anios": 8}],
        16: [{"cartero_id": 3,  "nombre": "Pedro Alarcón",   "tipo_movilidad": "A_PIE", "antiguedad_anios": 5}],
        18: [{"cartero_id": 4,  "nombre": "Carla Núñez",     "tipo_movilidad": "A_PIE", "antiguedad_anios": 15}],
        19: [{"cartero_id": 5,  "nombre": "Luis Fuentes",    "tipo_movilidad": "A_PIE", "antiguedad_anios": 3}],
        23: [{"cartero_id": 6,  "nombre": "Andrea Ramírez",  "tipo_movilidad": "A_PIE", "antiguedad_anios": 7}],
        32: [{"cartero_id": 7,  "nombre": "Diego Morales",   "tipo_movilidad": "A_PIE", "antiguedad_anios": 20}],
        1:  [{"cartero_id": 8,  "nombre": "Fernanda Rojas",  "tipo_movilidad": "A_PIE", "antiguedad_anios": 4}],
        26: [{"cartero_id": 9,  "nombre": "Ricardo Silva",   "tipo_movilidad": "A_PIE", "antiguedad_anios": 9}],
        48: [{"cartero_id": 10, "nombre": "Camila Torres",   "tipo_movilidad": "A_PIE", "antiguedad_anios": 6}],
        54: [{"cartero_id": 11, "nombre": "Hugo Castillo",   "tipo_movilidad": "MOTO",  "antiguedad_anios": 2}],
        55: [{"cartero_id": 12, "nombre": "Paula Vidal",     "tipo_movilidad": "MOTO",  "antiguedad_anios": 2}],
        56: [{"cartero_id": 13, "nombre": "Sergio Bravo",    "tipo_movilidad": "MOTO",  "antiguedad_anios": 1}],
        57: [{"cartero_id": 14, "nombre": "Rodrigo Peña",    "tipo_movilidad": "A_PIE", "antiguedad_anios": 10}],
        6:  [{"cartero_id": 15, "nombre": "Valentina Cruz",  "tipo_movilidad": "A_PIE", "antiguedad_anios": 11}],
    }

    raw_cuarteles = [
        (1,  1.205, "BAJA",      "A_PIE",      -33.02676, -71.64308),
        (2,  1.357, "BAJA",      "A_PIE",      -33.02737, -71.63430),
        (5,  1.463, "BAJA",      "A_PIE",      -33.03369, -71.65014),
        (6,  0.663, "MEDIA",     "A_PIE",      -33.03618, -71.63668),
        (9,  0.478, "ALTA",      "A_PIE",      -33.03935, -71.63044),
        (13, 1.085, "MEDIA",     "A_PIE",      -33.04929, -71.64622),
        (14, 0.820, "MEDIA",     "A_PIE",      -33.04361, -71.63988),
        (15, 0.438, "ALTA",      "A_PIE",      -33.04328, -71.62980),
        (16, 0.478, "ALTA",      "A_PIE",      -33.04808, -71.62785),
        (18, 0.436, "ALTA",      "A_PIE",      -33.04410, -71.61853),
        (19, 0.579, "ALTA",      "A_PIE",      -33.04669, -71.60665),
        (20, 0.767, "MEDIA",     "A_PIE",      -33.03619, -71.59292),
        (22, 0.691, "MEDIA",     "A_PIE",      -33.04064, -71.60112),
        (23, 0.471, "ALTA",      "A_PIE",      -33.04490, -71.59816),
        (24, 0.622, "MEDIA",     "A_PIE",      -33.04263, -71.58754),
        (25, 0.937, "MEDIA",     "A_PIE",      -33.03671, -71.58394),
        (26, 1.868, "BAJA",      "A_PIE",      -33.04703, -71.65441),
        (27, 1.104, "MEDIA",     "A_PIE",      -33.05362, -71.63818),
        (28, 0.953, "MEDIA",     "A_PIE",      -33.05560, -71.63030),
        (30, 0.722, "MEDIA",     "A_PIE",      -33.04877, -71.61900),
        (32, 0.458, "ALTA",      "A_PIE",      -33.05056, -71.61646),
        (35, 0.648, "MEDIA",     "A_PIE",      -33.04897, -71.59609),
        (36, 1.122, "MEDIA",     "A_PIE",      -33.05401, -71.58160),
        (37, 0.808, "MEDIA",     "A_PIE",      -33.04771, -71.57938),
        (38, 0.868, "MEDIA",     "A_PIE",      -33.05268, -71.56586),
        (39, 1.087, "MEDIA",     "A_PIE",      -33.06054, -71.61922),
        (40, 0.797, "MEDIA",     "A_PIE",      -33.06025, -71.61285),
        (42, 0.726, "MEDIA",     "A_PIE",      -33.05999, -71.60864),
        (43, 0.819, "MEDIA",     "A_PIE",      -33.05667, -71.60388),
        (44, 0.718, "MEDIA",     "A_PIE",      -33.06256, -71.59731),
        (45, 0.754, "MEDIA",     "A_PIE",      -33.05541, -71.59230),
        (46, 1.013, "MEDIA",     "A_PIE",      -33.06288, -71.58282),
        (48, 1.521, "BAJA",      "A_PIE",      -33.06257, -71.57279),
        (49, 0.950, "MEDIA",     "A_PIE",      -33.05931, -71.56400),
        (50, 0.828, "MEDIA",     "A_PIE",      -33.06724, -71.59264),
        (51, 1.558, "BAJA",      "A_PIE",      -33.07315, -71.58495),
        (52, 1.998, "BAJA",      "A_PIE",      -33.11252, -71.57245),
        (53, 0.966, "MEDIA",     "A_PIE",      -33.11934, -71.58434),
        (54, 3.058, "BAJA",      "MOTO", -33.14499, -71.57117),
        (55, 3.079, "BAJA",      "MOTO", -33.13470, -71.55979),
        (56, 4.301, "BAJA",      "MOTO", -33.12001, -71.55581),
        (57, 1.219, "BAJA",      "A_PIE",      -33.12888, -71.57536),
        (58, None,  "SIN_DATOS", "A_PIE",      -33.12377, -71.57121),
    ]

    docs_cuarteles = []
    for cid, area, dif, tipo, lat, lon in raw_cuarteles:
        docs_cuarteles.append({
            "_id": cid,
            "cdp": cdp_info,
            "area_km2": area,
            "nivel_dificultad": dif,
            "tipo_reparto": tipo,
            "latitud_centro": lat,
            "longitud_centro": lon,
            "ubicacion": {"type": "Point", "coordinates": [lon, lat]},
            "activo": "S",
            "carteros_asignados": carteros_por_cuartel.get(cid, [])
        })
    db.cuarteles.insert_many(docs_cuarteles)

    docs_clientes = [
        {"_id": 1,  "nombre": "Juan Carlos Muñoz",            "tipo_cliente": "PARTICULAR", "volumen_mensual_est": 1},
        {"_id": 2,  "nombre": "Isidora Fernández",            "tipo_cliente": "PARTICULAR", "volumen_mensual_est": 1},
        {"_id": 3,  "nombre": "Farmacia Cruz Verde Valpo",    "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 180},
        {"_id": 4,  "nombre": "Ecommerce Sur Andino SpA",     "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 260},
        {"_id": 5,  "nombre": "Notaría Plaza Sotomayor",      "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 90},
        {"_id": 6,  "nombre": "Manuel Cárdenas",              "tipo_cliente": "PARTICULAR", "volumen_mensual_est": 1},
        {"_id": 7,  "nombre": "Librería Ibáñez",              "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 40},
        {"_id": 8,  "nombre": "Distribuidora Placilla Ltda.", "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 310},
        {"_id": 9,  "nombre": "Rosa Elgueta",                 "tipo_cliente": "PARTICULAR", "volumen_mensual_est": 1},
        {"_id": 10, "nombre": "Clínica Reñaca Salud",         "tipo_cliente": "EMPRESA",    "volumen_mensual_est": 150},
    ]
    db.clientes.insert_many(docs_clientes)

    ahora = datetime.now(timezone.utc)

    docs_envios = [
        {"_id": 1,  "cliente_id": 1,  "cuartel_id": 9,  "tipo_envio": "CARTA",      "peso_gramos": 120,  "fecha_ingreso": ahora - timedelta(days=4), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 2,  "cliente_id": 2,  "cuartel_id": 15, "tipo_envio": "CARTA",      "peso_gramos": 90,   "fecha_ingreso": ahora - timedelta(days=3), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 3,  "cliente_id": 3,  "cuartel_id": 16, "tipo_envio": "ENCOMIENDA", "peso_gramos": 7800, "fecha_ingreso": ahora - timedelta(days=2), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 4,  "cliente_id": 4,  "cuartel_id": 16, "tipo_envio": "ENCOMIENDA", "peso_gramos": 7500, "fecha_ingreso": ahora - timedelta(days=1), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 5,  "cliente_id": 5,  "cuartel_id": 16, "tipo_envio": "ENCOMIENDA", "peso_gramos": 6200, "fecha_ingreso": ahora - timedelta(days=1), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 6,  "cliente_id": 6,  "cuartel_id": 23, "tipo_envio": "CARTA",      "peso_gramos": 95,   "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 7,  "cliente_id": 7,  "cuartel_id": 32, "tipo_envio": "ENCOMIENDA", "peso_gramos": 1500, "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 8,  "cliente_id": 8,  "cuartel_id": 54, "tipo_envio": "ENCOMIENDA", "peso_gramos": 7900, "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 9,  "cliente_id": 4,  "cuartel_id": 54, "tipo_envio": "ENCOMIENDA", "peso_gramos": 7600, "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 10, "cliente_id": 9,  "cuartel_id": 1,  "tipo_envio": "CARTA",      "peso_gramos": 80,   "fecha_ingreso": ahora - timedelta(days=5), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 11, "cliente_id": 10, "cuartel_id": 26, "tipo_envio": "ENCOMIENDA", "peso_gramos": 2200, "fecha_ingreso": ahora - timedelta(days=2), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 12, "cliente_id": 3,  "cuartel_id": 48, "tipo_envio": "ENCOMIENDA", "peso_gramos": 4100, "fecha_ingreso": ahora - timedelta(days=1), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 13, "cliente_id": 8,  "cuartel_id": 55, "tipo_envio": "ENCOMIENDA", "peso_gramos": 7950, "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 14, "cliente_id": 4,  "cuartel_id": 56, "tipo_envio": "ENCOMIENDA", "peso_gramos": 7600, "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
        {
            "_id": 15, "cliente_id": 1, "cuartel_id": 6, "tipo_envio": "CARTA", "peso_gramos": 70,
            "fecha_ingreso": ahora - timedelta(days=6), "estado": "DEVUELTO",
            "intentos_entrega": [
                {"intento_nro": 1, "cartero_id": 15, "fecha_entrega": ahora - timedelta(days=6), "resultado": "NO_UBICADO", "tiempo_minutos": 12},
                {"intento_nro": 2, "cartero_id": 15, "fecha_entrega": ahora - timedelta(days=5), "resultado": "RECHAZADO",  "tiempo_minutos": 15}
            ]
        },
        {"_id": 16, "cliente_id": 4,  "cuartel_id": 14, "tipo_envio": "ENCOMIENDA", "peso_gramos": 3000, "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 17, "cliente_id": 1,  "cuartel_id": 58, "tipo_envio": "CARTA",      "peso_gramos": 60,   "fecha_ingreso": ahora - timedelta(days=1), "estado": "PENDIENTE", "intentos_entrega": []},
        {"_id": 18, "cliente_id": 3,  "cuartel_id": 16, "tipo_envio": "ENCOMIENDA", "peso_gramos": 4000, "fecha_ingreso": ahora,                    "estado": "PENDIENTE", "intentos_entrega": []},
    ]
    db.envios.insert_many(docs_envios)

    return {"status": "ok", "cuarteles": len(docs_cuarteles), "clientes": len(docs_clientes), "envios": len(docs_envios)}