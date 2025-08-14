// ================== Clock ==================
const dateEl = document.querySelector('.date');
const timeEl = document.querySelector('.time');
function tickClock(){
  const now = new Date();
  dateEl.textContent = now.toLocaleDateString();
  timeEl.textContent = now.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
}
setInterval(tickClock, 1000); tickClock();

// ================== Theme Persist ==================
const html = document.documentElement;
const themeBtn = document.getElementById('btn-theme');
(function initTheme(){
  const saved = localStorage.getItem('st_theme') || 'light';
  html.setAttribute('data-theme', saved);
  themeBtn.textContent = saved==='dark' ? '☀' : '🌙';
})();
themeBtn.onclick = () => {
  const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('st_theme', next);
  themeBtn.textContent = next==='dark' ? '☀' : '🌙';
};

// ================== Fullscreen ==================
document.getElementById('btn-fullscreen').onclick = () => {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen();
  else document.exitFullscreen();
};

// ================== State ==================
const state = {
  mode: 'auto',
  directionIndex: 0,
  directions: ['North','East','South','West'],
  baseGreen: 15,
  yellow: 3,
  weather: 'Clear',
  emergencyActive: false,
  emergencyEndsAt: 0,
  density: [14, 9, 12, 10],
  history: [],
  alerts: [],
  accidentCount: 0
};

const ui = {
  dir: document.getElementById('direction'),
  countdown: document.getElementById('countdown'),
  redTime: document.getElementById('red-time'),
  yellowTime: document.getElementById('yellow-time'),
  greenTime: document.getElementById('green-time'),
  btnAuto: document.getElementById('btn-auto'),
  btnManual: document.getElementById('btn-manual'),
  btnEmergency: document.getElementById('btn-emergency'),
  peakPill: document.getElementById('peak-pill'),
  priorityPill: document.getElementById('priority-pill'),
  weatherPill: document.getElementById('weather-pill'),
  weatherPill2: document.getElementById('weather-pill-2'),
  accidentPill: document.getElementById('accident-pill'),
  alertList: document.getElementById('alert-list'),
  lights: {
    red: document.querySelector('.light.red'),
    yellow: document.querySelector('.light.yellow'),
    green: document.querySelector('.light.green')
  },
  arrows: {
    n: document.getElementById('arrow-n'),
    e: document.getElementById('arrow-e'),
    s: document.getElementById('arrow-s'),
    w: document.getElementById('arrow-w'),
  }
};

// ================== Helpers ==================
function isPeakHour(d= new Date()){
  const h = d.getHours();
  return (h>=8 && h<10) || (h>=18 && h<20);
}
function weatherImpactFactor(weather){
  if (weather === 'Rain') return 1.25;
  if (weather === 'Fog') return 1.35;
  return 1.0;
}
function randomPick(arr){ return arr[Math.floor(Math.random()*arr.length)]; }
function addAlert(text, type='info'){
  state.alerts.unshift({text, type, ts: new Date()});
  if (state.alerts.length>30) state.alerts.pop();
  renderAlerts();
}
function renderAlerts(){
  if (state.alerts.length===0){
    ui.alertList.innerHTML = '<li>No alerts yet.</li>';
    return;
  }
  ui.alertList.innerHTML = state.alerts.map(a=>{
    const badge = a.type==='danger' ? '<span class="badge danger">ALERT</span>' :
                  a.type==='warn'   ? '<span class="badge warn">WARN</span>' :
                                       '<span class="badge ok">INFO</span>';
    return `<li>${badge} ${a.text} <small class="muted">(${a.ts.toLocaleTimeString()})</small></li>`;
  }).join('');
}

// ================== Weather Simulator ==================
const weatherCycle = ['Clear','Clear','Rain','Clear','Fog'];
setInterval(()=>{
  if (Math.random() < 0.30){
    state.weather = randomPick(weatherCycle);
    ui.weatherPill.textContent = (state.weather==='Clear'?'☀ ':'🌦 ') + state.weather;
    ui.weatherPill2.innerHTML = `🌦 Weather Control: <b>${state.weather==='Clear'?'Off':'On'}</b>`;
    addAlert(`Weather changed to ${state.weather}. Green duration auto-adjusted.`, 'info');
  }
}, 15000);

