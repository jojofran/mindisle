import bpy, math, os, json, shutil
from mathutils import Vector

ROOT='/Users/fran/Documents/Code/mindisle'; OUT=os.path.join(ROOT,'image2blender-runs','water-orb'); RD=os.path.join(OUT,'renders_2p5d'); os.makedirs(RD,exist_ok=True)
W,H=640,1384; CAM_SCALE=7.65; ASPECT=W/H
SCENE=None; COLL=None

def set_input(node,val,*names):
    for n in names:
        if n in node.inputs: node.inputs[n].default_value=val; return
def surf(m):
    if hasattr(m,'surface_render_method'): m.surface_render_method='BLENDED'
def clear_scene():
    global SCENE,COLL
    old=bpy.data.scenes.get('water_orb_2p5d')
    if old: bpy.data.scenes.remove(old)
    SCENE=bpy.data.scenes.new('water_orb_2p5d'); COLL=SCENE.collection
    for w in bpy.context.window_manager.windows: w.scene=SCENE
def look_at(o,t=(0,0,0)): o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()

def radial_material(name, stops, strength=1.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; surf(m); nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); em=nt.nodes.new('ShaderNodeEmission'); tc=nt.nodes.new('ShaderNodeTexCoord'); sep=nt.nodes.new('ShaderNodeSeparateXYZ')
    subx=nt.nodes.new('ShaderNodeMath'); subx.operation='SUBTRACT'; subx.inputs[1].default_value=.5
    suby=nt.nodes.new('ShaderNodeMath'); suby.operation='SUBTRACT'; suby.inputs[1].default_value=.5
    sx=nt.nodes.new('ShaderNodeMath'); sx.operation='MULTIPLY'; sy=nt.nodes.new('ShaderNodeMath'); sy.operation='MULTIPLY'
    add=nt.nodes.new('ShaderNodeMath'); add.operation='ADD'; root=nt.nodes.new('ShaderNodeMath'); root.operation='SQRT'
    ramp=nt.nodes.new('ShaderNodeValToRGB')
    cr=ramp.color_ramp; cr.interpolation='EASE'; cr.elements.remove(cr.elements[1]);
    for i,(pos,col) in enumerate(stops):
        e=cr.elements[0] if i==0 else cr.elements.new(pos); e.position=pos; e.color=(*col,1)
    nt.links.new(tc.outputs['Generated'],sep.inputs[0]); nt.links.new(sep.outputs['X'],subx.inputs[0]); nt.links.new(sep.outputs['Y'],suby.inputs[0]); nt.links.new(subx.outputs[0],sx.inputs[0]); nt.links.new(subx.outputs[0],sx.inputs[1]); nt.links.new(suby.outputs[0],sy.inputs[0]); nt.links.new(suby.outputs[0],sy.inputs[1]); nt.links.new(sx.outputs[0],add.inputs[0]); nt.links.new(sy.outputs[0],add.inputs[1]); nt.links.new(add.outputs[0],root.inputs[0]); nt.links.new(root.outputs[0],ramp.inputs[0]); nt.links.new(ramp.outputs['Color'],em.inputs['Color']); set_input(em,strength,'Strength'); nt.links.new(em.outputs[0],out.inputs[0])
    return m
def flat_material(name,color,alpha=1.0,strength=1.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; surf(m); nt=m.node_tree; nt.nodes.clear(); out=nt.nodes.new('ShaderNodeOutputMaterial'); bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); set_input(bs,(*color,1),'Base Color'); set_input(bs,alpha,'Alpha'); set_input(bs,(*color,1),'Emission Color','Emission'); set_input(bs,strength,'Emission Strength'); set_input(bs,.22,'Roughness'); nt.links.new(bs.outputs[0],out.inputs[0]); return m
def spherical_material(name, stops, strength=1.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear(); out=nt.nodes.new('ShaderNodeOutputMaterial'); em=nt.nodes.new('ShaderNodeEmission'); lw=nt.nodes.new('ShaderNodeLayerWeight'); ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation='EASE'; ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i,(pos,col) in enumerate(stops):
        e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos); e.position=pos; e.color=(*col,1)
    nt.links.new(lw.outputs['Facing'],ramp.inputs[0])
    tc=nt.nodes.new('ShaderNodeTexCoord'); noise=nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=2.0; noise.inputs['Detail'].default_value=5.0; noise.inputs['Roughness'].default_value=.72
    nr=nt.nodes.new('ShaderNodeValToRGB'); nr.color_ramp.elements[0].color=(.66,.88,.90,1); nr.color_ramp.elements[1].color=(1.0,1.0,1.0,1)
    mix=nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=.28
    nt.links.new(tc.outputs['Generated'],noise.inputs['Vector']); nt.links.new(noise.outputs['Fac'],nr.inputs[0]); nt.links.new(ramp.outputs['Color'],mix.inputs[1]); nt.links.new(nr.outputs['Color'],mix.inputs[2]); nt.links.new(mix.outputs[0],em.inputs['Color']); set_input(em,strength,'Strength'); nt.links.new(em.outputs[0],out.inputs[0]); return m
def add_plane(name,size,z,mat):
    bpy.ops.mesh.primitive_plane_add(size=size,location=(0,0,z)); o=bpy.context.object; o.name=name; o.data.materials.append(mat); [c.objects.unlink(o) for c in list(o.users_collection)]; COLL.objects.link(o); return o
