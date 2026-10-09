"""
Painel web (frontend) para o ESP32 + DHT11.

Este programa roda no seu computador. Ele:
  1. mostra o painel no navegador (http://localhost:5000)
  2. busca os dados no ESP32 por HTTP (http://IP_DO_ESP32/api/dados)

Uso:
    pip install -r requirements.txt
    python app.py                      (usa o IP 10.74.22.240 já configurado)

Tambem funciona assim:
    ESP32_IP=10.74.22.240 python app.py
"""
import os
import sys
import socket
import threading
import time

import requests
from flask import Flask, Response, jsonify

# ===== CONFIGURACOES =====
ESP32_IP = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ESP32_IP", "10.74.22.240"))
ESP32_URL = f"http://{ESP32_IP}/api/dados"
PORTA = int(os.environ.get("PORTA", "5000"))
TIMEOUT_ESP32 = 3          # segundos esperando o ESP32 responder
CACHE_SEGUNDOS = 1.5       # evita sobrecarregar o ESP32 se houver varios navegadores abertos

app = Flask(__name__)

_cache = {"hora": 0.0, "status": 200, "corpo": None}
_trava = threading.Lock()


@app.route("/")
def pagina():
    return Response(PAGINA_HTML, mimetype="text/html")


@app.route("/api/dados")
def dados():
    """Repassa a leitura do ESP32 para o navegador."""
    with _trava:
        agora = time.time()
        if _cache["corpo"] is not None and agora - _cache["hora"] < CACHE_SEGUNDOS:
            return jsonify(_cache["corpo"]), _cache["status"]

        try:
            r = requests.get(ESP32_URL, timeout=TIMEOUT_ESP32)
            corpo = r.json()
            status = r.status_code          # 200 = ok, 500 = DHT11 sem leitura
        except requests.RequestException:
            return jsonify({"erro": "ESP32 sem resposta"}), 502
        except ValueError:
            return jsonify({"erro": "Resposta invalida do ESP32"}), 502

        _cache.update(hora=agora, status=status, corpo=corpo)
        return jsonify(corpo), status


def ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


# ===== PAGINA (HTML/CSS/JS) =====
PAGINA_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0a1c12">
<link rel="icon" href="data:,">
<title>Monitor DHT11</title>
<style>
:root{
  color-scheme:dark;
  --bg:#0a1c12;
  --card:#12291c;
  --cardline:#21402e;
  --solid:#12291c;
  --ink:#e9f0e2;
  --muted:#93a998;
  --track:rgba(181,199,124,.16);
  --soft:rgba(181,199,124,.08);
  --acc-t:#b9cb82;      /* verde musgo claro */
  --acc-h:#93b06e;      /* verde musgo */
  --ok:#b9cb82;
  --off:#5f7a66;
  --warn:#1a3324;
  font-family:ui-rounded,"SF Pro Rounded","Nunito","Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  min-height:100vh;
  background:var(--bg);
  color:var(--ink);
  padding:max(20px,env(safe-area-inset-top)) 16px 32px;
}
.wrap{max-width:880px;margin:0 auto}

/* topo */
header{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.marca{display:flex;align-items:center;gap:12px;font-weight:700;font-size:1.1rem;letter-spacing:-.01em}
.logo{width:40px;height:40px;border-radius:14px;background:var(--soft);border:1px solid var(--cardline);display:grid;place-items:center}
.status{display:flex;align-items:center;gap:8px;font-size:.85rem;color:var(--muted);
  padding:8px 14px;border-radius:999px;background:var(--card);border:1px solid var(--cardline)}
.dot{width:10px;height:10px;border-radius:50%;background:var(--ok)}
.status.on .dot{animation:pulse 2s ease-out infinite}
.status.off .dot{background:transparent;border:2px solid var(--off)}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(185,203,130,.55)}100%{box-shadow:0 0 0 9px rgba(185,203,130,0)}}

/* resumo e escalas */
.resumo{margin:30px 0 18px;font-size:clamp(1.7rem,5.5vw,2.5rem);font-weight:600;letter-spacing:-.025em;line-height:1.15;max-width:20ch}
.un{display:inline-flex;gap:4px;padding:4px;border-radius:999px;background:var(--card);border:1px solid var(--cardline)}
.un button{font:inherit;font-weight:700;font-size:.95rem;color:var(--muted);background:transparent;border:0;
  padding:8px 20px;border-radius:999px;cursor:pointer;min-width:58px}
