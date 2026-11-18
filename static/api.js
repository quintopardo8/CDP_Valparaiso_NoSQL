
const API_BASE = '';

const ROUTES = {
  KPIS:          { m: 'GET',  url: () => '/api/kpis' },
  ALERTAS:       { m: 'GET',  url: () => '/api/alertas' },
  MAPA:          { m: 'GET',  url: () => '/api/mapa' },
  DIAGNOSTICAR:  { m: 'POST', url: () => '/api/diagnostico' },
  OPORTUNIDADES: { m: 'POST', url: () => '/api/oportunidades',
                   body: x => ({ umbral: Number(x.x06) }) },
  LISTAR_ENVIOS: { m: 'GET',  url: x => '/api/carteros/' + encodeURIComponent(x.x02) + '/envios-pendientes' },
  REGISTRAR_ENTREGA: { m: 'POST', url: () => '/api/entregas',
                   body: x => ({ envio_id: Number(x.x02), cartero_id: Number(x.x03),
                                 resultado: x.x04, tiempo_min: Number(x.x05) }) }
};


function normalizar(op, d) {
  d = d || {};
  if (Array.isArray(d)) { d = { filas: d }; }
  if (d.status === undefined) { d.status = 'OK'; }
  if (d.filas === undefined) {
    var alt = d.items || d.data || d.resultados || d.rows;
    if (Array.isArray(alt)) { d.filas = alt; }
  }
  return d;
}

async function llamar(op, extra, ok, fallo) {
  var r = ROUTES[op];
  if (!r) { fallo('Operación desconocida: ' + op); return; }
  var datos = extra || {};
  try {
    var resp = await fetch(API_BASE + r.url(datos), {
      method: r.m,
      headers: { 'Content-Type': 'application/json' },
      body: r.body ? JSON.stringify(r.body(datos)) : undefined
    });
    var d = null;
    try { d = await resp.json(); } catch (e) { d = null; }
    if (!resp.ok) {
      var det = d && d.detail;
      fallo(det ? (typeof det === 'string' ? det : JSON.stringify(det)) : ('Error ' + resp.status));
      return;
    }
    d = normalizar(op, d);
    if (d.status === 'OK') { ok(d); } else { fallo(d.msg || 'Respuesta no válida'); }
  } catch (e) {
    fallo('Comunicación: ' + e.message);
  }
}