def add_uv(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); bpy.ops.object.shade_smooth(); o.data.materials.append(mat); [c.objects.unlink(o) for c in list(o.users_collection)]; COLL.objects.link(o); return o
def catmull(points,samples=12):
    p=[Vector(x) for x in points]; out=[]
    for i in range(len(p)-1):
        p0=p[max(i-1,0)]; p1=p[i]; p2=p[i+1]; p3=p[min(i+2,len(p)-1)]
        for j in range(samples):
            t=j/samples; t2=t*t; t3=t2*t; out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
    out.append(p[-1]); return out
def ribbon(name,points,width,z,mat,phase=0):
    pts=catmull(points); vs=[]; fs=[]
    for i,p in enumerate(pts):
        tan=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized(); n=Vector((-tan.y,tan.x,0)); w=width*(0.85+0.15*math.sin(i*.18+phase)); q=p+Vector((.025*math.sin(phase+i*.2),.018*math.cos(phase+i*.23),0)); vs += [(q.x+n.x*w,q.y+n.y*w,z),(q.x-n.x*w,q.y-n.y*w,z)]
    for i in range(len(pts)-1): fs.append((2*i,2*i+1,2*i+3,2*i+2))
    me=bpy.data.meshes.new(name+'_mesh'); me.from_pydata(vs,[],fs); me.update(); o=bpy.data.objects.new(name,me); COLL.objects.link(o); o.data.materials.append(mat); return o
def camera():
    d=bpy.data.cameras.new('review_camera'); o=bpy.data.objects.new('review_camera',d); COLL.objects.link(o); o.location=(0,0,7); look_at(o); d.type='ORTHO'; d.ortho_scale=CAM_SCALE; SCENE.camera=o
def build(state,phase=0,path=None):
    clear_scene(); s=SCENE; s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=W; s.render.resolution_y=H; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.render.film_transparent=False; s.render.filepath=path or os.path.join(RD,state+'.png'); s.world=bpy.data.worlds.new('water_orb_2p5d_world'); s.world.color=(.82,.9,.92); s.view_settings.view_transform='Standard'; s.view_settings.look='None'; s.view_settings.exposure=.0
    bg=radial_material('background_mist',[(0,(.84,.93,.96)),(.55,(.91,.965,.975)),(1,(.86,.93,.95))],.9); add_plane('background_plane',30,-.6,bg); camera()
    # fixed-front spherical gradient: aqua body and pale edge imply transparent volume without a dithered shell
    shell=spherical_material('orb_glass',[(0,(.78,.91,.91)),(.18,(.45,.75,.77)),(.55,(.17,.48,.53)),(.84,(.08,.29,.34)),(1,(.04,.17,.22))],.92); add_uv('orb_shell',(0,0,0),(1.34,1.30,1.0),shell)
    core=spherical_material('core_teal',[(0,(.10,.36,.42)),(.20,(.12,.42,.48)),(.62,(.24,.56,.60)),(.86,(.30,.62,.65)),(1,(.38,.68,.70))],.72); add_uv('inner_core',(-.06,.02,1.06),(1.26,1.22,.54),core)
    cyan=flat_material('flow_cyan',(.25,.70,.73),.34,.40); warm=flat_material('flow_warm',(.90,.78,.65),.24,.25); soft=flat_material('flow_soft',(.36,.66,.68),.12,.14)
    p1=[(-.78,.22,.11),(-.48,.46,.11),(-.12,.42,.11),(.22,.18,.11),(.52,-.12,.11)]; p2=[(-.63,-.20,.12),(-.34,-.40,.12),(.03,-.37,.12),(.34,-.14,.12),(.58,.18,.12)]
    if state=='moving': p1=[(x+.05*math.sin(phase),y+.045*math.cos(phase),z) for x,y,z in p1]; p2=[(x-.04*math.cos(phase),y+.04*math.sin(phase),z) for x,y,z in p2]
    ribbon('flow_band_soft',[(-.82,.06,.11),(-.48,.26,.11),(-.08,.24,.11),(.32,.02,.11),(.60,-.24,.11)],.15,1.68,soft,phase*.4)
    ribbon('flow_band_cyan',p1,.072,1.72,cyan,phase); ribbon('flow_band_warm',p2,.056,1.74,warm,-phase)
    if state=='moving': ribbon('flow_band_moving',[(-.56,.02,.13),(-.28,.20,.13),(.06,.16,.13),(.38,-.02,.13),(.60,-.22,.13)],.042,1.78,cyan,phase+.6)
    cool=flat_material('point_cool',(.34,.78,.86),1,1.15); hot=flat_material('point_warm',(.86,.48,.25),1,1.15); add_uv('point_cool',(-.46,.28,1.62),(.058,.058,.04),cool); add_uv('point_warm',(.42,-.27,1.63),(.058,.058,.04),hot)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(RD,'water_orb_'+state+'.blend')); bpy.ops.render.render(write_still=True)
def run_all():
    build('still',0,os.path.join(RD,'still.png'))
    for i in range(8): build('moving',2*math.pi*i/8,os.path.join(RD,f'moving_{i:02d}.png'))
    shutil.copyfile(os.path.join(RD,'moving_00.png'),os.path.join(RD,'moving.png'))
    with open(os.path.join(OUT,'render_manifest_2p5d.json'),'w') as f: json.dump({'engine':'BLENDER_EEVEE','resolution':[W,H],'camera':'orthographic_front','states':['still','moving'],'moving_frames':8,'external_ribbons':False,'layers':['orb_shell','inner_core','orb_rim_layer','flow_band_cyan','flow_band_warm','flow_band_moving','point_cool','point_warm']},f,indent=2)