.un button[aria-pressed="true"]{background:var(--acc-t);color:#13230f}
.un button:focus-visible{outline:2px solid var(--acc-t);outline-offset:2px}
.escala{margin:14px 0 22px;padding:12px 16px;border-radius:18px;background:var(--soft);
  font-size:.88rem;line-height:1.45;color:var(--muted);max-width:68ch}

.aviso{display:none;align-items:flex-start;gap:12px;margin:0 0 16px;padding:12px 16px;border-radius:18px;
  background:var(--warn);border:1px dashed var(--off);font-size:.9rem}
.aviso.show{display:flex}
.aviso::before{content:"!";flex:none;width:24px;height:24px;border-radius:50%;background:var(--acc-t);color:#13230f;
  font-weight:800;display:grid;place-items:center}

/* cards */
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:680px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--cardline);border-radius:32px;padding:24px 22px 20px;
  transition:opacity .4s,filter .4s}
#cardT{--acc:var(--acc-t)}
#cardH{--acc:var(--acc-h)}
body.off .card{opacity:.55;filter:grayscale(.6)}

.gauge{display:block;width:100%;max-width:270px;margin:0 auto;height:auto;overflow:visible}
.gauge path{fill:none;stroke-width:13;stroke-linecap:round}
.trk{stroke:var(--track)}
.arc{stroke:var(--acc);stroke-dasharray:0 100;transition:stroke-dasharray .9s cubic-bezier(.2,.8,.2,1)}
.thumb{transform-box:view-box;transform-origin:100px 100px;transform:rotate(135deg);
  transition:transform .9s cubic-bezier(.2,.8,.2,1)}
