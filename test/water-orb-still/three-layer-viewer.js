import * as THREE from 'three';

const ROOT = './2p5d-composite-v1/';
const LAYERS = [
  ['00_background_plate', 'layers/00_background_plate.png'],
  ['01_outer_film', 'layers/01_outer_film.png'],
  ['02_internal_cyan_volume', 'layers/02_internal_cyan_volume.png'],
  ['03_boundary_mask', 'layers/03_boundary_mask.png'],
  ['04_flow_primary', 'layers/04_flow_layer.png'],
  ['05_flow_secondary', 'layers/05_flow_layer.png'],
  ['06_fine_ink_wash', 'layers/06_fine_ink_wash.png'],
  ['07_cool_point_core', 'layers/07_cool_point_core.png'],
  ['08_cool_point_glow', 'layers/08_cool_point_glow.png'],
  ['09_warm_point_core', 'layers/09_warm_point_core.png'],
  ['10_warm_point_glow', 'layers/10_warm_point_glow.png'],
  ['11_curvature_highlights', 'layers/11_curvature_highlights.png'],
];
const frame = { width: 853, height: 1844 };
const sphere = { center: [426.5, 925], radius: 316 };

const stage = document.querySelector('#stage');
const status = document.querySelector('#status');
const hit = document.querySelector('#orbHit');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, premultipliedAlpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x000000, 0);
stage.prepend(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(0, frame.width, 0, frame.height, -10, 10);
camera.position.z = 5;
const group = new THREE.Group();
scene.add(group);
const loader = new THREE.TextureLoader();
const entries = [];

function fit() {
  const rect = stage.getBoundingClientRect();
  renderer.setSize(rect.width, rect.height, false);
  const scale = Math.min(rect.width / frame.width, rect.height / frame.height);
  const left = (rect.width - frame.width * scale) / 2;
  const top = (rect.height - frame.height * scale) / 2;
  hit.style.left = `${left + (sphere.center[0] - sphere.radius) * scale}px`;
  hit.style.top = `${top + (sphere.center[1] - sphere.radius) * scale}px`;
  hit.style.width = `${sphere.radius * 2 * scale}px`;
  hit.style.height = `${sphere.radius * 2 * scale}px`;
  return { rect, scale, left, top };
}

function plane() {
  const geometry = new THREE.PlaneGeometry(frame.width, frame.height);
  geometry.translate(frame.width / 2, frame.height / 2, 0);
  return geometry;
}

async function loadLayer([name, path], z) {
  const texture = await loader.loadAsync(ROOT + path);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthWrite: false, depthTest: false });
  const mesh = new THREE.Mesh(plane(), material);
  mesh.position.z = z;
  mesh.name = name;
  group.add(mesh);
  entries.push({ name, mesh, texture });
}

function inspect() {
  return {
    renderer: 'three-layer-composite',
    state: 'still',
    ready: entries.length === LAYERS.length,
    interactive: entries.length === LAYERS.length,
    frame,
    sphere: { center: [...sphere.center], radius: sphere.radius },
    layers: entries.map(({ name }) => name),
    moving: false,
  };
}

async function main() {
  fit();
  await Promise.all(LAYERS.map((entry, index) => loadLayer(entry, index)));
  fit();
  status.textContent = `still · ${entries.length} layers · ${frame.width}×${frame.height}`;
  window.waterOrbViewer = { inspect, renderer, scene, camera, layers: entries };
  renderer.setAnimationLoop(() => renderer.render(scene, camera));
}

window.addEventListener('resize', fit);
hit.addEventListener('click', () => {
  status.textContent = 'still · hit';
  window.dispatchEvent(new CustomEvent('water-orb-hit', { detail: inspect() }));
});

main().catch(error => {
  status.textContent = `error · ${error.message}`;
  console.error(error);
});
