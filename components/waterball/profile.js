/* Formal v1 still atlas. Geometry is derived from the locked 853x1844 layers. */
window.WATERBALL_PROFILE = {
  version: 'mindisle-water-orb-still-2p5d-v1',
  renderer: 'layered-reference-canvas',
  frame: [853, 1844],
  center: [426.5, 925],
  radius: 316,
  hitRadius: 300,
  // Shared field model for still and the later moving state. The center is
  // the dominant mass; the two visible points only perturb nearby volume.
  gravity: {
    center: {position: [0, 0], mass: 1.0},
    points: [
      {name: 'cool', position: [-0.40, 0.45], mass: 0.20},
      {name: 'warm', position: [0.50, -0.45], mass: 0.20}
    ]
  },
  assetRoot: 'assets/waterball-still-v1/',
  staticComposite: 'static_composite.png',
  manifest: 'assets/waterball-still-v1/manifest.json',
  // The still atlas is the visual authority for the body.  This is kept
  // separate from the geometry used for motion and hit testing so a future
  // orbit layer can leave the body without changing its silhouette.
  silhouetteAuthority: {
    type: 'atlas-alpha',
    layer: '01_outer_film',
    threshold: 6
  },
  bodyDomain: 'still-silhouette',
  orbitDomain: 'separate-attached-elements',
  layerOrder: [
    '00_background_plate',
    '01_outer_film',
    '02_internal_cyan_volume',
    '03_boundary_mask',
    '04_flow_layer',
    '05_flow_layer',
    '06_fine_ink_wash',
    '07_cool_point_core',
    '08_cool_point_glow',
    '09_warm_point_core',
    '10_warm_point_glow',
    '11_curvature_highlights'
  ],
  layers: {
    '00_background_plate': 'layers/00_background_plate.png',
    '01_outer_film': 'layers/01_outer_film.png',
    '02_internal_cyan_volume': 'layers/02_internal_cyan_volume.png',
    '03_boundary_mask': 'layers/03_boundary_mask.png',
    '04_flow_layer': 'layers/04_flow_layer.png',
    '05_flow_layer': 'layers/05_flow_layer.png',
    '06_fine_ink_wash': 'layers/06_fine_ink_wash.png',
    '07_cool_point_core': 'layers/07_cool_point_core.png',
    '08_cool_point_glow': 'layers/08_cool_point_glow.png',
    '09_warm_point_core': 'layers/09_warm_point_core.png',
    '10_warm_point_glow': 'layers/10_warm_point_glow.png',
    '11_curvature_highlights': 'layers/11_curvature_highlights.png'
  },
  dynamicLayers: new Set([
    '02_internal_cyan_volume', '03_boundary_mask', '04_flow_layer', '05_flow_layer', '06_fine_ink_wash', '11_curvature_highlights'
  ]),
  layerBounds: {
    '02_internal_cyan_volume': [149, 648, 555, 555],
    '03_boundary_mask': [154, 812, 547, 219],
    '04_flow_layer': [169, 727, 508, 270],
    '05_flow_layer': [169, 889, 514, 218],
    '06_fine_ink_wash': [152, 651, 550, 549],
    '11_curvature_highlights': [88, 586, 678, 679],
    '08_cool_point_glow': [262, 744, 75, 77],
    '10_warm_point_glow': [544, 1029, 79, 77]
  }
};
