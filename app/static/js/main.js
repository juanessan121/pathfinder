let map, linesLayer, nodes = {}, edges = [], markers = {};

// Colores del sistema
const COLORS = {
    start: '#22C55E',  // Verde
    end: '#EF4444',    // Rojo
    mid: '#3B82F6',    // Azul
    route: '#6366F1'   // Indigo
};

// Generador de Icono
const getIconHtml = (color) => `<div style="background-color:${color}; width:16px; height:16px; border-radius:50%; border:3px solid white; box-shadow:0 4px 6px rgba(0,0,0,0.3);"></div>`;

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadFromLocal();
    enableSmartAutocomplete('nodeName', 'nodeSuggestions'); // Activa la búsqueda tipo Google
    updateWizardUI();
});

function initMap() {
    const street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 });
    map = L.map('map', { center: [-1.2491, -78.6168], zoom: 14, layers: [street], zoomControl: false });
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    linesLayer = L.layerGroup().addTo(map);

    // --- EVENTO CLIC EN MAPA (AUTO-NOMBRE) ---
    map.on('click', (e) => {
        // 1. Llenar coordenadas
        document.getElementById('nodeLat').value = e.latlng.lat.toFixed(5);
        document.getElementById('nodeLng').value = e.latlng.lng.toFixed(5);

        // 2. AUTO-NOMBRE: Si el input está vacío, pone la siguiente letra (A, B, C...)
        const nameInput = document.getElementById('nodeName');
        if(!nameInput.value.trim()) {
            nameInput.value = getNextName();
        }

        // 3. Tocar en el mapa
        const pulse = L.circleMarker(e.latlng, { radius: 5, color: COLORS.route, fillOpacity:0.5 }).addTo(map);
        setTimeout(() => map.removeLayer(pulse), 500);
    });
}

