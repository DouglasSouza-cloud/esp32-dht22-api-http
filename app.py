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
<link rel="icon" href="data:,">
<title>Sensor DHT11</title>
<style>
@property --h{syntax:"<number>";inherits:true;initial-value:200}
:root{
  --h:200;
  transition:--h 1.5s ease;
  --bg:hsl(var(--h) 40% 92%);
  --bg2:hsl(calc(var(--h) + 24) 48% 83%);
  --card:rgba(255,255,255,.6);
  --cardline:rgba(255,255,255,.8);
  --solid:#fff;
  --ink:#15242b;
  --muted:#52666f;
  --track:rgba(21,36,43,.12);
  --acc-t:hsl(var(--h) 72% 42%);
  --acc-h:hsl(196 75% 38%);
  --ok:#23824f; --err:#b3261e;
  font-family:ui-rounded,"SF Pro Rounded","Nunito","Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:hsl(var(--h) 34% 10%);
    --bg2:hsl(calc(var(--h) + 24) 38% 16%);
    --card:rgba(255,255,255,.07);
    --cardline:rgba(255,255,255,.12);
    --solid:#22333b;
    --ink:#e8f0f3;
    --muted:#9bb0ba;
    --track:rgba(255,255,255,.15);
    --acc-t:hsl(var(--h) 85% 62%);
    --acc-h:hsl(193 80% 60%);
    --ok:#52cc8a; --err:#ff8a80;
  }
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  min-height:100vh;
  color:var(--ink);
  background:linear-gradient(160deg,var(--bg),var(--bg2)) fixed;
  padding:max(18px,env(safe-area-inset-top)) 16px 28px;
}
.wrap{max-width:840px;margin:0 auto}

header{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
h1{margin:0;font-size:1.05rem;font-weight:650;letter-spacing:-.01em}
.ctrl{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.status{display:flex;align-items:center;gap:8px;font-size:.85rem;color:var(--muted);
  padding:6px 12px;border-radius:999px;background:var(--card);border:1px solid var(--cardline)}
.dot{width:9px;height:9px;border-radius:50%;background:var(--muted)}
.status.on .dot{background:var(--ok);animation:pulse 2s ease-out infinite}
.status.off .dot{background:var(--err)}
@keyframes pulse{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--ok) 55%,transparent)}100%{box-shadow:0 0 0 9px transparent}}
.seg{display:inline-flex;padding:3px;border-radius:999px;background:var(--track)}
.seg button{
  font:inherit;font-size:.85rem;font-weight:600;color:var(--muted);
  border:0;background:transparent;padding:5px 14px;border-radius:999px;cursor:pointer;
}
.seg button[aria-pressed="true"]{background:var(--solid);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.15)}
button:focus-visible{outline:2px solid var(--acc-h);outline-offset:2px}

.resumo{margin:22px 0 22px;font-size:clamp(1.5rem,5vw,2.1rem);font-weight:500;letter-spacing:-.025em;line-height:1.2;max-width:22ch}

.aviso{display:none;margin:0 0 16px;padding:12px 14px;border-radius:12px;font-size:.9rem;
  background:color-mix(in srgb,var(--err) 14%,var(--card));border:1px solid var(--err)}
.aviso.show{display:block}

.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:640px){.grid{grid-template-columns:1fr}}
.card{
  background:var(--card);border:1px solid var(--cardline);border-radius:24px;padding:22px 20px 18px;
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  transition:opacity .4s,filter .4s;
}
#cardT{--acc:var(--acc-t)} #cardH{--acc:var(--acc-h)}
body.off .card{opacity:.55;filter:saturate(.4)}

.gauge{display:block;width:100%;max-width:270px;margin:0 auto;height:auto;overflow:visible}
.gauge path{fill:none;stroke-width:12;stroke-linecap:round}
.trk{stroke:var(--track)}
.arc{stroke:var(--acc);stroke-dasharray:0 100;transition:stroke-dasharray .9s cubic-bezier(.2,.8,.2,1)}
.thumb{transform-box:view-box;transform-origin:100px 100px;transform:rotate(135deg);
  transition:transform .9s cubic-bezier(.2,.8,.2,1)}
