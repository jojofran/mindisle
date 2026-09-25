import bpy, math, os, json, sys
from mathutils import Vector

ROOT = "/Users/fran/Documents/Code/mindisle"
OUT = os.path.join(ROOT, "image2blender-runs", "water-orb")
RENDER_DIR = os.path.join(OUT, "renders_v2")
os.makedirs(RENDER_DIR, exist_ok=True)
SCENE = None
COLL = None

W, H = 640, 1384
ASPECT = W / H
ORB_R = 1.28
CAM_SCALE = 7.65

def set_input(node, value, *names):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return

def set_surface(mat):
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = 'BLENDED'

def material_bg():
    mat = bpy.data.materials.new("background_mist")
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 1.4
    tex.inputs["Detail"].default_value = 2.0
    tex.inputs["Roughness"].default_value = 0.65
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (0.86, 0.94, 0.965, 1)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.97, 0.985, 0.985, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    set_input(em, 0.72, "Strength")
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat

def material_shell():
    mat = bpy.data.materials.new("orb_glass")
    mat.use_nodes = True; set_surface(mat)
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    rimr = nt.nodes.new("ShaderNodeValToRGB")
    rimr.color_ramp.elements[0].position = 0.10; rimr.color_ramp.elements[0].color = (0,0,0,1)
    rimr.color_ramp.elements[1].position = 0.50; rimr.color_ramp.elements[1].color = (1,1,1,1)
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    nt.links.new(inv.outputs[0], rimr.inputs[0])
    set_input(bs, (0.12, 0.42, 0.48, 1), "Base Color")
    set_input(bs, 0.14, "Roughness")
    set_input(bs, 1.33, "IOR")
    set_input(bs, 0.12, "Transmission Weight", "Transmission")
    set_input(bs, (0.22, 0.55, 0.60, 1), "Emission Color", "Emission")
    set_input(bs, 0.10, "Emission Strength")
    if "Coat Weight" in bs.inputs: bs.inputs["Coat Weight"].default_value = 0.28
    if "Coat Roughness" in bs.inputs: bs.inputs["Coat Roughness"].default_value = 0.08
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixs = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(rimr.outputs[0], mixs.inputs[0])
    nt.links.new(tr.outputs[0], mixs.inputs[1])
    nt.links.new(bs.outputs[0], mixs.inputs[2])
    nt.links.new(mixs.outputs[0], out.inputs[0])
    return mat

def material_core():
    mat = bpy.data.materials.new("core_teal")
    mat.use_nodes = True; set_surface(mat)
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = 2.7; tex.inputs["Detail"].default_value = 4.0; tex.inputs["Roughness"].default_value = 0.7
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.03, 0.19, 0.22, 1)
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[1].color = (0.22, 0.57, 0.59, 1)
    ramp.color_ramp.elements[1].position = 0.82
    nt.links.new(tex.outputs["Fac"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], bs.inputs["Base Color"])
    set_input(bs, 0.3, "Roughness"); set_input(bs, 1.33, "IOR"); set_input(bs, 0.08, "Transmission Weight", "Transmission")
    set_input(bs, (0.02, 0.20, 0.24, 1), "Emission Color", "Emission"); set_input(bs, 0.08, "Emission Strength")
    nt.links.new(bs.outputs[0], out.inputs[0])
    return mat

def material_flow(name, color, alpha=0.26, emission=0.0):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; set_surface(mat)
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    set_input(bs, (*color, 1), "Base Color"); set_input(bs, 0.18, "Roughness"); set_input(bs, alpha, "Alpha")
    if emission:
        set_input(bs, (*color, 1), "Emission Color", "Emission")
        set_input(bs, emission, "Emission Strength")
    nt.links.new(bs.outputs[0], out.inputs[0])
    return mat

def material_point(name, color):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bs = nt.nodes.get("Principled BSDF")
    set_input(bs, (*color, 1), "Base Color")
    set_input(bs, 0.12, "Roughness")
    set_input(bs, (*color, 1), "Emission Color", "Emission")
    set_input(bs, 1.35, "Emission Strength")
    return mat

