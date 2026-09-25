/* Formal v1 layered still renderer with deterministic, low-attention idle motion. */
(() => {
  const profile = window.WATERBALL_PROFILE;
  const scriptBase = new URL('../../', document.currentScript.src);
  const assetUrl = relative => new URL(relative, scriptBase);
  const loadImage = path => new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('无法加载水球素材：' + path));
    image.src = assetUrl(path);
  });
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  class Waterball extends EventTarget {
    constructor(host, {onActivate = () => {}, state = 'still'} = {}) {
      super();
      this.host = host;
      this.state = state;
      this.onActivate = onActivate;
      this.ready = false;
      this.frames = 0;
      this.idleEpoch = performance.now();
      this.idleTime = 0;
      this.visualTime = 0;
      this.idlePhase = 0;
      this.lifecycleSuspended = document.visibilityState === 'hidden';
      this.animationLoopRunning = false;
      this.animationLoopStarts = 0;
      this.suspendCount = 0;
      this.resumeCount = 0;
      this.debugMaterial = new URLSearchParams(location.search).has('shaderDebug');
      this.reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
      this.motionQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)');
      this.canvas = document.createElement('canvas');
      this.canvas.className = 'waterball-canvas';
      this.canvas.setAttribute('aria-hidden', 'true');
      Object.assign(this.canvas.style, {position:'absolute', inset:'0', width:'100%', height:'100%', zIndex:'0'});
      host.append(this.canvas);
      this.materialCanvas = document.createElement('canvas');
      this.materialCanvas.className = 'waterball-material-canvas';
      this.materialCanvas.setAttribute('aria-hidden', 'true');
      Object.assign(this.materialCanvas.style, {position:'absolute', inset:'0', width:'100%', height:'100%', zIndex:'1', pointerEvents:'none'});
      host.append(this.materialCanvas);
      this.initMaterial();
      if (this.debugMaterial) this.canvas.style.visibility = 'hidden';
      this.button = document.createElement('button');
      this.button.type = 'button';
      this.button.className = 'waterball-touch';
      this.button.disabled = true;
      host.append(this.button);
      this.button.addEventListener('click', event => {
        if (!this.ready) return;
        const rect = host.getBoundingClientRect();
        if (event.detail && !this.hit(event.clientX - rect.left, event.clientY - rect.top)) return;
        const detail = {state: this.state, point: {x: event.clientX - rect.left, y: event.clientY - rect.top}};
        host.dispatchEvent(new CustomEvent('water-orb-hit', {bubbles: true, detail}));
        this.dispatchEvent(new CustomEvent('water-orb-hit', {detail}));
        this.onActivate(detail);
      });
      this.onMotionChange = event => {
        this.reducedMotion = event.matches;
        if (this.reducedMotion) {
          this.idleTime = 0;
          this.visualTime = 0;
          this.stopAnimationLoop();
        } else {
          this.idleEpoch = performance.now();
        }
        this.draw();
        this.startAnimationLoop();
      };
      this.onVisibilityChange = () => {
        if (document.visibilityState === 'hidden') this.suspend('visibilitychange');
        else this.resume('visibilitychange');
      };
      this.onPageHide = () => this.suspend('pagehide');
      this.onPageShow = () => this.resume('pageshow');
      document.addEventListener('visibilitychange', this.onVisibilityChange);
      window.addEventListener('pagehide', this.onPageHide);
      window.addEventListener('pageshow', this.onPageShow);
      this.motionQuery?.addEventListener?.('change', this.onMotionChange);
      this.observer = new ResizeObserver(() => this.draw());
      this.observer.observe(host);
      this.loaded = this.loadLayers();
    }
    async loadLayers() {
      const entries = await Promise.all(profile.layerOrder.map(async name => [name, await loadImage(profile.assetRoot + profile.layers[name])]));
      this.images = Object.fromEntries(entries);
      this.renderImages = {};
      for (const name of profile.dynamicLayers) {
        const [sx, sy, sw, sh] = profile.layerBounds[name];
        const crop = document.createElement('canvas'); crop.width = sw; crop.height = sh;
        crop.getContext('2d').drawImage(this.images[name], sx, sy, sw, sh, 0, 0, sw, sh);
        this.renderImages[name] = crop;
        if (name === '03_boundary_mask') {
          // The formal boundary is deliberately faint. A restrained runtime
          // boost lets its moving position read without inventing a new shape.
          const boundary = document.createElement('canvas'); boundary.width = sw; boundary.height = sh;
          const boundaryCtx = boundary.getContext('2d');
          boundaryCtx.drawImage(crop, 0, 0);
          boundaryCtx.globalAlpha = 0.62;
          boundaryCtx.drawImage(crop, 0, 0);
          this.boundaryCurve = boundary;
        }
        if (name === '11_curvature_highlights') {
          // Boost only the moving copy. The static composite remains untouched,
          // so the shell stays a single stable object while its curve travels.
          const curve = document.createElement('canvas'); curve.width = sw; curve.height = sh;
          const curveCtx = curve.getContext('2d');
          curveCtx.drawImage(crop, 0, 0);
          curveCtx.globalAlpha = 0.48;
          curveCtx.drawImage(crop, 0, 0);
          this.shellCurve = curve;
          this.shellWave = document.createElement('canvas');
          this.shellWave.width = sw; this.shellWave.height = sh;
          // Reuse the formal highlight alpha as a restrained, blue-green depth fold.
          // This is generated at runtime from the same v1 layer; it is not a second asset.
          const shade = document.createElement('canvas'); shade.width = sw; shade.height = sh;
          const shadeCtx = shade.getContext('2d');
          shadeCtx.drawImage(crop, 0, 0);
          shadeCtx.globalCompositeOperation = 'source-in';
          shadeCtx.fillStyle = '#52777a';
          shadeCtx.fillRect(0, 0, sw, sh);
          this.shellShade = shade;
        }
      }
      this.staticComposite = await loadImage(profile.assetRoot + profile.staticComposite);
      this.prepareMaterialTexture();
      this.staticCompositeCanvas = document.createElement('canvas');
      this.staticCompositeCanvas.width = profile.frame[0]; this.staticCompositeCanvas.height = profile.frame[1];
      const compositeCtx = this.staticCompositeCanvas.getContext('2d');
      compositeCtx.drawImage(this.staticComposite, 0, 0);
      compositeCtx.globalCompositeOperation = 'destination-in';
      const compositeMask = compositeCtx.createRadialGradient(profile.center[0], profile.center[1], 410, profile.center[0], profile.center[1], 690);
      compositeMask.addColorStop(0, 'rgba(255,255,255,1)'); compositeMask.addColorStop(0.72, 'rgba(255,255,255,0.94)'); compositeMask.addColorStop(1, 'rgba(255,255,255,0)');
      compositeCtx.fillStyle = compositeMask; compositeCtx.fillRect(0, 0, profile.frame[0], profile.frame[1]);
      this.plate = document.createElement('canvas');
      this.plate.width = profile.frame[0]; this.plate.height = profile.frame[1];
      const plateCtx = this.plate.getContext('2d');
      plateCtx.drawImage(this.images['00_background_plate'], 0, 0);
      plateCtx.globalCompositeOperation = 'destination-in';
      const mask = plateCtx.createRadialGradient(profile.center[0], profile.center[1], 420, profile.center[0], profile.center[1], 700);
      mask.addColorStop(0, 'rgba(255,255,255,1)'); mask.addColorStop(0.72, 'rgba(255,255,255,0.92)'); mask.addColorStop(1, 'rgba(255,255,255,0)');
      plateCtx.fillStyle = mask; plateCtx.fillRect(0, 0, profile.frame[0], profile.frame[1]);
      this.ready = true;
      this.button.disabled = false;
      this.draw();
      this.startAnimationLoop();
      return this;
    }
    initMaterial() {
      const gl = this.materialCanvas.getContext('webgl', {alpha: true, antialias: true});
      if (!gl) return;
      const vertex = `attribute vec2 p; void main(){gl_Position=vec4(p,0.0,1.0);}`;
      const fragment = `precision mediump float;
        uniform vec2 u_resolution, u_center; uniform float u_radius, u_time, u_strength; uniform sampler2D u_texture;
        float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
        float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.,1.)),f.x),f.y);}
        void main(){
          vec2 p=(gl_FragCoord.xy-u_center)/u_radius; float r=length(p); if(r>1.0) discard;
    float dCool=distance(p,vec2(-0.40,0.45));
    float dCoolFlip=distance(p,vec2(-0.40,-0.45));
    float dWarm=distance(p,vec2(0.50,-0.45));
    float dWarmFlip=distance(p,vec2(0.50,0.45));
    float pointKeep=min(min(smoothstep(0.52,0.78,dCool),smoothstep(0.52,0.78,dCoolFlip)),min(smoothstep(0.52,0.78,dWarm),smoothstep(0.52,0.78,dWarmFlip)));
          float t=u_time*0.58; vec2 q=p;
          float swell=sin(p.x*3.1+t*0.72)+cos(p.y*2.7-t*0.61);
          q+=0.078*swell*normalize(p)*smoothstep(0.08,0.92,r);
          q+=0.068*vec2(sin(p.y*3.8+t*0.72),cos(p.x*3.4-t*0.66));
          q+=0.030*vec2(sin(p.y*7.0-t*0.35),cos(p.x*6.4+t*0.31));
          float n=noise(q*3.0+vec2(t*0.45,-t*0.36));
          n=0.72*n+0.28*noise(q*7.0+vec2(-t*0.25,t*0.22));
          // A shared mass field: the center dominates the volume, while the
          // cool/warm points only pull on their nearby water. The field changes
          // depth and light response, never the point locations themselves.
          float centerGravity=exp(-dot(q,q)*2.6);
          float coolGravity=exp(-dot(q-vec2(-0.40,0.45),q-vec2(-0.40,0.45))*10.0);
          float warmGravity=exp(-dot(q-vec2(0.50,-0.45),q-vec2(0.50,-0.45))*10.0);
          float gravity=clamp(centerGravity*0.18+(coolGravity+warmGravity)*0.055,0.0,0.24);
          vec2 uv=vec2(0.5+q.x*0.370,1.0-(0.501+q.y*0.171));
          vec2 orbit=vec2(sin(t*0.58)*0.26,cos(t*0.49)*0.19);
          float gloss=exp(-dot((q-orbit)*vec2(1.15,1.8),(q-orbit)*vec2(1.15,1.8))*5.0);
          float gloss2=exp(-dot((q+orbit*0.8-vec2(0.10,-0.16))*vec2(1.8,1.0),(q+orbit*0.8-vec2(0.10,-0.16))*vec2(1.8,1.0))*7.0);
          float light=clamp(gloss*0.50+gloss2*0.28+n*0.20+gravity*0.10,0.0,1.0);
          float shade=clamp((1.0-n)*0.20+(1.0-gloss)*0.10+centerGravity*0.055,0.0,1.0);
          float edge=smoothstep(1.0,0.72,r);
          vec2 uv0=vec2(0.5+p.x*0.370,1.0-(0.501+p.y*0.171));
          vec3 source0=texture2D(u_texture,uv0).rgb;
          vec3 source=texture2D(u_texture,uv).rgb;
          vec3 col=mix(source0,source,0.72)+vec3(0.035,0.04,0.03)*light-vec3(0.025,0.03,0.025)*shade;
          float a=edge*pointKeep*u_strength*(0.16+0.22*light);
          gl_FragColor=vec4(col,a);
        }`;
      const compile=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);return s;};
      const program=gl.createProgram(); gl.attachShader(program,compile(gl.VERTEX_SHADER,vertex)); gl.attachShader(program,compile(gl.FRAGMENT_SHADER,fragment)); gl.linkProgram(program);
      const buffer=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buffer); gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      this.material={gl,program,buffer,p:gl.getAttribLocation(program,'p'),resolution:gl.getUniformLocation(program,'u_resolution'),center:gl.getUniformLocation(program,'u_center'),radius:gl.getUniformLocation(program,'u_radius'),time:gl.getUniformLocation(program,'u_time'),strength:gl.getUniformLocation(program,'u_strength'),texture:gl.getUniformLocation(program,'u_texture')};
    }
    prepareMaterialTexture() {
      if (!this.material || !this.staticComposite) return;
      const gl=this.material.gl; this.material.textureObject=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,this.material.textureObject); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,this.staticComposite); gl.bindTexture(gl.TEXTURE_2D,null);
    }
    drawMaterial(layout,time) {
      if (!this.material || this.reducedMotion) { if (this.material) this.material.gl.clear(this.material.gl.COLOR_BUFFER_BIT); return; }
      const {gl,program,buffer,p,resolution,center,radius,strength,texture,textureObject} = this.material;
      const dpr=Math.min(window.devicePixelRatio||1,2); this.materialCanvas.width=Math.max(1,Math.round(layout.width*dpr)); this.materialCanvas.height=Math.max(1,Math.round(layout.height*dpr));
      gl.viewport(0,0,this.materialCanvas.width,this.materialCanvas.height); gl.clearColor(0,0,0,0); gl.clear(gl.COLOR_BUFFER_BIT); gl.useProgram(program); gl.bindBuffer(gl.ARRAY_BUFFER,buffer); gl.enableVertexAttribArray(p); gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D,textureObject); gl.uniform1i(texture,0); gl.uniform2f(resolution,this.materialCanvas.width,this.materialCanvas.height); gl.uniform2f(center,layout.cx*dpr,(layout.height-layout.cy)*dpr); gl.uniform1f(radius,layout.radius*dpr); gl.uniform1f(this.material.time,time); gl.uniform1f(strength,this.debugMaterial?2.4:0.78);
      gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
    }
    layout() {
      const {width, height} = this.host.getBoundingClientRect();
      const scale = Math.min(width / profile.frame[0], height / profile.frame[1]);
      const frameWidth = profile.frame[0] * scale;
      const frameHeight = profile.frame[1] * scale;
      return {width, height, scale, left: (width - frameWidth) / 2, top: (height - frameHeight) / 2,
        cx: (width - frameWidth) / 2 + profile.center[0] * scale,
        cy: (height - frameHeight) / 2 + profile.center[1] * scale,
        radius: profile.radius * scale, hitRadius: profile.hitRadius * scale,
        frame: {width: frameWidth, height: frameHeight}};
    }
    setState(state) { if (state !== 'still') throw new Error('This slice only supports still'); this.state = state; this.draw(); }
    shouldAnimate() {
      return this.ready && this.state === 'still' && !this.reducedMotion && !this.lifecycleSuspended;
    }
    startAnimationLoop() {
      if (this.animationLoopRunning || !this.shouldAnimate()) return false;
      this.animationLoopRunning = true;
      this.animationLoopStarts++;
      const tick = () => {
        this.animationFrame = 0;
        if (!this.shouldAnimate()) {
          this.animationLoopRunning = false;
          return;
        }
        this.draw();
        this.animationFrame = requestAnimationFrame(tick);
      };
      this.animationFrame = requestAnimationFrame(tick);
      return true;
    }
    stopAnimationLoop() {
      if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
      this.animationFrame = 0;
      this.animationLoopRunning = false;
    }
    suspend(reason = 'manual') {
      if (this.lifecycleSuspended) return false;
      this.visualTime = this.now();
      this.idleTime = this.visualTime;
      this.lifecycleSuspended = true;
      this.idleEpoch = performance.now();
      this.suspendCount++;
      this.stopAnimationLoop();
      this.draw();
      this.dispatchEvent(new CustomEvent('lifecycle', {detail: {type: 'suspend', reason, idleTime: this.visualTime}}));
      return true;
    }
    resume(reason = 'manual') {
      if (!this.lifecycleSuspended) return false;
      this.lifecycleSuspended = false;
      this.idleEpoch = performance.now();
      this.resumeCount++;
      this.draw();
      this.startAnimationLoop();
      this.dispatchEvent(new CustomEvent('lifecycle', {detail: {type: 'resume', reason, idleTime: this.idleTime}}));
      return true;
    }
    reset() {
      this.stopAnimationLoop();
      this.idleTime = 0;
      this.visualTime = 0;
      this.idleEpoch = performance.now();
      this.idlePhase = 0;
      this.state = 'still';
      this.draw();
      this.startAnimationLoop();
      this.dispatchEvent(new CustomEvent('lifecycle', {detail: {type: 'reset', idleTime: 0}}));
    }
    now() {
      if (this.reducedMotion || this.state !== 'still') return 0;
      const activeSegment = this.lifecycleSuspended ? 0 : (performance.now() - this.idleEpoch) / 1000;
      return Math.max(0, this.visualTime + activeSegment);
    }
    draw() {
      const layout = this.layout();
      if (!layout.width || !layout.height) return;
      this.geometry = layout;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.canvas.width = Math.max(1, Math.round(layout.width * dpr));
      this.canvas.height = Math.max(1, Math.round(layout.height * dpr));
      const ctx = this.canvas.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, layout.width, layout.height);
      ctx.fillStyle = '#edf3f5';
      ctx.fillRect(0, 0, layout.width, layout.height);
      const t = this.now();
      // Keep the driving phase unwrapped. Taking a modulo here while using
      // fractional harmonics caused a small position/velocity jump at the
      // cycle boundary, which read as a dropped frame. Only the inspector gets
      // the normalized phase value below.
      const phase = t / 3.2 * Math.PI * 2;
      this.idleTime = t;
      this.idlePhase = ((phase % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
      if (this.ready) {
        ctx.save();
        ctx.translate(layout.left, layout.top);
        ctx.scale(layout.scale, layout.scale);
        ctx.drawImage(this.staticCompositeCanvas, 0, 0);
        const sharedDx = Math.sin(phase) * 10.0;
        const sharedDy = Math.cos(phase) * 7.0;
        const sharedTurn = -Math.sin(phase * 0.92) * 0.085;
        const sharedBreathe = 1 + Math.sin(phase * 1.08 + 0.2) * 0.050;
        const shellTurn = phase * 0.92 + 0.10;
        // One smooth out-and-back stroke: zero at entry, deepest at the
        // half-turn, then returning to the round starting shape.
        const dent = 0.5 - 0.5 * Math.cos(shellTurn);
        const volumeDepth = 0.5 - 0.5 * Math.cos(shellTurn - 0.28);
        for (const name of profile.layerOrder) {
          if (!profile.dynamicLayers.has(name)) continue;
          if (this.reducedMotion) continue;
          const image = this.renderImages[name];
          const [bx, by] = profile.layerBounds[name];
          let alpha = 0.36, dx = 0, dy = 0, breathe = 1;
          if (name === '02_internal_cyan_volume') { alpha = 0.58 + volumeDepth * 0.42 + Math.sin(phase * 0.55) * 0.04; breathe = 1 + volumeDepth * 0.045 + Math.sin(phase * 0.55) * 0.008; dx = Math.sin(phase * 0.31) * 3.6; dy = Math.cos(phase * 0.29) * 2.3; }
          if (name === '03_boundary_mask') {
            // This is the inner edge seen at the right/lower side of the orb.
            // It shares the shell's inward stroke so it does not look pinned in
            // place while the outer curve turns.
            alpha = 0.36 + dent * 0.58 + Math.sin(phase * 0.82 + 0.4) * 0.03;
            breathe = 1 - dent * 0.060;
            dx = Math.sin(shellTurn + 0.42) * 20.0 + sharedDx * 0.70;
            dy = Math.cos(shellTurn + 0.42) * 10.0 + sharedDy * 0.70;
          }
          if (name === '04_flow_layer') { alpha = 0.96 + Math.sin(phase + 0.7) * 0.30; breathe = 1 + Math.sin(phase * 0.46 + 0.4) * 0.016; dx = Math.sin(phase * 0.52 + 1.1) * 7.2; dy = Math.cos(phase * 0.47) * 4.3; }
          if (name === '05_flow_layer') { alpha = 0.92 + Math.sin(phase * 0.91 + 2.2) * 0.28; breathe = 1 + Math.cos(phase * 0.41) * 0.016; dx = Math.cos(phase * 0.49) * 6.8; dy = Math.sin(phase * 0.43 + 0.8) * 4.6; }
          if (name === '06_fine_ink_wash') { alpha = 0.70 + Math.sin(phase * 0.43 + 1.7) * 0.20; breathe = 1 + Math.sin(phase * 0.38 + 0.8) * 0.010; dx = Math.cos(phase * 0.34) * 2.2; dy = Math.sin(phase * 0.28) * 1.7; }
          if (name === '11_curvature_highlights') {
            // The shell follows the same low-amplitude turn as the inner volume.
            // Its larger, phase-locked drift makes the original curved highlight
            // visibly travel around the surface instead of reading as a fixed rim.
            alpha = 0.34 + dent * 0.58 + Math.sin(phase * 0.78 + 0.8) * 0.08;
            breathe = 1 + Math.sin(phase * 0.52) * 0.040;
            dx = Math.sin(shellTurn) * 36.0 + Math.sin(phase * 1.16 + 0.5) * 5.0;
            dy = Math.cos(shellTurn) * 24.0 + Math.cos(phase * 1.08) * 4.0;
          }
          if (name === '08_cool_point_glow') alpha = 0.88 + Math.sin(phase * 0.76 + 1.2) * 0.22;
          if (name === '10_warm_point_glow') alpha = 0.88 + Math.sin(phase * 0.69 + 3.0) * 0.22;
          const isShell = name === '11_curvature_highlights';
          const isBoundary = name === '03_boundary_mask';
          const shellShearX = isShell ? Math.sin(shellTurn) * 0.060 : 0;
          const shellShearY = isShell ? Math.cos(shellTurn) * 0.045 : 0;
          const shellInset = isShell ? 1 - dent * 0.075 : 1;
          const shellStretchX = isShell ? shellInset * (1 + Math.sin(shellTurn) * 0.070) : 1;
          const shellStretchY = isShell ? shellInset * (1 - Math.sin(shellTurn) * 0.050) : 1;
          const curveTurn = isShell ? sharedTurn + Math.sin(shellTurn) * 0.016 : sharedTurn + Math.sin(shellTurn + 0.42) * 0.010;
          const curveScale = isBoundary ? 1 - dent * 0.040 : 1;
          const boundaryScaleY = isBoundary ? 1 - dent * 0.024 : 1;
          ctx.save();
          ctx.translate(profile.center[0], profile.center[1]);
          ctx.rotate(curveTurn);
          ctx.scale(sharedBreathe * breathe * (isShell ? shellStretchX : curveScale), sharedBreathe * breathe * (isShell ? shellStretchY : boundaryScaleY));
          if (isShell) ctx.transform(1, shellShearY, shellShearX, 1, 0, 0);
          ctx.translate(-profile.center[0], -profile.center[1]);
          ctx.globalAlpha = clamp(isBoundary ? alpha * 1.55 : alpha, 0, 1);
          ctx.globalCompositeOperation = isShell ? 'screen' : 'source-over';
          ctx.filter = isShell ? `blur(${(1.2 + (1 - dent) * 2.4).toFixed(2)}px)` : (isBoundary ? `blur(${(0.8 + (1 - dent) * 1.4).toFixed(2)}px)` : 'none');
          const movingCurve = isShell ? (this.shellCurve || image) : (isBoundary ? (this.boundaryCurve || image) : image);
          // Keep every dynamic layer anchored to the same water mass. Still
          // motion is expressed by the existing field/opacity/shape response;
          // independent layer translation reads as image-plane sliding.
          ctx.drawImage(movingCurve, bx, by); ctx.restore();
          if (isShell) {
            // A broad moving mask makes the existing rim highlight travel in a
            // soft wave. It is clipped by the formal curve alpha, so it cannot
            // create a separate spot or ring outside the shell.
            if (this.shellWave) {
              const waveCtx = this.shellWave.getContext('2d');
              const [sx, sy, sw, sh] = profile.layerBounds[name];
              waveCtx.clearRect(0, 0, sw, sh);
              waveCtx.drawImage(this.shellCurve || image, 0, 0);
              waveCtx.globalCompositeOperation = 'destination-in';
              const waveX = sw * 0.5 + Math.cos(shellTurn * 0.82 + 0.5) * sw * 0.24;
              const waveY = sh * 0.5 + Math.sin(shellTurn * 0.82 + 0.5) * sh * 0.24;
              const wave = waveCtx.createRadialGradient(waveX, waveY, sw * 0.03, waveX, waveY, sw * 0.46);
              wave.addColorStop(0, 'rgba(255,255,255,0.90)');
              wave.addColorStop(0.42, 'rgba(255,255,255,0.48)');
              wave.addColorStop(1, 'rgba(255,255,255,0.04)');
              waveCtx.fillStyle = wave; waveCtx.fillRect(0, 0, sw, sh);
              ctx.save();
              ctx.translate(profile.center[0], profile.center[1]);
              ctx.rotate(curveTurn);
              ctx.scale(sharedBreathe * breathe * shellStretchX, sharedBreathe * breathe * shellStretchY);
              ctx.transform(1, shellShearY, shellShearX, 1, 0, 0);
              ctx.translate(-profile.center[0], -profile.center[1]);
              ctx.globalAlpha = 0.18 + dent * 0.18;
              ctx.globalCompositeOperation = 'screen';
              ctx.filter = `blur(${(2.2 + (1 - dent) * 1.8).toFixed(2)}px)`;
              ctx.drawImage(this.shellWave, bx, by);
              ctx.restore();
            }
            ctx.save();
            ctx.translate(profile.center[0], profile.center[1]);
            ctx.rotate(curveTurn);
            ctx.scale(sharedBreathe * breathe * shellStretchX, sharedBreathe * breathe * shellStretchY);
            if (isShell) ctx.transform(1, shellShearY, shellShearX, 1, 0, 0);
            ctx.translate(-profile.center[0], -profile.center[1]);
            ctx.globalAlpha = 0.08 + dent * 0.30 + (Math.sin(phase * 0.78 + 0.8) + 1) * 0.04;
            ctx.globalCompositeOperation = 'source-over';
            ctx.filter = `blur(${(1.4 + (1 - dent) * 1.8).toFixed(2)}px)`;
            ctx.drawImage(this.shellShade || image, bx, by);
            ctx.restore();
          }
        }
        ctx.restore();
        this.drawMaterial(layout, t);
      }
      const left = layout.cx - layout.hitRadius, top = layout.cy - layout.hitRadius, diameter = layout.hitRadius * 2;
      Object.assign(this.button.style, {left: `${left}px`, top: `${top}px`, width: `${diameter}px`, height: `${diameter}px`, borderRadius: '50%'});
      this.button.setAttribute('aria-label', '轻触水球，开始或继续冥想');
      this.host.dataset.visualState = this.state;
      this.frames++;
    }
    drawIdleMaterial(ctx, phase) {
      const [cx, cy] = profile.center;
      ctx.save();
      ctx.beginPath(); ctx.arc(cx, cy, profile.radius - 2, 0, Math.PI * 2); ctx.clip();
      const lightX = cx + Math.sin(phase * 0.52) * 42;
      const lightY = cy - 22 + Math.cos(phase * 0.41) * 20;
      const light = ctx.createRadialGradient(lightX, lightY, 8, lightX, lightY, 205);
      const lightPulse = 0.22 + (Math.sin(phase * 0.55) + 1) * 0.07;
      light.addColorStop(0, `rgba(235,255,252,${lightPulse.toFixed(3)})`);
      light.addColorStop(0.42, `rgba(167,232,228,${(lightPulse * 0.72).toFixed(3)})`);
      light.addColorStop(1, 'rgba(120,210,210,0)');
      ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = light; ctx.fillRect(0, 0, profile.frame[0], profile.frame[1]);
      const shadeX = cx - 42 + Math.cos(phase * 0.46 + 1.2) * 34;
      const shadeY = cy + 28 + Math.sin(phase * 0.37) * 22;
      const shade = ctx.createRadialGradient(shadeX, shadeY, 10, shadeX, shadeY, 185);
      const shadePulse = 0.14 + (Math.cos(phase * 0.48) + 1) * 0.05;
      shade.addColorStop(0, `rgba(24,100,113,${shadePulse.toFixed(3)})`);
      shade.addColorStop(0.55, `rgba(42,142,150,${(shadePulse * 0.58).toFixed(3)})`);
      shade.addColorStop(1, 'rgba(40,130,145,0)');
      ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = shade; ctx.fillRect(0, 0, profile.frame[0], profile.frame[1]);
      const bandX = cx + Math.sin(phase * 0.43 + 0.8) * 28;
      const bandY = cy + Math.cos(phase * 0.31) * 18;
      ctx.save(); ctx.translate(bandX, bandY); ctx.rotate(-0.38 + Math.sin(phase * 0.24) * 0.08);
      const band = ctx.createLinearGradient(-220, 0, 220, 0);
      band.addColorStop(0, 'rgba(255,255,255,0)'); band.addColorStop(0.44, 'rgba(214,255,250,0)');
      band.addColorStop(0.53, 'rgba(221,255,251,0.18)'); band.addColorStop(0.62, 'rgba(214,255,250,0)'); band.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = band;
      ctx.beginPath(); ctx.ellipse(0, 0, 245, 72 + Math.sin(phase * 0.38) * 7, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      ctx.restore();
    }
    hit(x, y) { const l = this.geometry; return !!l && Math.hypot(x - l.cx, y - l.cy) <= l.hitRadius; }
    inspect() {
      const l = this.geometry || this.layout();
      const effectiveVisualTime = this.now();
      return {renderer: profile.renderer, version: profile.version, state: this.state, ready: this.ready,
        idleAnimation: this.state === 'still' && !this.reducedMotion, idleTime: effectiveVisualTime, visualTime: effectiveVisualTime, idlePhase: this.idlePhase,
        lifecycle: {suspended: this.lifecycleSuspended, animationLoopRunning: this.animationLoopRunning,
          animationLoopStarts: this.animationLoopStarts, suspendCount: this.suspendCount, resumeCount: this.resumeCount},
        reducedMotion: this.reducedMotion, frame: {width: profile.frame[0], height: profile.frame[1]},
        center: {x: l.cx, y: l.cy}, radius: l.radius,
        hitRegion: {type: 'circle', x: l.cx, y: l.cy, radius: l.hitRadius},
        layerNames: [...profile.layerOrder], gravity: profile.gravity,
        material: {type:'webgl-flow-field', ready:!!this.material, debug:this.debugMaterial}, frames: this.frames};
    }
    destroy() {
      this.stopAnimationLoop(); this.observer.disconnect();
      document.removeEventListener('visibilitychange', this.onVisibilityChange);
      window.removeEventListener('pagehide', this.onPageHide);
      window.removeEventListener('pageshow', this.onPageShow);
      this.motionQuery?.removeEventListener?.('change', this.onMotionChange);
      this.canvas.remove(); this.materialCanvas.remove(); this.button.remove();
    }
  }
  window.MindIsleWaterball = Waterball;
  window.MINDISLE = window.MINDISLE || {};
  window.__MINDISLE__ = window.__MINDISLE__ || window.MINDISLE;
  window.MINDISLE.Waterball = Waterball;
})();