.thumb circle{fill:#fff;stroke:var(--acc);stroke-width:4}
.gv{font-size:48px;font-weight:300;letter-spacing:-2px;fill:var(--ink);text-anchor:middle;font-variant-numeric:tabular-nums}
.gu{font-size:15px;fill:var(--muted);text-anchor:middle;font-weight:500}
.gl{font-size:12.5px;fill:var(--muted);text-anchor:middle}
.ge{font-size:10.5px;fill:var(--muted);text-anchor:middle;font-variant-numeric:tabular-nums}

.spark{margin-top:6px}
.readout{margin:0 0 4px;font-size:.82rem;color:var(--muted);min-height:1.2em;font-variant-numeric:tabular-nums}
.spark svg{display:block;width:100%;height:auto;color:var(--acc);touch-action:pan-y;cursor:crosshair}
.al{fill:none;stroke:currentColor;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
.aa{stroke:none}
.cur{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 3}
.pt{fill:currentColor;stroke:var(--solid);stroke-width:2.5}

.mm{display:flex;justify-content:space-between;margin:12px 0 0;padding-top:12px;border-top:1px solid var(--track)}
.mm div{display:flex;flex-direction:column;gap:2px}
.mm div:last-child{text-align:right}
.mm span{font-size:.78rem;color:var(--muted)}
.mm b{font-size:1.05rem;font-weight:600;font-variant-numeric:tabular-nums}

footer{margin-top:20px;text-align:center;font-size:.8rem;color:var(--muted)}
footer p{margin:2px 0}
@media (prefers-reduced-motion:reduce){
  :root{transition:none}
  .status.on .dot{animation:none}
  .arc,.thumb,.card{transition:none}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Sensor DHT11</h1>
    <div class="ctrl">
      <div id="status" class="status"><span class="dot"></span><span id="stxt">Conectando…</span></div>
      <div class="seg" role="group" aria-label="Unidade de temperatura">
        <button id="uC" aria-pressed="true">°C</button>
        <button id="uF" aria-pressed="false">°F</button>
      </div>
    </div>
  </header>

  <p id="resumo" class="resumo">Aguardando a primeira leitura…</p>
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
            <stop offset="0" stop-color="currentColor" stop-opacity=".32"/>
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
            <stop offset="0" stop-color="currentColor" stop-opacity=".32"/>
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
try { u = localStorage.getItem('unidade') === 'F' ? 'F' : 'C'; } catch (e) {}

const conv = c => u === 'F' ? c * 9 / 5 + 32 : c;
const fmt = v => v.toFixed(1).replace('.', ',');
const pct = (v, a, b) => Math.max(0, Math.min(100, (v - a) / (b - a) * 100));
const valor = (k, v) => k === 't' ? fmt(conv(v)) + ' °' + u : fmt(v) + ' %';

function resumo(t, h) {
  const a = t < 18 ? 'frio' : t < 27 ? 'agradável' : t < 32 ? 'quente' : 'muito quente';
  const b = h < 30 ? 'seco' : h <= 60 ? 'confortável' : 'úmido';
  return 'Está ' + a + ' e o ar está ' + b + '.';
}

// Cor ambiente: azul (frio) -> verde (agradavel) -> laranja/vermelho (quente)
function matiz(t) {
  const p = (Math.max(5, Math.min(38, t)) - 5) / 33;
  return Math.round(215 - p * 205);
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

function render() {
  if (!cur) return;
  const t = cur.t, h = cur.h;
  const tp = pct(t, 0, 50), hp = pct(h, 0, 100);

  $('tv').textContent = fmt(conv(t));
  $('tu').textContent = '°' + u;
  $('hv').textContent = fmt(h);
  $('tlo').textContent = Math.round(conv(0));
  $('thi').textContent = Math.round(conv(50));

  $('tarc').style.strokeDasharray = tp + ' 100';
  $('harc').style.strokeDasharray = hp + ' 100';
  $('tth').style.transform = 'rotate(' + (135 + 2.7 * tp) + 'deg)';
  $('hth').style.transform = 'rotate(' + (135 + 2.7 * hp) + 'deg)';

  $('tmin').textContent = valor('t', mm.tmin);
  $('tmax').textContent = valor('t', mm.tmax);
  $('hmin').textContent = valor('h', mm.hmin);
  $('hmax').textContent = valor('h', mm.hmax);

  $('resumo').textContent = resumo(t, h);
  document.documentElement.style.setProperty('--h', matiz(t));

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
  $('uC').setAttribute('aria-pressed', x === 'C');
  $('uF').setAttribute('aria-pressed', x === 'F');
  render();
}
$('uC').onclick = () => setUnidade('C');
$('uF').onclick = () => setUnidade('F');
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
