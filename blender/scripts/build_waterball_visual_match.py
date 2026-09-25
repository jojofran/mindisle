"""Fixed-camera procedural optical water. No source images, fluid bake or animation.
Logical layers: projected cyan depth, warped caustics, continuous shell, compositor.
All optical masks are live shader math; same local coordinates deform with the body.
"""
import bpy, math, json, sys, argparse, hashlib, time
from pathlib import Path
from mathutils import Vector
_SCRIPT_FILE = globals().get('__file__')
if _SCRIPT_FILE:
    ROOT = Path(_SCRIPT_FILE).resolve().parents[1]
else:
    # Blender's interactive console does not populate __file__.  Keep the
    # project-local fallback so the same script can be executed with exec().
    ROOT = Path('/Users/fran/Documents/Code/mindisle/blender')
p=argparse.ArgumentParser(); p.add_argument('--preview',action='store_true'); p.add_argument('--state',default='both',choices=['still','moving','both']); p.add_argument('--pass',dest='pass_name',default='C',choices=['A','B','C']); p.add_argument('--output-dir',default=str(ROOT/'renders/visual-match')); p.add_argument('--no-render',action='store_true')
A=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
P=json.loads((ROOT/'waterball_visual_parameters.json').read_text()); OUT=Path(A.output_dir); OUT.mkdir(parents=True,exist_ok=True)
CY=-(P['camera']['center_from_top']-.5)*P['camera']['ortho_scale']