.thumb circle{fill:#f2f6e8;stroke:var(--acc);stroke-width:4}
.gv{font-size:48px;font-weight:400;letter-spacing:-2px;fill:var(--ink);text-anchor:middle;font-variant-numeric:tabular-nums}
.gu{font-size:15px;fill:var(--acc);text-anchor:middle;font-weight:600}
.gl{font-size:12.5px;fill:var(--muted);text-anchor:middle}
.ge{font-size:10.5px;fill:var(--muted);text-anchor:middle;font-variant-numeric:tabular-nums}

.spark{margin-top:10px;padding:12px 14px 8px;border-radius:22px;background:var(--soft)}
.readout{margin:0 0 6px;font-size:.82rem;color:var(--muted);min-height:1.2em;font-variant-numeric:tabular-nums}
.spark svg{display:block;width:100%;height:auto;color:var(--acc);touch-action:pan-y;cursor:crosshair}
.al{fill:none;stroke:currentColor;stroke-width:2.8;stroke-linejoin:round;stroke-linecap:round}
.aa{stroke:none}
.cur{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 3}
.pt{fill:currentColor;stroke:var(--card);stroke-width:2.5}

.mm{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.mm div{display:flex;flex-direction:column;gap:2px;padding:10px 14px;border-radius:18px;background:var(--soft)}
.mm div:last-child{text-align:right}
.mm span{font-size:.78rem;color:var(--muted)}
.mm b{font-size:1.05rem;font-weight:650;font-variant-numeric:tabular-nums}

footer{margin-top:22px;text-align:center;font-size:.8rem;color:var(--muted)}
footer p{margin:2px 0}
@media (prefers-reduced-motion:reduce){
  .status.on .dot{animation:none}
  .arc,.thumb,.card{transition:none}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="marca">
      <span class="logo">
        <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
          <rect x="2" y="12" width="5" height="8" rx="2.5" fill="#93b06e"/>
          <rect x="8.5" y="7" width="5" height="13" rx="2.5" fill="#a9bf79"/>
          <rect x="15" y="2" width="5" height="18" rx="2.5" fill="#b9cb82"/>
        </svg>
      </span>
      Monitor DHT11
    </div>
    <div id="status" class="status"><span class="dot"></span><span id="stxt">Conectando…</span></div>
  </header>

  <h1 id="resumo" class="resumo">Aguardando a primeira leitura…</h1>

  <div class="un" role="group" aria-label="Escala de temperatura">
    <button id="uC" aria-pressed="true">°C</button>
    <button id="uF" aria-pressed="false">°F</button>
    <button id="uK" aria-pressed="false">K</button>
  </div>
  <p id="escala" class="escala"></p>

  <p id="aviso" class="aviso"></p>

  <div class="grid">
    <!-- TEMPERATURA -->
    <section class="card" id="cardT">
      <svg class="gauge" viewBox="0 0 200 178" role="img" aria-label="Medidor de temperatura">
        <path class="trk" pathLength="100" d="M43.43 156.57 A80 80 0 1 1 156.57 156.57"/>
        <path class="arc" id="tarc" pathLength="100" d="M43.43 156.57 A80 80 0 1 1 156.57 156.57"/>
        <g class="thumb" id="tth"><circle cx="180" cy="100" r="6.5"/></g>
        <text class="gv" x="100" y="106" id="tv">--</text>
        <text class="gu" x="100" y="128" id="tu">°C</text>
        <text class="gl" x="100" y="160">Temperatura</text>
        <text class="ge" x="40" y="176" id="tlo">0</text>
        <text class="ge" x="160" y="176" id="thi">50</text>
      </svg>
      <div class="spark">
        <p class="readout" id="sTr">Últimos 3 minutos</p>
        <svg id="sT" viewBox="0 0 300 70" aria-label="Histórico de temperatura">
          <defs><linearGradient id="gaT" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="currentColor" stop-opacity=".35"/>
            <stop offset="1" stop-color="currentColor" stop-opacity="0"/>
          </linearGradient></defs>
          <path id="sTa" class="aa" fill="url(#gaT)" d=""/>
          <path id="sTl" class="al" d=""/>
          <line id="sTc" class="cur" y1="0" y2="70" style="display:none"/>
          <circle id="sTd" class="pt" r="4.5" style="display:none"/>
        </svg>
      </div>
      <div class="mm">
        <div><span>Mínima</span><b id="tmin">--</b></div>
        <div><span>Máxima</span><b id="tmax">--</b></div>
      </div>
    </section>

    <!-- UMIDADE -->
    <section class="card" id="cardH">
      <svg class="gauge" viewBox="0 0 200 178" role="img" aria-label="Medidor de umidade">
        <path class="trk" pathLength="100" d="M43.43 156.57 A80 80 0 1 1 156.57 156.57"/>
        <path class="arc" id="harc" pathLength="100" d="M43.43 156.57 A80 80 0 1 1 156.57 156.57"/>
        <g class="thumb" id="hth"><circle cx="180" cy="100" r="6.5"/></g>
        <text class="gv" x="100" y="106" id="hv">--</text>
        <text class="gu" x="100" y="128">%</text>
        <text class="gl" x="100" y="160">Umidade</text>
        <text class="ge" x="40" y="176">0</text>
        <text class="ge" x="160" y="176">100</text>
      </svg>
      <div class="spark">
        <p class="readout" id="sHr">Últimos 3 minutos</p>
        <svg id="sH" viewBox="0 0 300 70" aria-label="Histórico de umidade">
          <defs><linearGradient id="gaH" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="currentColor" stop-opacity=".35"/>
            <stop offset="1" stop-color="currentColor" stop-opacity="0"/>
          </linearGradient></defs>
          <path id="sHa" class="aa" fill="url(#gaH)" d=""/>
          <path id="sHl" class="al" d=""/>
          <line id="sHc" class="cur" y1="0" y2="70" style="display:none"/>
          <circle id="sHd" class="pt" r="4.5" style="display:none"/>
        </svg>
      </div>
      <div class="mm">
        <div><span>Mínima</span><b id="hmin">--</b></div>
        <div><span>Máxima</span><b id="hmax">--</b></div>
      </div>
    </section>
  </div>

  <footer>
    <p id="rodape">Atualiza a cada 2 segundos.</p>
    <p>Mínimas e máximas valem desde que esta página foi aberta.</p>
  </footer>
</div>

<script>
const MAX = 90;            // 90 leituras x 2 s = 3 min
const INTERVALO = 2000;
const W = 300, H = 70;

const $ = id => document.getElementById(id);
const hist = [];
const mm = { tmin: null, tmax: null, hmin: null, hmax: null };
const sp = {
  t: { id: 'sT', minSpan: 2, xs: [], ys: [], vx: null },
  h: { id: 'sH', minSpan: 6, xs: [], ys: [], vx: null }
};
let cur = null;
let u = 'C';
try {
  const salvo = localStorage.getItem('unidade');
  if (salvo === 'F' || salvo === 'K') u = salvo;
} catch (e) {}

// ----- escalas de temperatura -----
const ESCALAS = {
  C: { simbolo: '°C', conv: c => c,
       texto: 'Celsius: 0 °C é o ponto de fusão do gelo e 100 °C o de ebulição da água, em 100 partes iguais. É a escala do dia a dia no Brasil.' },
  F: { simbolo: '°F', conv: c => c * 9 / 5 + 32,
       texto: 'Fahrenheit: a água congela a 32 °F e ferve a 212 °F, em 180 partes. É usada principalmente nos Estados Unidos e em países de língua inglesa.' },
  K: { simbolo: 'K', conv: c => c + 273.15,
       texto: 'Kelvin: escala absoluta e unidade oficial do SI. 0 K é o zero absoluto, a ausência total de agitação molecular. Não leva o símbolo de grau.' }
};
const conv = c => ESCALAS[u].conv(c);
const fmt = v => v.toFixed(1).replace('.', ',');
const pct = (v, a, b) => Math.max(0, Math.min(100, (v - a) / (b - a) * 100));
const valor = (k, v) => k === 't' ? fmt(conv(v)) + ' ' + ESCALAS[u].simbolo : fmt(v) + ' %';

function resumo(t, h) {
  const a = t < 18 ? 'frio' : t < 27 ? 'agradável' : t < 32 ? 'quente' : 'muito quente';
  const b = h < 30 ? 'seco' : h <= 60 ? 'confortável' : 'úmido';
  return 'Está ' + a + ' e o ar está ' + b + '.';
}

function status(estado, texto) {
  $('status').className = 'status ' + estado;
  $('stxt').textContent = texto;
  document.body.classList.toggle('off', estado === 'off');
}
function aviso(msg) {
  const el = $('aviso');
  el.textContent = msg || '';
  el.classList.toggle('show', !!msg);
}

// ----- grafico -----
function mostrarPonto(k) {
  const s = sp[k], c = $(s.id + 'c'), d = $(s.id + 'd'), r = $(s.id + 'r');
  if (s.vx === null || !s.xs.length) {
    c.style.display = d.style.display = 'none';
    r.textContent = 'Últimos 3 minutos';
    return;
  }
  let i = 0, melhor = 1e9;
  s.xs.forEach((x, j) => {
    const dx = Math.abs(x - s.vx);
    if (dx < melhor) { melhor = dx; i = j; }
  });
  c.setAttribute('x1', s.xs[i]); c.setAttribute('x2', s.xs[i]);
  d.setAttribute('cx', s.xs[i]); d.setAttribute('cy', s.ys[i]);
  c.style.display = d.style.display = '';
  const idade = (hist.length - 1 - i) * INTERVALO / 1000;
  r.textContent = (idade ? 'Há ' + idade + ' s: ' : 'Agora: ') + valor(k, hist[i][k]);
}

function desenhar(k) {
  const s = sp[k], n = hist.length;
  s.xs = []; s.ys = [];
  if (n < 2) {
    $(s.id + 'l').setAttribute('d', '');
    $(s.id + 'a').setAttribute('d', '');
    mostrarPonto(k);
    return;
  }
  const v = hist.map(p => p[k]);
  let lo = Math.min(...v), hi = Math.max(...v);
  const span = Math.max(hi - lo, s.minSpan), mid = (hi + lo) / 2;
  lo = mid - span / 2;
  for (let i = 0; i < n; i++) {
    s.xs.push(W - (n - 1 - i) / (MAX - 1) * W);
    s.ys.push(H - 8 - (v[i] - lo) / span * (H - 16));
  }
  const linha = s.xs.map((x, i) => (i ? 'L' : 'M') + x.toFixed(1) + ' ' + s.ys[i].toFixed(1)).join(' ');
  $(s.id + 'l').setAttribute('d', linha);
  $(s.id + 'a').setAttribute('d', linha + ' L' + s.xs[n - 1].toFixed(1) + ' ' + H + ' L' + s.xs[0].toFixed(1) + ' ' + H + ' Z');
  mostrarPonto(k);
}

// ----- tela -----
function rotulosEscala() {
  $('tlo').textContent = Math.round(conv(0));
  $('thi').textContent = Math.round(conv(50));
  $('tu').textContent = ESCALAS[u].simbolo;
  $('escala').textContent = ESCALAS[u].texto;
}

function render() {
  rotulosEscala();
  if (!cur) return;
  const t = cur.t, h = cur.h;
  const tp = pct(t, 0, 50), hp = pct(h, 0, 100);

  $('tv').textContent = fmt(conv(t));
  $('hv').textContent = fmt(h);

  $('tarc').style.strokeDasharray = tp + ' 100';
  $('harc').style.strokeDasharray = hp + ' 100';
  $('tth').style.transform = 'rotate(' + (135 + 2.7 * tp) + 'deg)';
  $('hth').style.transform = 'rotate(' + (135 + 2.7 * hp) + 'deg)';

  $('tmin').textContent = valor('t', mm.tmin);
  $('tmax').textContent = valor('t', mm.tmax);
  $('hmin').textContent = valor('h', mm.hmin);
  $('hmax').textContent = valor('h', mm.hmax);

  $('resumo').textContent = resumo(t, h);
  desenhar('t');
  desenhar('h');
}

function atualizar(t, h) {
  cur = { t: t, h: h };
  mm.tmin = mm.tmin === null ? t : Math.min(mm.tmin, t);
  mm.tmax = mm.tmax === null ? t : Math.max(mm.tmax, t);
  mm.hmin = mm.hmin === null ? h : Math.min(mm.hmin, h);
  mm.hmax = mm.hmax === null ? h : Math.max(mm.hmax, h);
  hist.push({ t: t, h: h });
  if (hist.length > MAX) hist.shift();
  render();
}

function setUnidade(x) {
  u = x;
  try { localStorage.setItem('unidade', x); } catch (e) {}
  ['C', 'F', 'K'].forEach(k => $('u' + k).setAttribute('aria-pressed', k === x));
  render();
}
['C', 'F', 'K'].forEach(k => { $('u' + k).onclick = () => setUnidade(k); });
setUnidade(u);

['t', 'h'].forEach(k => {
  const svg = $(sp[k].id);
  const mover = e => {
    const r = svg.getBoundingClientRect();
    sp[k].vx = (e.clientX - r.left) / r.width * W;
    mostrarPonto(k);
  };
  svg.addEventListener('pointermove', mover);
  svg.addEventListener('pointerdown', mover);
  svg.addEventListener('pointerleave', () => { sp[k].vx = null; mostrarPonto(k); });
});

async function buscar() {
  try {
    const r = await fetch('/api/dados', { cache: 'no-store' });
    if (r.status === 500) {
      status('off', 'Sensor sem leitura');
      aviso('O ESP32 respondeu, mas o DHT11 não retornou dados. Verifique a fiação do sensor (pino 15).');
      return;
    }
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    atualizar(d.temperatura, d.umidade);
    aviso('');
    status('on', 'Ao vivo');
    $('rodape').textContent = 'Última atualização às ' + new Date().toLocaleTimeString('pt-BR') + '.';
  } catch (e) {
    status('off', 'ESP32 sem resposta');
    aviso('Não foi possível falar com o ESP32. Confira se ele está ligado e na mesma rede Wi-Fi.');
  }
}

buscar();
setInterval(buscar, INTERVALO);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print(f"ESP32 configurado em: {ESP32_URL}")
    print(f"Painel neste computador: http://localhost:{PORTA}")
    print(f"Painel em outros aparelhos da rede: http://{ip_local()}:{PORTA}")
    app.run(host="0.0.0.0", port=PORTA, debug=False, threaded=True)