//  BUSCADOR TIPO
function enableSmartAutocomplete(inputId, resultsId) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    let timeout = null;

    // Cerrar lista si clicas fuera
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !results.contains(e.target)) results.style.display = 'none';
    });

    input.addEventListener('input', () => {
        const q = input.value.trim();
        // Si es muy corto (probablemente una letra A, B, C manual), no busques
        if (q.length < 3) { results.style.display = 'none'; return; }

        if (timeout) clearTimeout(timeout);

        timeout = setTimeout(async () => {
            try {
                // Búsqueda priorizando la vista actual del mapa
                const b = map.getBounds();
                const viewbox = `${b.getWest()},${b.getNorth()},${b.getEast()},${b.getSouth()}`;

                const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=5&countrycodes=ec&viewbox=${viewbox}`);
                const data = await res.json();

                results.innerHTML = '';
                if(data.length === 0) { results.style.display = 'none'; return; }

                data.forEach(p => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    // Diseño de cada item de la lista
                    div.innerHTML = `
                        <i class="fas fa-map-marker-alt"></i>
                        <div style="overflow:hidden;">
                            <b>${p.name || p.display_name.split(',')[0]}</b>
                            <small>${p.display_name}</small>
                        </div>
                    `;

                    div.onclick = () => {
                        // Al hacer clic en sugerencia:
                        const lat = parseFloat(p.lat);
                        const lon = parseFloat(p.lon);

                        // 1. Volar al sitio
                        map.setView([lat, lon], 16);

                        // 2. Llenar inputs
                        document.getElementById('nodeLat').value = lat.toFixed(5);
                        document.getElementById('nodeLng').value = lon.toFixed(5);
                        document.getElementById('nodeName').value = p.name || p.display_name.split(',')[0]; // Pone el nombre real

                        results.style.display = 'none';
                    };
                    results.appendChild(div);
                });
                results.style.display = 'block';
            } catch(e) { console.error(e); }
        }, 300); // Espera 300ms antes de buscar para no saturar
    });
}

// Generar nombre automático (A, B, C...)
function getNextName() {
    let i = 0;
    while(true) {
        let c = String.fromCharCode(65 + (i % 26));
        if (i >= 26) c += (Math.floor(i/26) + 1);
        if (!nodes[c]) return c;
        i++;
    }
}

// Agregar Nodo al Sistema
async function addNode() {
    let name = document.getElementById('nodeName').value.trim();
    let lat = document.getElementById('nodeLat').value;
    let lng = document.getElementById('nodeLng').value;

    // Validación básica
    if (!name && !isNaN(parseFloat(lat))) name = getNextName(); // Respaldo final

    if (name && lat && lng) {
        if(nodes[name]) return Swal.fire('Duplicado', 'Ese nombre ya existe', 'warning');

        nodes[name] = [parseFloat(lat), parseFloat(lng)];
        createMarker(name, nodes[name][0], nodes[name][1]);

        document.getElementById('nodeName').value = ''; // Limpiar para el siguiente
        saveToLocal();
        updateWizardUI();

        Swal.mixin({toast: true, position: 'top-end', showConfirmButton: false, timer: 1500})
            .fire({icon: 'success', title: 'Punto Agregado'});

        // Autocompletar conexión si hay historial
        const keys = Object.keys(nodes);
        if(keys.length > 1) {
            document.getElementById('edgeFrom').value = keys[keys.length-2];
            document.getElementById('edgeTo').value = name;
        }
    } else {
        Swal.fire('Faltan datos', 'Selecciona un punto en el mapa', 'warning');
    }
}

function createMarker(name, lat, lng, type='mid') {
    const color = COLORS[type];
    const icon = L.divIcon({ className: 'custom-pin', html: getIconHtml(color), iconSize: [16, 16], iconAnchor: [8, 8], popupAnchor: [0, -10] });

    if(markers[name]) map.removeLayer(markers[name]);
    const m = L.marker([lat, lng], {icon: icon}).addTo(map);
    m.bindPopup(`<b>${name}</b>`);
    markers[name] = m;
}

// Resto de funciones (addEdge, deleteNode, calculatePath, drawMapLines, updateWizardUI, save/load)
function updateWizardUI() {
    const count = Object.keys(nodes).length;
    document.getElementById('pointsCount').innerText = `${count} puntos agregados`;
    const s2 = document.getElementById('step2');
    const s3 = document.getElementById('step3');

    if(count >= 2) {
        s2.classList.remove('disabled');
        if(edges.length > 0) s3.classList.remove('disabled'); else s3.classList.add('disabled');
    } else {
        s2.classList.add('disabled'); s3.classList.add('disabled');
    }
}

function deleteNode() {
    const name = document.getElementById('deleteNodeName').value.trim();
    if(nodes[name]) {
        map.removeLayer(markers[name]); delete nodes[name]; delete markers[name];
        edges = edges.filter(e => e.from !== name && e.to !== name);
        saveToLocal(); drawMapLines(); updateWizardUI();
        document.getElementById('deleteNodeName').value = '';
    }
}

function addEdge() {
    const f=document.getElementById('edgeFrom').value, t=document.getElementById('edgeTo').value;
    if(nodes[f] && nodes[t]) { edges.push({from:f, to:t}); saveToLocal(); drawMapLines(); updateWizardUI(); }
}

function drawMapLines(path=[], geo=[]) {
    linesLayer.clearLayers();
    edges.forEach(e => { if(nodes[e.from] && nodes[e.to]) L.polyline([nodes[e.from], nodes[e.to]], {color:'#94a3b8', dashArray:'5,5'}).addTo(linesLayer); });
    if(geo.length) {
        L.polyline(geo, {color: COLORS.route, weight:6, opacity:0.5}).addTo(linesLayer);
        L.polyline(geo, {color: COLORS.route, weight:3}).addTo(linesLayer);
    }
}

async function calculatePath() {
    // ... Misma lógica de cálculo ...
    const s = document.getElementById('startNode').value, e = document.getElementById('endNode').value;
    const res = await fetch('/api/calculate-path', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({nodes, edges, start:s, end:e})});
    const d = await res.json();
    if(d.path) {
        drawMapLines(d.path, d.geometry);
        document.getElementById('resDistance').innerText = d.total_distance + ' km';
        document.getElementById('resTime').innerText = d.formatted_time;
        document.getElementById('resultCard').style.display = 'block';
    }
}

function saveToLocal(){ localStorage.setItem(CURRENT_USER_KEY, JSON.stringify({nodes, edges})); }
function loadFromLocal(){
    const d=JSON.parse(localStorage.getItem(CURRENT_USER_KEY));
    if(d){ nodes=d.nodes||{}; edges=d.edges||[]; for(let n in nodes) createMarker(n, nodes[n][0], nodes[n][1]); drawMapLines(); updateWizardUI(); }
}
function clearMapData(){ localStorage.removeItem(CURRENT_USER_KEY); location.reload(); }