class Graph:
    def __init__(self,name):
        self.mat=bpy.data.materials.new(name); self.mat.use_nodes=True; self.nt=self.mat.node_tree; self.nt.nodes.clear(); self.out=self.node('ShaderNodeOutputMaterial')
    def node(self,kind,label=None):
        v=self.nt.nodes.new(kind)
        if label: v.label=label; v.name=label
        return v
    def feed(self,value,socket):
        if isinstance(value,bpy.types.NodeSocket): self.nt.links.new(value,socket)
        else: socket.default_value=value
    def op(self,op,a,b=None,c=None):
        v=self.node('ShaderNodeMath'); v.operation=op
        for i,x in enumerate((a,b,c)):
            if x is not None:self.feed(x,v.inputs[i])
        return v.outputs[0]
    def vec(self,x,y,z=0):
        v=self.node('ShaderNodeCombineXYZ')
        for i,x in enumerate((x,y,z)):self.feed(x,v.inputs[i])
        return v.outputs[0]
    def ramp(self,x,stops,label=''):
        v=self.node('ShaderNodeValToRGB',label); self.feed(x,v.inputs[0]); r=v.color_ramp; r.interpolation='EASE'
        for i,(pos,col) in enumerate(stops):
            e=r.elements[i] if i<2 else r.elements.new(pos); e.position=pos; e.color=(*col,1) if len(col)==3 else col
        return v.outputs['Color']
    def mix(self,f,a,b):
        v=self.node('ShaderNodeMixRGB'); v.blend_type='MIX'; self.feed(f,v.inputs[0]); self.feed(a,v.inputs[1]); self.feed(b,v.inputs[2]); return v.outputs[0]
    def noise(self,v,scale,detail=2,rough=.6):
        n=self.node('ShaderNodeTexNoise'); n.inputs['Scale'].default_value=scale; n.inputs['Detail'].default_value=detail; n.inputs['Roughness'].default_value=rough; self.feed(v,n.inputs['Vector']); return n.outputs['Fac']
    def smooth(self,x,a,b): return self.ramp(x,[(a,(0,0,0)),(b,(1,1,1))])
    def gauss(self,x,width):return self.op('EXPONENT',self.op('MULTIPLY',self.op('POWER',self.op('DIVIDE',x,width),2),-1))
    def emission(self,color):
        e=self.node('ShaderNodeEmission'); self.feed(color,e.inputs['Color']); self.nt.links.new(e.outputs[0],self.out.inputs['Surface'])
        return e
    def layout(self):
        # Deterministic readable columns (data is also rebuilt from this file).
        for i,n in enumerate(self.nt.nodes): n.location=((i//12)*210,-(i%12)*160)


def background():
    g=Graph('Background | pale cyan spatial field'); tc=g.node('ShaderNodeTexCoord'); v=tc.outputs['Object']; noise=g.noise(v,.7,3)
    c=g.ramp(noise,[(.18,(.68,.79,.82)),(.82,(.97,.985,.98))],'Soft spatial variation')
    g.emission(c);g.layout();return g.mat


def optical(state):
    g=Graph('Water optical layers | '+state); op=g.op
    tc=g.node('ShaderNodeTexCoord'); sep=g.node('ShaderNodeSeparateXYZ'); g.feed(tc.outputs['Object'],sep.inputs[0]); x,y,z=[sep.outputs[s] for s in 'XYZ']
    # Local undeformed XYZ: continuous at poles and follows the deformed mesh.
    v=tc.outputs['Object']; low=g.noise(v,2.6,3); fine=g.noise(v,24,2,.62)
    rr=op('SQRT',op('ADD',op('MULTIPLY',x,x),op('MULTIPLY',y,y)))
    theta=op('ARCTAN2',y,x)
    # Core projected thickness: an S-warped elliptical falloff, no enclosed inner ball.
    sx=op('ADD',x,op('MULTIPLY',op('SINE',op('MULTIPLY',y,2.6)),.10))
    sx=op('ADD',sx,.07); yy=op('SUBTRACT',y,.015)
    er=op('SQRT',op('ADD',op('POWER',op('DIVIDE',sx,.80),2),op('POWER',op('DIVIDE',yy,.76),2)))
    core=g.ramp(er,[(.04,(1,1,1)),(.55,(.9,.9,.9)),(1.26,(0,0,0))],'Core soft thickness')
    density=P['optics']['core_density'][state]; core=op('MULTIPLY',core,density)
    # Keep the base nearly clear; low-frequency noise is a tint, not opacity.
    base=g.mix(.28,(.42,.70,.72,1),(.12,.40,.44,1))
    cyan=g.mix(fine,tuple(P['optics']['core_dark'])+(1,),tuple(P['optics']['core_light'])+(1,))
    # Core is thickness/alpha only; never use it as a cloudy color mask.
    col=g.mix(.12,base,cyan)
    if A.pass_name!='A':
        # Polar domain stretched radially, warped by low-frequency noise.
        # These masks modulate optical brightness, not geometry strips.
        wx=op('ADD',op('MULTIPLY',theta,1.7),op('MULTIPLY',rr,3.8))
        wy=op('ADD',op('MULTIPLY',rr,7.5),op('MULTIPLY',low,1.0))
        w=g.vec(wx,wy,op('MULTIPLY',z,.4))
        wav=g.noise(w,2.6,3.2,.68)
        # Two warped bands replace cloud blobs: one broad water fold and one
        # finer refractive line. Both are brightness/normal drivers only.
        wave1=g.node('ShaderNodeTexWave','Broad warped flow band'); wave1.wave_type='BANDS'; wave1.bands_direction='X'; wave1.inputs['Scale'].default_value=2.1; wave1.inputs['Distortion'].default_value=6.8; wave1.inputs['Detail'].default_value=5.0; wave1.inputs['Detail Scale'].default_value=2.0; g.feed(w,wave1.inputs['Vector'])
        band1=g.ramp(wave1.outputs['Color'],[(.30,(0,0,0)),(.47,(.92,.92,.92)),(.64,(0,0,0))],'Broad continuous water band')
        wave2=g.node('ShaderNodeTexWave','Fine warped refractive band'); wave2.wave_type='BANDS'; wave2.bands_direction='X'; wave2.inputs['Scale'].default_value=4.4; wave2.inputs['Distortion'].default_value=5.0; wave2.inputs['Detail'].default_value=4.0; wave2.inputs['Detail Scale'].default_value=2.5; g.feed(w,wave2.inputs['Vector'])
        band2=g.ramp(wave2.outputs['Color'],[(.39,(0,0,0)),(.51,(.75,.75,.75)),(.60,(0,0,0))],'Fine continuous water band')
        ann=g.ramp(er,[(.45,(0,0,0)),(.82,(.9,.9,.9)),(1.3,(1,1,1)),(1.85,(0,0,0))],'Broad water-layer region')
        # Voronoi cell edges with domain warp create refractive multi-scale flecks.
        vor=g.node('ShaderNodeTexVoronoi','Caustic network'); vor.feature='DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value=5.2; g.feed(w,vor.inputs['Vector'])
        veins=g.ramp(vor.outputs['Distance'],[(.018,(1,1,1)),(.095,(0,0,0))],'Thin caustic edges')
        broad=g.ramp(wav,[(.30,(0,0,0)),(.54,(.58,.58,.58)),(.70,(1,1,1))],'Soft refractive faces')
        water=op('MULTIPLY',ann,op('ADD',op('MULTIPLY',band1,.72),op('ADD',op('MULTIPLY',band2,.32),op('MULTIPLY',veins,.10))))
        col=g.mix(water,col,(.56,.86,.87,1))
        shade=op('MULTIPLY',ann,op('MULTIPLY',g.smooth(wav,.25,.45),.035))
        col=g.mix(shade,col,(.22,.45,.48,1))
        # Vertical S interface, soft and irregular; not a luminous white line.
        path=op('ADD',.23,op('MULTIPLY',op('SINE',op('ADD',op('MULTIPLY',y,3.0),.1)),-.40))
        dist=op('SUBTRACT',x,path); swarp=op('ADD',dist,op('MULTIPLY',op('SUBTRACT',low,.5),.09))
        smask=op('MULTIPLY',g.gauss(swarp,.045),g.smooth(op('SUBTRACT',1,rr),.06,.26))
        # S is a local optical boundary: it contributes to bump and a small
        # brightness lift, never a visible white stripe.
        s_bump=op('MULTIPLY',smask,.80)
        water=op('ADD',water,s_bump)
        col=g.mix(op('MULTIPLY',smask,.16),col,(.45,.72,.74,1))
    if A.pass_name=='C':
        # Analytic optical thickness on the real sphere; anisotropic light sectors.
        norm=g.node('ShaderNodeNewGeometry'); ns=g.node('ShaderNodeSeparateXYZ');g.feed(norm.outputs['Normal'],ns.inputs[0]); face=op('ABSOLUTE',ns.outputs['Z'])
        edge=g.gauss(op('SUBTRACT',face,.13),.10)
        light=op('ADD',.5,op('MULTIPLY',op('SINE',op('ADD',op('MULTIPLY',theta,2),.8)),.5))
        # Keep the silhouette optically continuous.  The previous narrow
        # normal-response stripe read as a manufactured white ring rather
        # than a thin water membrane, so use only a broad, low-amplitude
        # edge absorption response here.
        edge_tint=op('MULTIPLY',edge,op('ADD',.10,op('MULTIPLY',light,.18)))
        col=g.mix(edge_tint,col,(.16,.38,.40,1))
        lw=g.node('ShaderNodeLayerWeight','Irregular shell rim'); rimfac=lw.outputs['Facing']; rimnoise=g.noise(v,2.2,3,.68); rimnoise=g.smooth(rimnoise,.42,.70); rim=op('MULTIPLY',op('POWER',op('SUBTRACT',1,rimfac),2.2),rimnoise)
        col=g.mix(rim,col,(.93,1.0,.98,1))
        # Broad broken highlights in outer shell, warm on upper right/lower left.
        radius=op('ADD',.88,op('MULTIPLY',op('SUBTRACT',wav,.5),.08))
        arc=g.gauss(op('SUBTRACT',rr,radius),.045)
        sectors=op('POWER',op('ABSOLUTE',op('SINE',op('ADD',theta,.55))),5)
        # Broken glints are broad and translucent; they never form a closed
        # white stripe and stay close to the shell's pale cyan value.
        col=g.mix(op('MULTIPLY',arc,op('MULTIPLY',sectors,.22)),col,(.76,.93,.90,1))
    # Emission is only a restrained optical lift.  Transmission and Fresnel
    # carry the body; high emission would flatten the internal depth.
    e=g.emission(col); e.inputs['Strength'].default_value=.055
    # A modest real refraction component, bounded to avoid a second glass marble.
    if A.pass_name=='C':
        glass=g.node('ShaderNodeBsdfGlass','Small true refraction contribution');glass.inputs['IOR'].default_value=P['optics']['ior'];glass.inputs['Roughness'].default_value=.045
        bump=g.node('ShaderNodeBump');g.feed(water if A.pass_name!='A' else low,bump.inputs['Height']);bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.018;g.feed(bump.outputs[0],glass.inputs['Normal'])
        glass.inputs['Color'].default_value=(.62,.86,.86,1)
        tr=g.node('ShaderNodeBsdfTransparent');pr=g.node('ShaderNodeBsdfPrincipled','Clear water base');pr.inputs['Roughness'].default_value=.09;pr.inputs['IOR'].default_value=P['optics']['ior'];pr.inputs['Transmission Weight'].default_value=.58;g.feed(col,pr.inputs['Base Color'])
        alpha=op('ADD',.10,op('MULTIPLY',core,.16));mix=g.node('ShaderNodeMixShader');g.feed(alpha,mix.inputs[0]);g.feed(tr.outputs[0],mix.inputs[1]);g.feed(pr.outputs[0],mix.inputs[2])
        add=g.node('ShaderNodeAddShader');g.feed(mix.outputs[0],add.inputs[0]);g.feed(e.outputs[0],add.inputs[1]);g.feed(add.outputs[0],g.out.inputs['Surface'])
    g.layout();return g.mat


def flow_material():
    g=Graph('Open flow | warped refractive mask');uv=g.node('ShaderNodeTexCoord');sep=g.node('ShaderNodeSeparateXYZ');g.feed(uv.outputs['UV'],sep.inputs[0]);t=sep.outputs['X'];u=sep.outputs['Y'];op=g.op
    wave=op('SINE',op('ADD',op('MULTIPLY',t,15),op('MULTIPLY',u,4)))
    v=g.vec(op('MULTIPLY',t,2),op('ADD',op('MULTIPLY',u,5),op('MULTIPLY',wave,.7)),0)
    pat=g.noise(v,3,3)
    alpha=g.node('ShaderNodeAttribute');alpha.attribute_name='flow_alpha'
    col=g.mix(pat,(.27,.51,.56,1),(.87,1.01,1.02,1)); e=g.node('ShaderNodeEmission');g.feed(col,e.inputs['Color'])
    tr=g.node('ShaderNodeBsdfTransparent');mix=g.node('ShaderNodeMixShader');g.feed(op('MULTIPLY',alpha.outputs['Fac'],.56),mix.inputs[0]);g.feed(tr.outputs[0],mix.inputs[1]);g.feed(e.outputs[0],mix.inputs[2]);g.feed(mix.outputs[0],g.out.inputs['Surface']);g.layout();return g.mat


def mesh(scene,name,verts,faces,m):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
    for f in me.polygons:f.use_smooth=True
    me.materials.append(m);return ob


def make_body(scene,state):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6,radius=1)
    ob=bpy.context.object;ob.name='Water body | '+state
    for c in list(ob.users_collection):c.objects.unlink(ob)
    scene.collection.objects.link(ob);ob.location.y=CY
    for f in ob.data.polygons:f.use_smooth=True
    ob.shape_key_add(name='still');key=ob.shape_key_add(name='moving frozen');
    for v in ob.data.vertices:
        x,y,z=v.co;key.data[v.index].co=v.co*(1+.047*(x*x-y*y)+.055*2*x*y+.015*x*z)
    key.value=1 if state=='moving' else 0
    ob.data.materials.append(optical(state));return ob


def bez(c,t):return (1-t)**3*Vector(c[0])+3*(1-t)**2*t*Vector(c[1])+3*(1-t)*t*t*Vector(c[2])+t**3*Vector(c[3])
def make_flow(scene,name,ctrl,m):
    nu,nv=180,24;verts=[];faces=[];alphas=[];uvs=[]
    for i in range(nu+1):
        t=i/nu;c=bez(ctrl,t);tan=(bez(ctrl,min(1,t+.001))-bez(ctrl,max(0,t-.001))).normalized();side=Vector((-tan.y,tan.x,0));width=.09*math.sin(math.pi*t)**1.2
        for j in range(nv+1):
            u=j/nv*2-1;q=c+side*width*u;q.z+=width*u*u*.8;verts.append((q.x,q.y+CY,q.z));uvs.append((t,j/nv));alphas.append(math.sin(math.pi*t)**.5*(1-abs(u)**10)**.5)
    for i in range(nu):
        for j in range(nv):
            k=i*(nv+1)+j;faces.append((k,k+1,k+nv+2,k+nv+1))
    ob=mesh(scene,name,verts,faces,m);a=ob.data.attributes.new('flow_alpha','FLOAT','POINT')
    for i,v in enumerate(alphas):a.data[i].value=v
    uv=ob.data.uv_layers.new(name='Flow coordinates')
    for l in ob.data.loops:uv.data[l.index].uv=uvs[l.vertex_index]
    return ob


def bead(scene,name,p,warm=False):
    g=Graph(name+' optical point');tc=g.node('ShaderNodeTexCoord');sep=g.node('ShaderNodeSeparateXYZ');g.feed(tc.outputs['Generated'],sep.inputs[0]);c=g.ramp(sep.outputs['Z'],[(0,(.12,.36,.4)),(.68,(.5,.76,.77)),(1,(1.9,1.9,1.7))]);
    if warm:c=g.mix(.66,c,(1.0,.70,.46,1))
    g.emission(c);g.layout()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.025);ob=bpy.context.object;ob.name=name
    for c in list(ob.users_collection):c.objects.unlink(ob)
    scene.collection.objects.link(ob);ob.location=(p[0],p[1]+CY,p[2]);ob.data.materials.append(g.mat)
    for f in ob.data.polygons:f.use_smooth=True


