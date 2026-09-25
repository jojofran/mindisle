"""Deterministic static pair. No image textures, keyframes or fallback renderer.
Blender -b --factory-startup --python scripts/build_waterball.py -- --state both
Use --preview for 45% / preview samples; --stage blockout omits films/nodes/flows.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import bpy
from mathutils import Vector
_SCRIPT_FILE = globals().get('__file__')
ROOT = Path(_SCRIPT_FILE).resolve().parents[1] if _SCRIPT_FILE else Path('/Users/fran/Documents/Code/mindisle/blender')
p = argparse.ArgumentParser()
p.add_argument('--state', choices=['still','moving','both'], default='both')
p.add_argument('--preview', action='store_true')
p.add_argument('--stage', choices=['blockout','films','complete'], default='complete')
p.add_argument('--output-dir', default=str(ROOT/'renders'))
p.add_argument('--no-render', action='store_true')
A = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
P = json.loads((ROOT/'waterball_static_parameters.json').read_text())
CY = -(P['camera']['center_from_top']-0.5)*P['camera']['ortho_scale']
OUT = Path(A.output_dir); OUT.mkdir(parents=True,exist_ok=True)

def node(mat,kind): return mat.node_tree.nodes.new(kind)
def link(mat,a,out,b,inp): mat.node_tree.links.new(a.outputs[out],b.inputs[inp])
def material(name):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.node_tree.nodes.clear()
    return m,node(m,'ShaderNodeOutputMaterial')
def mathnode(m,op,a=None,b=None):
    n=node(m,'ShaderNodeMath'); n.operation=op
    for i,v in enumerate((a,b)):
        if v is not None:
            if isinstance(v,(int,float)): n.inputs[i].default_value=v
            else: m.node_tree.links.new(v,n.inputs[i])
    return n.outputs[0]
def mesh_obj(scene,name,verts,faces,mat):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); scene.collection.objects.link(ob)
    for f in me.polygons: f.use_smooth=True
    if mat: me.materials.append(mat)
    return ob

def body_material(state):
    m,out=material('Water / clear surface + continuous absorption / '+state)
    g=node(m,'ShaderNodeBsdfGlass'); g.inputs['Color'].default_value=(0.97,0.995,1.0,1)
    g.inputs['Roughness'].default_value=P['body']['roughness']; g.inputs['IOR'].default_value=P['body']['ior']
    t=node(m,'ShaderNodeBsdfTransparent'); mix=node(m,'ShaderNodeMixShader')
    layer=node(m,'ShaderNodeLayerWeight'); ramp=node(m,'ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=0.04; ramp.color_ramp.elements[0].color=(0.76,0.76,0.76,1)
    ramp.color_ramp.elements[1].position=0.92; ramp.color_ramp.elements[1].color=(0.22,0.22,0.22,1)
    link(m,layer,'Facing',ramp,'Fac'); link(m,ramp,'Color',mix,0); link(m,t,0,mix,1); link(m,g,0,mix,2)
    # Broad Fresnel response supplies a continuous water edge without a
    # detached outline mesh or a fixed screen-space stroke.
    fres=node(m,'ShaderNodeFresnel'); fres.inputs['IOR'].default_value=P['body']['ior']
    edge=node(m,'ShaderNodeValToRGB'); edge.color_ramp.elements[0].position=0.18; edge.color_ramp.elements[0].color=(0.0,0.0,0.0,1)
    edge.color_ramp.elements[1].position=0.78; edge.color_ramp.elements[1].color=(0.46,0.74,0.70,1)
    link(m,fres,'Fac',edge,'Fac')
    em=node(m,'ShaderNodeEmission'); link(m,edge,'Color',em,'Color'); em.inputs['Strength'].default_value=0.42
    add=node(m,'ShaderNodeAddShader'); link(m,mix,0,add,0); link(m,em,0,add,1); link(m,add,0,out,'Surface')
    # Spatial absorption lives inside the single body. No enclosed inner ball.
    geo=node(m,'ShaderNodeTexCoord'); sep=node(m,'ShaderNodeSeparateXYZ'); link(m,geo,'Object',sep,0)
    sig=P['body']['core_sigma'][state]
    terms=[]
    for i in range(3):
        offsets=[0.10, -0.10, 0.04]
        shifted=mathnode(m,'ADD',sep.outputs[i],offsets[i])
        scaled=mathnode(m,'DIVIDE',shifted,sig[i]); terms.append(mathnode(m,'MULTIPLY',scaled,scaled))
    s=mathnode(m,'ADD',mathnode(m,'ADD',terms[0],terms[1]),terms[2])
    density=mathnode(m,'EXPONENT',mathnode(m,'MULTIPLY',s,-2.0))
    # Very low-frequency modulation keeps the center aqueous and irregular
    # instead of reading as a perfect radial lamp or a solid inner ball.
    noise=node(m,'ShaderNodeTexNoise'); noise.noise_dimensions='3D'; noise.inputs['Scale'].default_value=2.8
    noise.inputs['Detail'].default_value=2.0; noise.inputs['Roughness'].default_value=0.42
    link(m,geo,'Object',noise,'Vector')
    mod=mathnode(m,'MULTIPLY',noise.outputs['Fac'],0.16)
    mod=mathnode(m,'ADD',mod,0.92)
    density=mathnode(m,'MULTIPLY',density,mod)
    density=mathnode(m,'MULTIPLY',density,P['body']['core_density'][state])
    vol=node(m,'ShaderNodeVolumeAbsorption'); vol.inputs['Color'].default_value=(*P['body']['absorption_color'],1)
    m.node_tree.links.new(density,vol.inputs['Density']); link(m,vol,0,out,'Volume')
    return m

def film_material(name, color=(0.32,0.72,0.74), ior=None, opacity=None, emission_strength=0.72):
    m,out=material(name)
    # A controlled transparent/emissive optical layer keeps broad sheets
    # readable through the shell without producing a solid second sphere.
    tr=node(m,'ShaderNodeBsdfTransparent'); mix=node(m,'ShaderNodeMixShader')
    attr=node(m,'ShaderNodeAttribute'); attr.attribute_name='film_alpha'
    fade=mathnode(m,'MULTIPLY',attr.outputs['Fac'],min(0.92, (opacity or P['film']['opacity']) * 0.96))
    em=node(m,'ShaderNodeEmission'); em.inputs['Color'].default_value=(*color,1)
    em.inputs['Strength'].default_value=emission_strength
    m.node_tree.links.new(fade,mix.inputs[0]); link(m,tr,0,mix,1); link(m,em,0,mix,2); link(m,mix,0,out,'Surface')
    return m

def backdrop():
    m,out=material('Procedural pale cyan-white space; no image')
    tex=node(m,'ShaderNodeTexCoord'); noise=node(m,'ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=0.72
    noise.inputs['Detail'].default_value=1.4; noise.inputs['Roughness'].default_value=0.48
    link(m,tex,'Object',noise,'Vector')
    ramp=node(m,'ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=0.18
    ramp.color_ramp.elements[0].color=(0.88,0.94,0.96,1)
    ramp.color_ramp.elements[1].position=0.80; ramp.color_ramp.elements[1].color=(1.0,1.0,0.995,1)
    link(m,noise,'Fac',ramp,'Fac'); em=node(m,'ShaderNodeEmission'); em.inputs['Strength'].default_value=1.18
    link(m,ramp,'Color',em,'Color'); link(m,em,0,out,'Surface')
    return m

def body(scene,state):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=P['body']['subdivisions'],radius=1)
    ob=bpy.context.object; ob.name='Body / single closed continuous mesh / '+state
    for c in list(ob.users_collection): c.objects.unlink(ob)
    scene.collection.objects.link(ob); ob.location.y=CY
    ob.shape_key_add(name='Still'); shape=ob.shape_key_add(name='Moving frozen shape')
    d=P['body']['deform']
    for i,v in enumerate(ob.data.vertices):
        n=v.co.normalized(); x,y,z=n
        # Polynomial on the unit sphere: smooth everywhere, no angular seam/poles.
        delta=d['xxy']*(x*x-y*y)+d['xy']*2*x*y+d['xz']*x*z
        shape.data[i].co=v.co*(1+delta)
    shape.value=1 if state=='moving' else 0
    for face in ob.data.polygons: face.use_smooth=True
    ob.data.materials.append(body_material(state)); return ob

def alpha_attr(ob,vals):
    attr=ob.data.attributes.new('film_alpha','FLOAT','POINT')
    for i,v in enumerate(vals): attr.data[i].value=v

def internal_film(scene,state,index,mat):
    # Open crescent sheets, with a rolled section and unequal curvature.
    # These are inside the body, and are not screen-facing highlight outlines.
    config=[(142,333,0.69,0.29,0.15),(18,187,0.71,0.22,-0.22),(205,375,0.80,0.16,0.29)]
    start,end,radius,width,depth=config[index]
    verts=[]; faces=[]; alpha=[]; nu,nv=144,20
    for i in range(nu+1):
        t=i/nu; a=math.radians(start+(end-start)*t)
        taper=math.sin(math.pi*t)**0.65
        r=radius+0.075*math.sin(2*a+index)+ (0.035 if state=='moving' else 0)*math.sin(3*a+0.6)
        for j in range(nv+1):
            u=2*j/nv-1
            # Width turns into depth near the edge: a curled water sheet.
            roll=u*1.35+0.24*math.sin(3*a+index)
            rr=r+width*taper*math.sin(roll)
            x=rr*math.cos(a); y=rr*math.sin(a)*0.93
            z=depth+width*taper*(1-math.cos(roll))+0.12*math.sin(a*1.4+index)
            norm=math.sqrt(x*x+y*y+z*z)
            if norm>0.975: x*=0.975/norm; y*=0.975/norm; z*=0.975/norm
            verts.append((x,y+CY,z))
            edge=(1-abs(u)**8)**0.65
            alpha.append(taper*edge)
    for i in range(nu):
        for j in range(nv):
            k=i*(nv+1)+j; faces.append((k,k+1,k+nv+2,k+nv+1))
    ob=mesh_obj(scene,f'Open internal folded sheet {index+1} / {state}',verts,faces,mat); alpha_attr(ob,alpha)
    return ob

def bezier(ctrl,t):
    return (1-t)**3*Vector(ctrl[0])+3*(1-t)**2*t*Vector(ctrl[1])+3*(1-t)*t*t*Vector(ctrl[2])+t**3*Vector(ctrl[3])

def add_mesh_ribbon(name, points, widths, mat, curve_bias=0.0):
    verts=[]; faces=[]
    for i,point in enumerate(points):
        prev=Vector(points[max(0,i-1)]); nxt=Vector(points[min(len(points)-1,i+1)])
        tangent=(nxt-prev).normalized(); side=Vector((-tangent.y,tangent.x,0))
        if side.length<0.01: side=Vector((1,0,0))
        side.normalize(); c=Vector(point); c.z += curve_bias*math.sin(math.pi*i/max(1,len(points)-1)); w=widths[i]
        verts.extend([tuple(c+side*w),tuple(c-side*w)])
    for i in range(len(points)-1):
        k=2*i; faces.append((k,k+1,k+3,k+2))
    return mesh_obj(bpy.context.scene,name,verts,faces,mat)

def cross_membrane(scene, state, mat):
    # One broad S-shaped sheet supplies the reference's folded water mass.
    # It is an open surface, not a hard outline or a second enclosed sphere.
    pts = [(-0.92, 0.18, 0.10), (-0.78, 0.42, 0.12), (-0.55, 0.60, 0.15),
           (-0.26, 0.68, 0.19), (0.04, 0.53, 0.22), (0.28, 0.26, 0.22),
           (0.43, -0.02, 0.20), (0.50, -0.28, 0.19), (0.56, -0.46, 0.16),
           (0.70, -0.62, 0.14), (0.86, -0.72, 0.12)]
    if state == 'moving':
        pts = [(-0.88, 0.34, 0.12), (-0.74, 0.56, 0.16), (-0.60, 0.70, 0.18),
               (-0.38, 0.72, 0.21), (-0.15, 0.68, 0.24), (0.10, 0.52, 0.27),
               (0.28, 0.34, 0.29), (0.42, 0.10, 0.27), (0.50, -0.12, 0.25),
               (0.58, -0.36, 0.22), (0.64, -0.58, 0.20), (0.90, -0.82, 0.14)]
    widths = [0.02, 0.10, 0.18, 0.25, 0.30, 0.31, 0.28, 0.23, 0.15, 0.08, 0.04, 0.02]
    ob = add_mesh_ribbon('Broad diagonal folded water membrane / '+state, [(x,y+CY,z) for x,y,z in pts], widths, mat, 0.050 if state=='moving' else 0.038)
    alpha_attr(ob, [0.02, 0.28, 0.46, 0.60, 0.70, 0.74, 0.68, 0.58, 0.42, 0.24, 0.10, 0.02])
    return ob


def flow(scene,name,ctrl,mat):
    verts=[]; faces=[]; alphas=[]; nu,nv=192,20
    for i in range(nu+1):
        t=i/nu; c=bezier(ctrl,t); tangent=(bezier(ctrl,min(1,t+.001))-bezier(ctrl,max(0,t-.001))).normalized()
        side=Vector((-tangent.y,tangent.x,0)).normalized()
        width=0.102*math.sin(math.pi*t)**1.22*(0.62+0.38*math.sin(math.pi*t))
        for j in range(nv+1):
            u=2*j/nv-1; v=c+side*(u*width)
            v.z+=width*(0.75*u*u+0.36*math.sin(2*math.pi*t)*u)
            v.y+=CY; verts.append(tuple(v))
            alphas.append(math.sin(math.pi*t)**0.55*(1-abs(u)**6)**0.5)
    for i in range(nu):
        for j in range(nv):
            k=i*(nv+1)+j; faces.append((k,k+1,k+nv+2,k+nv+1))
    ob=mesh_obj(scene,name,verts,faces,mat); alpha_attr(ob,alphas)
    return ob

def bead(scene,name,pos,col):
    m,out=material(name+' wet glass')
    g=node(m,'ShaderNodeBsdfPrincipled'); g.inputs['Base Color'].default_value=(*col,1)
    g.inputs['Roughness'].default_value=0.1; g.inputs['IOR'].default_value=1.333
    g.inputs['Transmission Weight'].default_value=.65; link(m,g,0,out,'Surface')
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=P['nodes']['radius'])
    ob=bpy.context.object; ob.name=name
    for c in list(ob.users_collection): c.objects.unlink(ob)
    scene.collection.objects.link(ob); ob.location=(pos[0],pos[1]+CY,pos[2]); ob.data.materials.append(m)
    for face in ob.data.polygons: face.use_smooth=True
    return ob

def configure(scene):
    # Assign directly; fail loudly if Cycles is unavailable. No fallback.
    scene.render.engine='CYCLES'; scene.cycles.device=P['render']['device']
    scene.cycles.samples=P['render']['preview_samples'] if A.preview else P['render']['samples']
    scene.cycles.use_denoising=True; scene.cycles.seed=P['seed']; scene.cycles.use_animated_seed=False
    scene.cycles.max_bounces=18; scene.cycles.transmission_bounces=12; scene.cycles.transparent_max_bounces=24
    scene.cycles.volume_bounces=0; scene.cycles.sample_clamp_indirect=4
    scene.render.resolution_x=852; scene.render.resolution_y=1846; scene.render.resolution_percentage=45 if A.preview else 100
    scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'; scene.render.image_settings.color_depth='8'
    scene.view_settings.view_transform=P['render']['view_transform']; scene.view_settings.look=P['render']['look']; scene.view_settings.exposure=P['render']['exposure']
    scene.render.film_transparent=False
    scene['visual_state']=scene.name; scene['static_only']=True; scene['flow_time']=0.0; scene['seed']=P['seed']

# Clear all previous generated data so reruns cannot accumulate objects.
# Blender MCP blocks read_factory_settings; this equivalent empty startup is
# allowed in the connected instance and keeps reruns deterministic.
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
bpy.context.preferences.filepaths.save_version=0
base=bpy.context.scene; base.name='still'; configure(base)
world=bpy.data.worlds.new('Shared pale studio'); world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(0.96,0.985,0.99,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.48; base.world=world
cam_data=bpy.data.cameras.new('Shared orthographic camera'); cam_data.type='ORTHO'; cam_data.ortho_scale=P['camera']['ortho_scale']
cam=bpy.data.objects.new('Shared orthographic camera',cam_data); base.collection.objects.link(cam); cam.location=P['camera']['position']; base.camera=cam
bg=mesh_obj(base,'Shared procedural background',[(-10,-10,-2.3),(10,-10,-2.3),(10,10,-2.3),(-10,10,-2.3)],[(0,1,2,3)],backdrop())
shared=[cam,bg]
for spec in P['lights']:
    data=bpy.data.lights.new(spec['name'],'AREA'); data.shape='RECTANGLE'; data.energy=spec['energy']; data.size,data.size_y=spec['size']; data.color=spec['color']
    ob=bpy.data.objects.new(spec['name'],data); base.collection.objects.link(ob); ob.location=spec['location']; ob.rotation_euler=(Vector(spec['target'])-ob.location).to_track_quat('-Z','Y').to_euler(); shared.append(ob)
    film_cool=film_material('Internal cool water membrane',(0.12,0.48,0.52),opacity=0.66,emission_strength=0.42)
    film_pale=film_material('Internal pale refractive membrane',(0.52,0.82,0.84),opacity=0.58,emission_strength=0.28)
    film_warm=film_material('Internal restrained warm trace',(0.82,0.48,0.30),opacity=0.42,emission_strength=0.22)
    flow_mat=film_material('External open water sheets',(0.18,0.52,0.58),1.333,0.42,0.22)
metrics={}
for state in ['still','moving']:
    scene=base if state=='still' else bpy.data.scenes.new('moving')
    if state=='moving':
        configure(scene); scene.world=world; scene.camera=cam
        for ob in shared: scene.collection.objects.link(ob)
    shell=body(scene,state)
    if A.stage!='blockout':
        for i,mat in enumerate((film_cool,film_pale,film_warm)): internal_film(scene,state,i,mat)
        cross_membrane(scene,state,film_cool)
    if A.stage=='complete':
        if state=='still':
            for i,pos in enumerate(P['nodes']['still']): bead(scene,['Cool suspended node','Warm suspended node'][i],pos,P['nodes'][['cool','warm'][i]])
        else:
            for i,key in enumerate(['upper','lower']):
                ctrl=P['flows'][key]; flow(scene,'Open flow '+key,ctrl,flow_mat)
                bead(scene,'Released node '+key,ctrl[0],P['nodes'][['cool','warm'][i]])
    topo=hashlib.sha256(str([tuple(p.vertices) for p in shell.data.polygons]).encode()).hexdigest()
    metrics[state]={'engine_actual':scene.render.engine,'samples':scene.cycles.samples,'body_vertices':len(shell.data.vertices),'body_faces':len(shell.data.polygons),'topology_sha256':topo,'camera_name':scene.camera.name,'world_name':scene.world.name,'object_count':len(scene.objects),'node_radius_R':P['nodes']['radius'],'animation_data_count':sum(bool(o.animation_data) for o in scene.objects)}
    scene.render.filepath=str(OUT/(state+'.png'))
# Open into a useful camera view and make both scene presets easy to find.
bpy.context.window.scene=base
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'
blend=ROOT/('waterball_static_preview.blend' if A.preview else 'waterball_static_pair.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for state in (['still','moving'] if A.state=='both' else [A.state]):
    scene=bpy.data.scenes[state]; bpy.context.window.scene=scene
    if not A.no_render:
        start=time.time(); bpy.ops.render.render(write_still=True,scene=state); metrics[state]['render_seconds']=time.time()-start
        print('MINDISLE_RENDER '+json.dumps(metrics[state]))
(OUT/'render_manifest.json').write_text(json.dumps({'blender':bpy.app.version_string,'stage':A.stage,'preview':A.preview,'parameters':P,'states':metrics},indent=2))