// ================== Density Simulator ==================
let t = 0;
function simulateDensity(){
  for (let i=0;i<4;i++){
    const delta = Math.round((Math.random()-0.45)*4);
    state.density[i] = Math.max(0, state.density[i] + delta);
  }
  if (isPeakHour()) {
    const idx = Math.floor(Math.random()*4);
    state.density[idx] += 3;
  }
  if (!state.emergencyActive && Math.random()<0.08){
    triggerPriorityVehicle(randomPick(state.directions));
  }
  if (Math.random()<0.04){
    state.accidentCount++;
    ui.accidentPill.innerHTML = `⚠ Accident Alerts: <b>${state.accidentCount}</b>`;
    addAlert(`Possible accident detected at ${randomPick(state.directions)} approach. Dispatch unit.`, 'danger');
  }
  if (t%5===0){
    const sum = state.density.reduce((a,b)=>a+b,0);
    state.history.push(sum);
    if (state.history.length>30) state.history.shift();
    updatePredictionChart();
  }
  updateDensityChart();
  t++;
}
setInterval(simulateDensity, 2000);

// ================== Priority Vehicle (Auto Emergency) ==================
function triggerPriorityVehicle(dir){
  state.emergencyActive = true;
  state.emergencyEndsAt = Date.now() + 10000; // 10s
  ui.priorityPill.innerHTML = `🚑 Priority Vehicle: <b>${dir}</b>`;
  addAlert(`Priority vehicle detected on ${dir}. Emergency mode ON for 10s.`, 'warn');
  setLights('green');
}
function checkEmergencyTimeout(){
  if (state.emergencyActive && Date.now() > state.emergencyEndsAt){
    state.emergencyActive = false;
    ui.priorityPill.innerHTML = `🚑 Priority Vehicle: <b>None</b>`;
    addAlert('Emergency mode ended. Resuming normal cycle.', 'info');
  }
}
setInterval(checkEmergencyTimeout, 500);

// ================== Signal Timing ==================
let phaseEndsAt = Date.now() + 15000;
let phase = 'green';

function effectiveGreenSeconds(){
  let g = state.baseGreen;
  if (isPeakHour()) g = Math.round(g*1.2);
  g = Math.round(g * weatherImpactFactor(state.weather));
  return Math.max(8, Math.min(45, g));
}

function setLights(which){
  ui.lights.red.classList.remove('active');
  ui.lights.yellow.classList.remove('active');
  ui.lights.green.classList.remove('active');
  if (which==='red') ui.lights.red.classList.add('active');
  if (which==='yellow') ui.lights.yellow.classList.add('active');
  if (which==='green') ui.lights.green.classList.add('active');
}

function setActiveArrow(){
  const map = {0:'n',1:'e',2:'s',3:'w'};
  Object.values(ui.arrows).forEach(a=>a.classList.remove('active-arrow'));
  ui.arrows[map[state.directionIndex]].classList.add('active-arrow');
}

function nextDirection(){
  state.directionIndex = (state.directionIndex+1) % 4;
  ui.dir.textContent = state.directions[state.directionIndex];
  setActiveArrow();
}