def compositor(scene):
    # Blender 5 compositor uses a node group attached to Scene.
    nt=bpy.data.node_groups.new('Soft highlights | '+scene.name,'CompositorNodeTree');scene.compositing_node_group=nt
    nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    rl=nt.nodes.new('CompositorNodeRLayers');rl.scene=scene
    glare=nt.nodes.new('CompositorNodeGlare');go=nt.nodes.new('NodeGroupOutput')
    # Input sockets are inspected from the live API, with defaults left where unavailable.
    for key,val in [('Threshold',1.05),('Strength',.10),('Size',.23)]:
        if key in glare.inputs:glare.inputs[key].default_value=val
    nt.links.new(rl.outputs['Image'],glare.inputs['Image']);nt.links.new(glare.outputs['Image'],go.inputs['Image'])


def configure(scene):
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24 if A.preview else 128;scene.cycles.use_denoising=True;scene.cycles.seed=2718;scene.cycles.use_animated_seed=False
    scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8;scene.cycles.transparent_max_bounces=12
    scene.render.resolution_x=852;scene.render.resolution_y=1846;scene.render.resolution_percentage=45 if A.preview else 100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    scene['visual_state']=scene.name;scene['static_only']=True;scene['flow_time']=0.;scene['pass']=A.pass_name
    if A.pass_name=='C':compositor(scene)

