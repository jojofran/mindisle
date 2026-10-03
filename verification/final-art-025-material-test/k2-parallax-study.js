/* Verification-only inferred internal parallax. Camera and shell stay fixed. */
const SIZE = 360;
const byId = id => document.getElementById(id);
const state = {x:0, y:0, flow:0, phase:0, background:'light', playing:false, ready:false};
const modes = {light:0, dark:1, split:2, checker:3};
const files = {
  base:'k2-complete-authored-field/field-authority-a-rgb.png',
  trans:'k2-complete-authored-field/field-transmission.png',
  residual:'k2-complete-authored-field/field-residual-signed-encoded.png',
  mask:'k2-complete-authored-field/field-interior-mask.png',
  silhouette:'k2-complete-authored-field/field-silhouette.png',
  horizontal:'k2-parallax-field/field-parallax-horizontal.png',
  vertical:'k2-parallax-field/field-parallax-vertical.png',
};
const vertex = `#version 300 es
in vec2 p; out vec2 uv;
void main(){ uv=p*.5+.5; gl_Position=vec4(p,0.,1.); }`;
const fragment = `#version 300 es
precision highp float; in vec2 uv; out vec4 outColor;
uniform sampler2D tBase,tTrans,tResidual,tMask,tSilhouette,tHorizontal,tVertical;
uniform vec2 parallax; uniform float flow,phase; uniform int bgMode;
uniform bool uniformBasis;
vec3 bg(vec2 p){
  if(bgMode==1)return vec3(.07,.13,.16);
  if(bgMode==2)return mix(vec3(.8784,.9216,.9373),vec3(.07,.13,.16),step(.5,p.x));
  if(bgMode==3){vec2 c=floor(p*12.);return mix(vec3(.96,.97,.92),vec3(.82,.89,.91),mod(c.x+c.y,2.));}
  return vec3(.8784,.9216,.9373);
}
float decoded(sampler2D field,ivec2 p){
  ivec2 size=textureSize(field,0);
  vec2 bytes=floor(texelFetch(field,clamp(p,ivec2(0),size-1),0).rg*255.+.5);
  return (bytes.x*256.+bytes.y-32768.)/32767.*.08;
}
// Decode each 16-bit scalar first; interpolating byte channels breaks carries.
float basis(sampler2D field,vec2 p){
  vec2 pixel=p*vec2(textureSize(field,0))-.5; ivec2 q=ivec2(floor(pixel)); vec2 f=fract(pixel);
  return mix(mix(decoded(field,q),decoded(field,q+ivec2(1,0)),f.x),
             mix(decoded(field,q+ivec2(0,1)),decoded(field,q+ivec2(1,1)),f.x),f.y);
}
void main(){
  float im=texture(tMask,uv).r, sil=texture(tSilhouette,uv).r;
  vec2 delta=vec2(basis(tHorizontal,uv)*parallax.x,basis(tVertical,uv)*parallax.y);
  if(uniformBasis)delta=vec2(parallax.x,-parallax.y)*.00675*im;
  vec2 drift=vec2(sin(uv.y*7.+phase),cos(uv.x*6.-phase))*.026*flow*im;
  vec2 q=clamp(uv+delta+drift,0.,1.);
  vec3 fit=bg(uv)*texture(tTrans,q).rgb+texture(tResidual,q).rgb*2.-1.;
  vec3 color=mix(texture(tBase,uv).rgb,fit,im);
  outColor=vec4(mix(bg(uv),color,sil),1.);
}`;
let gl,program,loc,maskPixels,silPixels,raf=0,last=0,elapsed=0,uniformBasis=false;
function shader(type,source){
  const s=gl.createShader(type); gl.shaderSource(s,source); gl.compileShader(s);
  if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s)); return s;
}
function image(url){return new Promise((ok,no)=>{const img=new Image();img.onload=()=>ok(img);img.onerror=()=>no(Error(url));img.src=url;});}
function pixels(img){
  const c=document.createElement('canvas');c.width=c.height=SIZE;
  const ctx=c.getContext('2d');ctx.drawImage(img,0,0,SIZE,SIZE);
  const raw=ctx.getImageData(0,0,SIZE,SIZE).data,out=new Uint8Array(raw.length);
  for(let y=0;y<SIZE;y++)out.set(raw.subarray(y*SIZE*4,(y+1)*SIZE*4),(SIZE-1-y)*SIZE*4);
  return out;
}
function inspect(){return {...state,elapsed,rafActive:raf!==0,camera:'fixed',runtime:false,production:false};}
function draw(){
  if(!state.ready)return;
  gl.viewport(0,0,SIZE,SIZE);gl.useProgram(program);
  gl.uniform2f(loc.parallax,state.x,state.y);gl.uniform1f(loc.flow,state.flow);
  gl.uniform1f(loc.phase,state.phase);gl.uniform1i(loc.bgMode,modes[state.background]);
  gl.uniform1i(loc.uniformBasis,uniformBasis?1:0);gl.drawArrays(gl.TRIANGLES,0,6);
  byId('parallax').value=state.x;byId('parallaxValue').textContent=state.x.toFixed(3);
  byId('params').textContent=JSON.stringify(inspect(),null,2);
  document.querySelectorAll('[data-bg]').forEach(b=>b.classList.toggle('active',b.dataset.bg===state.background));
}
function pause(){state.playing=false;cancelAnimationFrame(raf);raf=0;draw();}
function play(){
  if(!state.ready||state.playing)return;
  state.playing=true;last=performance.now();raf=requestAnimationFrame(loop);draw();
}
function loop(now){
  if(!state.playing)return;
  elapsed+=Math.min(.064,Math.max(0,(now-last)/1000));last=now;
  const ramp=Math.min(1,elapsed/1.5);const fade=ramp*ramp*(3-2*ramp);
  state.x=fade*Math.sin(elapsed*.68);state.y=fade*.6*Math.sin(elapsed*.50);
  state.flow=fade*.42;state.phase=elapsed*.82;draw();raf=requestAnimationFrame(loop);
}
function reset(){pause();elapsed=0;Object.assign(state,{x:0,y:0,flow:0,phase:0,background:'light'});draw();}
function set(values){
  pause();for(const key of ['x','y'])if(key in values)state[key]=Math.max(-1,Math.min(1,values[key]));
  if('flow' in values)state.flow=Math.max(0,Math.min(1,values.flow));
  if('phase' in values)state.phase=values.phase;
  if(values.background in modes)state.background=values.background;draw();
}
function frame(){const a=new Uint8Array(SIZE*SIZE*4);gl.readPixels(0,0,SIZE,SIZE,gl.RGBA,gl.UNSIGNED_BYTE,a);return a;}
function compare(a,b,region){
  let n=0,sum=0,max=0;
  for(let i=0;i<a.length;i+=4){
    const m=maskPixels[i],s=silPixels[i];
    const hit=region==='outside'?s===0:region==='protected'?s>230&&m===0:region==='all'?true:m>16;
    if(!hit)continue;
    for(let k=0;k<3;k++){const d=Math.abs(a[i+k]-b[i+k]);sum+=d;max=Math.max(max,d);n++;}
  }
  return {channels:n,mean:n?sum/n:0,max};
}
function quality(){
  if(!state.ready)throw Error('字段未加载');
  const old={...state},oldElapsed=elapsed;pause();const rows=[];
  try{
    state.flow=state.phase=0;
    for(const background of Object.keys(modes)){
      Object.assign(state,{x:0,y:0,background});draw();const center=frame();
      const axes=[];
      for(const axis of ['x','y']){
        let prev;const adjacent=[];
        for(let i=0;i<=20;i++){
          Object.assign(state,{x:0,y:0,[axis]:-1+i*.1});draw();const current=frame();
          if(prev)adjacent.push(compare(prev,current,'interior'));prev=current;
        }
        axes.push({axis,adjacent,minMean:Math.min(...adjacent.map(a=>a.mean)),
          smoothRatio:Math.max(...adjacent.map(a=>a.mean))/Math.min(...adjacent.map(a=>a.mean))});
      }
      const corners=[];
      for(const x of [-1,1])for(const y of [-1,1]){
        Object.assign(state,{x,y});draw();const f=frame();
        corners.push({x,y,outside:compare(center,f,'outside'),protected:compare(center,f,'protected'),interior:compare(center,f,'interior')});
      }
      Object.assign(state,{x:0,y:0});draw();const returned=compare(center,frame(),'all');
      Object.assign(state,{x:1,y:1});draw();const authored=frame();
      uniformBasis=true;draw();const ablation=compare(authored,frame(),'interior');uniformBasis=false;
      rows.push({background,axes,corners,returnToCenter:returned,vsUniformShift:ablation});
    }
    const pass=rows.every(r=>r.returnToCenter.max===0&&r.vsUniformShift.mean>0&&
      r.corners.every(c=>c.outside.max===0&&c.protected.max<=1&&c.interior.mean>0)&&
      r.axes.every(a=>a.minMean>0&&a.smoothRatio<3));
    const result={schema:'mindisle.k2-depth-parallax-gpu.v1',status:pass?'PASS_TECHNICAL':'FAIL_TECHNICAL',
      camera:'fixed',physicalFreeView:false,samplesPerAxis:21,backgrounds:rows,
      criteria:'outside=0; protected<=1; center reset exact; each adjacent interior mean>0; smoothRatio<3; authored differs from uniform shift',
      visualGate:'OPEN_NEW_PARALLAX_MOTION',runtime:false,production:false};
    byId('qualityResult').textContent=JSON.stringify(result,null,2);return result;
  }finally{
    uniformBasis=false;Object.assign(state,old,{playing:false});elapsed=oldElapsed;draw();if(old.playing)play();
  }
}
async function start(){
  try{
    gl=byId('gpu').getContext('webgl2',{preserveDrawingBuffer:true});if(!gl)throw Error('需要 WebGL2');
    program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));
    gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
    loc=Object.fromEntries(['parallax','flow','phase','bgMode','uniformBasis'].map(k=>[k,gl.getUniformLocation(program,k)]));
    const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    const a=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL,gl.NONE);
    for(const [unit,[key,url]] of Object.entries(files).entries()){
      const img=await image(url);if(key==='mask')maskPixels=pixels(img);if(key==='silhouette')silPixels=pixels(img);
      gl.activeTexture(gl.TEXTURE0+unit);const t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,img);
      gl.uniform1i(gl.getUniformLocation(program,'t'+key[0].toUpperCase()+key.slice(1)),unit);
    }
    state.ready=true;byId('status').textContent='字段已加载 · 固定镜头 · 外壳和光点固定';draw();
  }catch(e){byId('status').textContent='加载失败：'+e.message;}
}
byId('play').onclick=play;byId('pause').onclick=pause;byId('reset').onclick=reset;
byId('parallax').oninput=e=>set({x:+e.target.value,y:0,flow:0});
byId('quality').onclick=()=>{try{quality();}catch(e){byId('qualityResult').textContent=e.message;}};
document.querySelectorAll('[data-bg]').forEach(b=>b.onclick=()=>{state.background=b.dataset.bg;draw();});
let answer='';
function verdict(){return `K2 内部层次视差裁决\nVERDICT=${answer==='是'?'PASS_REVIEW':answer==='否'?'REVISE_VISUAL':'HOLD'}\n球体、光点与内部水感：${answer}\n备注：${byId('note').value.trim()||'（未补充备注）'}`;}
document.querySelectorAll('[data-answer]').forEach(b=>b.onclick=()=>{
  answer=b.dataset.answer;document.querySelectorAll('[data-answer]').forEach(a=>a.classList.toggle('active',a===b));byId('result').textContent=verdict();
});
byId('copy').onclick=async()=>{if(!answer)return;const text=verdict();byId('result').textContent=text;try{await navigator.clipboard.writeText(text);}catch{byId('result').textContent=text+'\n请手动复制。';}};
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
window.__K2_PARALLAX_STUDY__={inspect,set,play,pause,reset,quality};start();