def clear_scene():
    global SCENE, COLL
    old = bpy.data.scenes.get("water_orb_v2")
    if old:
        bpy.data.scenes.remove(old)
    SCENE = bpy.data.scenes.new("water_orb_v2")
    COLL = SCENE.collection
    for window in bpy.context.window_manager.windows:
        window.scene = SCENE

def look_at(obj, target=(0,0,0)):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

def add_uv(name, loc, scale, mat, segments=96, rings=64):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat)
    return o

def catmull(points, samples=8):
    pts = [Vector(p) for p in points]
    out = []
    for i in range(len(pts)-1):
        p0 = pts[max(0,i-1)]; p1=pts[i]; p2=pts[i+1]; p3=pts[min(len(pts)-1,i+2)]
        for j in range(samples):
            t=j/samples; t2=t*t; t3=t2*t
            out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
    out.append(pts[-1]); return out

def add_ribbon(name, points, widths, z, mat, phase=0.0):
    pts = catmull(points, 10)
    ws = []
    for i in range(len(pts)):
        t=i/(len(pts)-1)
        # gently breathe the band; still uses phase 0, moving shifts the internal flow only
        ws.append(widths[0]*(1-t)+widths[-1]*t)
    verts=[]; faces=[]
    for i,p in enumerate(pts):
        if i==0: tangent=pts[1]-pts[0]
        elif i==len(pts)-1: tangent=pts[-1]-pts[-2]
        else: tangent=pts[i+1]-pts[i-1]
        tangent.normalize(); n=Vector((-tangent.y, tangent.x, 0));
        p2 = p + Vector((0.03*math.sin(phase + i*0.28), 0.02*math.cos(phase + i*0.24), 0))
        verts.extend([(p2.x+n.x*ws[i], p2.y+n.y*ws[i], z), (p2.x-n.x*ws[i], p2.y-n.y*ws[i], z)])
    for i in range(len(pts)-1): faces.append((2*i,2*i+1,2*i+3,2*i+2))
    me=bpy.data.meshes.new(name+"_mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); COLL.objects.link(o); o.data.materials.append(mat)
    sol=o.modifiers.new("micro_thickness",'SOLIDIFY'); sol.thickness=0.008; sol.offset=0
    return o

def add_lights():
    for name, loc, energy, size in [
        ("key_light", (2.8,-2.0,4.2), 130, 3.0),
        ("fill_light", (-3.0,-1.0,2.0), 55, 4.0),
        ("rim_light", (1.8,2.8,2.4), 90, 2.0)]:
        data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size
        o=bpy.data.objects.new(name,data); COLL.objects.link(o); o.location=loc; look_at(o,(0,0,0))

def add_camera():
    data=bpy.data.cameras.new("review_camera"); cam=bpy.data.objects.new("review_camera",data); COLL.objects.link(cam)
    cam.location=(0,0,7); look_at(cam,(0,0,0)); data.type='ORTHO'; data.ortho_scale=CAM_SCALE; bpy.context.scene.camera=cam
    return cam

def add_background(mat):
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0,0,-0.7)); o=bpy.context.object; o.name='background_plane'; o.data.materials.append(mat)
    for c in list(o.users_collection): c.objects.unlink(o)
    COLL.objects.link(o)