# Do not call read_homefile(factory_startup=True) here.  Blender 5.2.2 on
# macOS can crash while re-detecting the Metal backend from an in-process
# console.  An explicit datablock cleanup gives the same deterministic,
# non-accumulating rebuild without reopening the home file.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                   bpy.data.cameras, bpy.data.lights, bpy.data.worlds,
                   bpy.data.node_groups):
    for datablock in list(collection):
        if datablock.users == 0:
            collection.remove(datablock)
bpy.context.preferences.filepaths.save_version=0
base=bpy.context.scene;base.name='still';configure(base)
world=bpy.data.worlds.new('Shared pale studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.9,.92,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;base.world=world
camd=bpy.data.cameras.new('Shared orthographic camera');camd.type='ORTHO';camd.ortho_scale=P['camera']['ortho_scale'];cam=bpy.data.objects.new(camd.name,camd);base.collection.objects.link(cam);cam.location=(0,0,8);base.camera=cam
bg=mesh(base,'Shared procedural background',[(-10,-10,-2),(10,-10,-2),(10,10,-2),(-10,10,-2)],[(0,1,2,3)],background());shared=[cam,bg];flowmat=flow_material();metrics={}
for state in ('still','moving'):
    scene=base if state=='still' else bpy.data.scenes.new('moving');bpy.context.window.scene=scene
    if state=='moving':
        configure(scene);scene.world=world;scene.camera=cam
        for ob in shared:scene.collection.objects.link(ob)
    body=make_body(scene,state)
    if state=='still':
        bead(scene,'Cool suspended point',(-.34,.48,.92));bead(scene,'Warm suspended point',(.46,-.47,.80),True)
    else:
        for key in ('upper','lower'):
            ctrl=P['flows'][key];make_flow(scene,'Open flow '+key,ctrl,flowmat);bead(scene,'Released point '+key,ctrl[0],key=='lower')
    metrics[state]={'engine_actual':scene.render.engine,'device':scene.cycles.device,'samples':scene.cycles.samples,'denoise':True,'view_transform':scene.view_settings.view_transform,'exposure':0,'body_vertices':len(body.data.vertices),'body_faces':len(body.data.polygons),'topology_sha256':hashlib.sha256(str([tuple(f.vertices) for f in body.data.polygons]).encode()).hexdigest(),'animation_data_count':sum(bool(o.animation_data) for o in scene.objects),'object_count':len(scene.objects),'image_textures':sum(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)}
    scene.render.filepath=str(OUT/(state+'.png'))
bpy.context.window.scene=base
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'waterball_visual_match.blend'))
for state in (('still','moving') if A.state=='both' else (A.state,)):
    if not A.no_render:
        t=time.time();bpy.context.window.scene=bpy.data.scenes[state];bpy.ops.render.render(write_still=True,scene=state);metrics[state]['seconds']=time.time()-t
(OUT/'render_manifest.json').write_text(json.dumps({'blender':bpy.app.version_string,'pass':A.pass_name,'preview':A.preview,'parameters':P,'states':metrics},indent=2))
print(json.dumps(metrics))