function updateSignalLoop(){
  if (state.mode==='manual' && !state.emergencyActive){
    requestAnimationFrame(updateSignalLoop);
    return;
  }
  const now = Date.now();
  const remain = Math.max(0, Math.ceil((phaseEndsAt - now)/1000));
  ui.countdown.textContent = `${Math.floor(remain/60)}:${String(remain%60).padStart(2,'0')}`;

  if (phase==='green'){
    setLights('green');
    const g = effectiveGreenSeconds();
    ui.greenTime.textContent = g;
    ui.yellowTime.textContent = state.yellow;
    ui.redTime.textContent = g + state.yellow;

    if (state.emergencyActive) phaseEndsAt = state.emergencyEndsAt;
    if (now >= phaseEndsAt){
      phase = 'yellow';
      phaseEndsAt = now + state.yellow*1000;
    }
  } else if (phase==='yellow'){
    setLights('yellow');
    if (now >= phaseEndsAt){
      phase = 'green';
      nextDirection();
      const g = effectiveGreenSeconds();
      phaseEndsAt = now + g*1000;
    }
  }
  ui.peakPill.innerHTML = `⏫ Peak Hour: <b>${isPeakHour()?'On':'Auto'}</b>`;
  requestAnimationFrame(updateSignalLoop);
}
phaseEndsAt = Date.now() + effectiveGreenSeconds()*1000;
setActiveArrow();
updateSignalLoop();

// ================== Buttons ==================
ui.btnAuto.onclick = ()=>{ state.mode='auto'; addAlert('Switched to Auto mode.', 'info'); };
ui.btnManual.onclick = ()=>{ state.mode='manual'; addAlert('Switched to Manual mode. Auto cycle paused.', 'info'); };
ui.btnEmergency.onclick = ()=>{ triggerPriorityVehicle(state.directions[state.directionIndex]); };

// ================== Charts ==================
let densityChart, predictChart;

function buildDensityChart(){
  const ctx = document.getElementById('densityChart').getContext('2d');
  densityChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: state.directions,
      datasets: [{ label: 'Vehicles Waiting', data: state.density }]
    },
    options: {
      responsive: true,
      animation: { duration: 400 },
      plugins:{ legend:{ display:false } },
      scales:{ y: { beginAtZero:true } }
    }
  });
}
function updateDensityChart(){
  if (!densityChart) return;
  densityChart.data.datasets[0].data = state.density.slice();
  densityChart.update();
}

function predictNext10(history){
  const h = history.length ? history : [8,10,12,11,9,10];
  const last = h[h.length-1];
  const avg = h.slice(-6).reduce((a,b)=>a+b,0) / Math.min(6,h.length);
  const drift = (last - (h[h.length-2] ?? last)) * 0.4;
  const out = []; let cur = last;
  for (let i=0;i<10;i++){
    const noise = (Math.random()-0.5)*2;
    cur = Math.max(0, cur + 0.3*(avg-cur) + drift*0.2 + noise);
    out.push(Math.round(cur));
  }
  return out;
}
function buildPredictChart(){
  const ctx = document.getElementById('predictChart').getContext('2d');
  predictChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array.from({length:10}, (_,i)=>`${i+1}m`),
      datasets: [{ label: 'Predicted Total Vehicles', data: predictNext10(state.history), fill: false, tension: 0.35 }]
    },
    options: {
      responsive:true,
      animation: { duration: 500 },
      plugins:{ legend:{ display:false } },
      scales:{ y:{ beginAtZero:true } }
    }
  });
}
function updatePredictionChart(){
  if (!predictChart) return;
  predictChart.data.datasets[0].data = predictNext10(state.history);
  predictChart.update();
}
buildDensityChart();
buildPredictChart();
renderAlerts();

// ================== Export CSV ==================
document.getElementById('btn-export').onclick = () => {
  const rows = [];
  const now = new Date().toISOString();
  rows.push(['timestamp', now]);
  rows.push(['mode', state.mode]);
  rows.push(['direction', state.directions[state.directionIndex]]);
  rows.push(['weather', state.weather]);
  rows.push(['accident_count', state.accidentCount]);
  rows.push([]);
  rows.push(['direction','vehicles_waiting']);
  state.directions.forEach((d, i)=> rows.push([d, state.density[i]]));
  rows.push([]);
  rows.push(['prediction_minute','predicted_total']);
  predictNext10(state.history).forEach((v,i)=> rows.push([i+1, v]));

  const csv = rows.map(r=>r.join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `smart-traffic-${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
  addAlert('CSV report downloaded.', 'info');
};