def make_state(state, phase=0.0):
    clear_scene()
    scene=SCENE
    engines={i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items}
    scene.render.engine='CYCLES' if 'CYCLES' in engines else ('BLENDER_EEVEE' if 'BLENDER_EEVEE' in engines else 'BLENDER_EEVEE_NEXT')
    if scene.render.engine == 'CYCLES':
        scene.cycles.samples = 32
        scene.cycles.use_denoising = True
    scene.render.resolution_x=W; scene.render.resolution_y=H; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
    scene.render.image_settings.color_mode='RGBA'
    scene.render.filepath=os.path.join(RENDER_DIR, f"{state}.png")
    scene.world = bpy.data.worlds.new('water_orb_world') if scene.world is None else scene.world
    scene.world.color=(0.78,0.88,0.9)
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.25
    # Keep the render path simple and deterministic; point emission is deliberately restrained.
    scene.use_nodes=False
    bg=material_bg(); shell=material_shell(); core=material_core()
    cyan=material_flow('flow_cyan',(0.28,0.78,0.82),0.26,0.10)
    warm=material_flow('flow_warm',(0.98,0.86,0.70),0.18,0.06)
    coolp=material_point('point_cool',(0.52,0.9,0.98)); warmp=material_point('point_warm',(1.0,0.56,0.27))
    add_background(bg); add_camera(); add_lights()
    # Same silhouette and center in both states; only internal layers change.
    shell_obj=add_uv('orb_shell',(0,0,0),(ORB_R*1.02,ORB_R*0.98,ORB_R*0.92),shell)
    core_obj=add_uv('inner_core',(0.0,-0.02,0.13),(0.90,0.88,0.42),core)
    # soft inner flow, broad and planar so it cannot read as external tubing
    p1=[(-0.82,0.30,0.28),(-0.50,0.56,0.31),(-0.10,0.50,0.32),(0.33,0.20,0.33),(0.66,-0.17,0.31)]
    p2=[(-0.72,-0.28,0.30),(-0.38,-0.52,0.31),(0.04,-0.48,0.32),(0.42,-0.22,0.33),(0.72,0.23,0.30)]
    if state=='moving':
        p1=[(x+0.06*math.sin(phase),y+0.05*math.cos(phase),z) for x,y,z in p1]
        p2=[(x-0.05*math.cos(phase),y+0.04*math.sin(phase),z) for x,y,z in p2]
    add_ribbon('flow_band_cyan',p1,[0.11,0.07],0.34,cyan,phase)
    add_ribbon('flow_band_warm',p2,[0.09,0.05],0.35,warm,-phase)
    if state=='moving':
        p3=[(-0.72,0.04,0.37),(-0.34,0.23,0.38),(0.06,0.18,0.39),(0.46,-0.04,0.38),(0.72,-0.30,0.36)]
        add_ribbon('flow_band_moving',p3,[0.07,0.03],0.39,cyan,phase+0.7)
    add_uv('point_cool',(-0.48,0.30,0.46),(0.075,0.075,0.075),coolp,48,32)
    add_uv('point_warm',(0.43,-0.28,0.47),(0.078,0.078,0.078),warmp,48,32)
    # subtle inner highlight ellipsoid, behind the shell; gives volume without a separate ring
    hi=material_flow('inner_highlight',(0.72,0.94,0.94),0.035,0.05)
    add_uv('inner_highlight',(-0.16,0.17,0.27),(0.62,0.42,0.20),hi,64,40)
    # save state-specific scene and render
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(RENDER_DIR, f"water_orb_{state}.blend"))
    bpy.ops.render.render(write_still=True)

def main():
    make_state('still',0.0)
    for i in range(8):
        phase=2*math.pi*i/8
        make_state('moving',phase)
        os.replace(os.path.join(RENDER_DIR,'moving.png'), os.path.join(RENDER_DIR,f'moving_{i:02d}.png'))
    # phase 0 is the canonical moving.png
    import shutil
    shutil.copyfile(os.path.join(RENDER_DIR,'moving_00.png'), os.path.join(RENDER_DIR,'moving.png'))
    # write lightweight manifest from rendered files
    manifest={'engine':'BLENDER_EEVEE_NEXT','resolution':[W,H],'camera_ortho_scale':CAM_SCALE,'orb_radius':ORB_R,'states':['still','moving'],'moving_frames':8,'external_ribbons':False,'notes':'fixed front 2.5D visual component; internal flow only'}
    with open(os.path.join(OUT,'render_manifest_v2.json'),'w') as f: json.dump(manifest,f,indent=2)

if __name__=='__main__': main()
