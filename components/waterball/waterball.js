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
      this.productState = state;
      this.interactionVisualState = 'clear';
      this.activationCommitted = false;
      this.activationCount = 0;
      this.gesture = {active: false, valid: false, startedInside: false, leftHitRadius: false, committed: false, pointerId: null};
      this.pressPoint = null;
      this.pressAmount = 0;
      this.formationProgress = 0;
      this.formationStartedAt = 0;
      this.formationFrom = 0;
      this.onActivate = onActivate;
      this.ready = false;
      this.frames = 0;
      this.idleEpoch = performance.now();
      this.idleTime = 0;
      // Frozen base for the single effective visual-time authority. The
      // active segment is derived from idleEpoch; idleTime/idlePhase are views.
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
      this.button.addEventListener('pointerdown', event => this.pointerDown(event));
      this.button.addEventListener('pointermove', event => this.pointerMove(event));
      this.button.addEventListener('pointerup', event => this.pointerUp(event));
      this.button.addEventListener('pointercancel', event => this.cancelGesture(event));
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
      this.buildSilhouetteMask();
      this.staticComposite = await loadImage(profile.assetRoot + profile.staticComposite);
      this.buildClearComposite();
      this.prepareMaterialTexture();
      this.staticCompositeCanvas = document.createElement('canvas');
      this.staticCompositeCanvas.width = profile.frame[0]; this.staticCompositeCanvas.height = profile.frame[1];
      const compositeCtx = this.staticCompositeCanvas.getContext('2d');
      compositeCtx.drawImage(this.staticComposite, 0, 0);
      compositeCtx.globalCompositeOperation = 'destination-in';
      compositeCtx.drawImage(this.silhouetteMaskCanvas, 0, 0);
      this.plate = document.createElement('canvas');
      this.plate.width = profile.frame[0]; this.plate.height = profile.frame[1];
      const plateCtx = this.plate.getContext('2d');
      plateCtx.drawImage(this.images['00_background_plate'], 0, 0);
      plateCtx.globalCompositeOperation = 'destination-in';
      plateCtx.drawImage(this.silhouetteMaskCanvas, 0, 0);
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
        uniform vec2 u_resolution, u_center; uniform float u_radius, u_time, u_strength; uniform sampler2D u_texture, u_mask;
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
          float silhouette=texture2D(u_mask,uv0).a;
          float a=edge*pointKeep*u_strength*(0.16+0.22*light)*silhouette;
          gl_FragColor=vec4(col,a);
        }`;
      const compile=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);return s;};
      const program=gl.createProgram(); gl.attachShader(program,compile(gl.VERTEX_SHADER,vertex)); gl.attachShader(program,compile(gl.FRAGMENT_SHADER,fragment)); gl.linkProgram(program);
      const buffer=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buffer); gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      this.material={gl,program,buffer,p:gl.getAttribLocation(program,'p'),resolution:gl.getUniformLocation(program,'u_resolution'),center:gl.getUniformLocation(program,'u_center'),radius:gl.getUniformLocation(program,'u_radius'),time:gl.getUniformLocation(program,'u_time'),strength:gl.getUniformLocation(program,'u_strength'),texture:gl.getUniformLocation(program,'u_texture'),mask:gl.getUniformLocation(program,'u_mask')};
    }
    prepareMaterialTexture() {
      if (!this.material || !this.staticComposite) return;
      const gl=this.material.gl; this.material.textureObject=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,this.material.textureObject); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,this.staticComposite);
      this.material.maskObject=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,this.material.maskObject); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,this.silhouetteMaskCanvas); gl.bindTexture(gl.TEXTURE_2D,null);
    }
    buildClearComposite() {
      const [width, height] = profile.frame;
      this.clearCompositeCanvas = document.createElement('canvas');
      this.clearCompositeCanvas.width = width; this.clearCompositeCanvas.height = height;
      const ctx = this.clearCompositeCanvas.getContext('2d');
      ctx.drawImage(this.images['00_background_plate'], 0, 0);
      ctx.drawImage(this.images['01_outer_film'], 0, 0);
      ctx.globalAlpha = 0.34; ctx.drawImage(this.images['02_internal_cyan_volume'], 0, 0);
      ctx.globalAlpha = 0.24; ctx.drawImage(this.images['06_fine_ink_wash'], 0, 0);
      ctx.globalAlpha = 0.42; ctx.globalCompositeOperation = 'screen'; ctx.drawImage(this.images['11_curvature_highlights'], 0, 0);
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'destination-in'; ctx.drawImage(this.silhouetteMaskCanvas, 0, 0);
      ctx.globalCompositeOperation = 'source-over';
    }
    drawMaterial(layout,time,strengthValue = 0.78) {
      if (!this.material || this.reducedMotion) { if (this.material) this.material.gl.clear(this.material.gl.COLOR_BUFFER_BIT); return; }
      const {gl,program,buffer,p,resolution,center,radius,strength,texture,textureObject,maskObject} = this.material;
      const dpr=Math.min(window.devicePixelRatio||1,2); this.materialCanvas.width=Math.max(1,Math.round(layout.width*dpr)); this.materialCanvas.height=Math.max(1,Math.round(layout.height*dpr));
      gl.viewport(0,0,this.materialCanvas.width,this.materialCanvas.height); gl.clearColor(0,0,0,0); gl.clear(gl.COLOR_BUFFER_BIT); gl.useProgram(program); gl.bindBuffer(gl.ARRAY_BUFFER,buffer); gl.enableVertexAttribArray(p); gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D,textureObject); gl.uniform1i(texture,0); gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D,maskObject); gl.uniform1i(this.material.mask,1); gl.uniform2f(resolution,this.materialCanvas.width,this.materialCanvas.height); gl.uniform2f(center,layout.cx*dpr,(layout.height-layout.cy)*dpr); gl.uniform1f(radius,layout.radius*dpr); gl.uniform1f(this.material.time,time); gl.uniform1f(strength,this.debugMaterial?2.4:strengthValue);
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
    buildSilhouetteMask() {
      const [width, height] = profile.frame;
      this.silhouetteMaskCanvas = document.createElement('canvas');
      this.silhouetteMaskCanvas.width = width; this.silhouetteMaskCanvas.height = height;
      const ctx = this.silhouetteMaskCanvas.getContext('2d', {willReadFrequently: true});
      const source = this.images[profile.silhouetteAuthority.layer];
      if (!source) return;
      ctx.drawImage(source, 0, 0);
      const image = ctx.getImageData(0, 0, width, height);
      const threshold = profile.silhouetteAuthority.threshold;
      // The formal outer-film layer is a translucent ring, so turn its
      // per-row alpha extents into a filled body mask. This stays derived
      // from the atlas edge and avoids replacing it with a radial primitive.
      for (let y = 0; y < height; y++) {
        let left = width, right = -1, edgeAlpha = 0;
        for (let x = 0; x < width; x++) {
          const i = (y * width + x) * 4, alpha = image.data[i + 3];
          if (alpha >= threshold) { left = Math.min(left, x); right = Math.max(right, x); edgeAlpha = Math.max(edgeAlpha, alpha); }
        }
        for (let x = 0; x < width; x++) {
          const i = (y * width + x) * 4;
          image.data[i] = 255; image.data[i + 1] = 255; image.data[i + 2] = 255;
          image.data[i + 3] = right >= left && x >= left && x <= right ? (x === left || x === right ? edgeAlpha : 255) : 0;
        }
      }
      ctx.putImageData(image, 0, 0);
      this.silhouetteMaskReady = true;
    }
    setState(state) {
      if (!['still', 'transitioning', 'moving'].includes(state)) throw new Error('Unsupported ProductState: ' + state);
      if (state !== 'still') throw new Error('Activation / moving is not implemented in Slice 0');
      this.productState = state; this.state = state; this.interactionVisualState = 'clear'; this.draw();
    }
    localPoint(event) {
      const rect = this.host.getBoundingClientRect();
      return {x: event.clientX - rect.left, y: event.clientY - rect.top};
    }
    pointerDown(event) {
      if (!this.ready || this.lifecycleSuspended || this.gesture.active) return;
      const point = this.localPoint(event);
      if (!this.hit(point.x, point.y)) return;
      this.gesture = {active: true, valid: true, startedInside: true, leftHitRadius: false, committed: false, pointerId: event.pointerId};
      this.pressPoint = point;
      this.pressAmount = this.reducedMotion ? 1 : 0;
      this.formationProgress = 0;
      this.formationStartedAt = performance.now();
      this.formationFrom = 0;
      this.interactionVisualState = 'press';
      this.button.setPointerCapture?.(event.pointerId);
      event.preventDefault();
      this.draw();
    }
    pointerMove(event) {
      if (!this.gesture.active || event.pointerId !== this.gesture.pointerId) return;
      const point = this.localPoint(event);
      this.pressPoint = point;
      if (!this.hit(point.x, point.y)) {
        this.gesture.valid = false;
        this.gesture.leftHitRadius = true;
        this.interactionVisualState = 'clear';
        this.pressAmount = 0;
      }
      event.preventDefault();
      this.draw();
    }
    pointerUp(event) {
      if (!this.gesture.active || event.pointerId !== this.gesture.pointerId) return;
      const point = this.localPoint(event);
      const valid = this.gesture.valid && !this.gesture.leftHitRadius && this.hit(point.x, point.y);
      if (valid && !this.gesture.committed) this.commitActivation(point);
      else this.clearGesture();
      this.button.releasePointerCapture?.(event.pointerId);
      event.preventDefault();
    }
    commitActivation(point) {
      this.gesture.committed = true;
      this.gesture.active = false;
      this.activationCommitted = true;
      this.formationFrom = this.formationProgress;
      this.formationStartedAt = performance.now();
      this.activationCount++;
      this.pressPoint = null;
      this.pressAmount = 0;
      this.interactionVisualState = 'activated';
      const detail = {state: this.productState, point, activationCount: this.activationCount};
      this.host.dispatchEvent(new CustomEvent('water-orb-hit', {bubbles: true, detail}));
      this.dispatchEvent(new CustomEvent('water-orb-hit', {detail}));
      this.onActivate(detail);
      this.draw();
      // The marker is observable for the current turn, then settles into the
      // committed still-pose without inventing a new ProductState.
      queueMicrotask(() => {
        if (this.interactionVisualState === 'activated') {
          this.interactionVisualState = 'clear';
          this.draw();
        }
      });
    }
    clearGesture() {
      this.gesture = {active: false, valid: false, startedInside: false, leftHitRadius: false, committed: false, pointerId: null};
      this.pressPoint = null;
      this.pressAmount = 0;
      this.formationProgress = 0;
      this.formationFrom = 0;
      this.interactionVisualState = 'clear';
      this.draw();
    }
    cancelGesture(event) {
      if (!this.gesture.active) return;
      if (event?.pointerId != null && event.pointerId !== this.gesture.pointerId) return;
      this.clearGesture();
    }
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
      this.cancelGesture();
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
      this.productState = 'still';
      this.interactionVisualState = 'clear';
      this.activationCommitted = false;
      this.activationCount = 0;
      this.gesture = {active: false, valid: false, startedInside: false, leftHitRadius: false, committed: false, pointerId: null};
      this.pressPoint = null;
      this.pressAmount = 0;
      this.formationProgress = 0;
      this.formationFrom = 0;
      this.draw();
      this.startAnimationLoop();
      this.dispatchEvent(new CustomEvent('lifecycle', {detail: {type: 'reset', idleTime: 0}}));
    }
    effectiveVisualTime() {
      if (this.reducedMotion) return this.visualTime;
      const activeSegment = this.lifecycleSuspended ? 0 : (performance.now() - this.idleEpoch) / 1000;
      return Math.max(0, this.visualTime + activeSegment);
    }
    now() { return this.effectiveVisualTime(); }
    draw() {
      const layout = this.layout();
      if (!layout.width || !layout.height) return;
      this.geometry = layout;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.canvas.width = Math.max(1, Math.round(layout.width * dpr));
      this.canvas.height = Math.max(1, Math.round(layout.height * dpr));
      let ctx = this.canvas.getContext('2d');
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
        if (this.interactionVisualState === 'press' && !this.activationCommitted) {
          this.pressAmount = this.reducedMotion ? 1 : clamp((performance.now() - this.formationStartedAt) / 280, 0, 1);
          this.formationProgress = this.pressAmount;
        } else if (this.activationCommitted && this.formationProgress < 1) {
          if (this.reducedMotion) this.formationProgress = 1;
          else {
          const from = this.formationFrom;
          this.formationProgress = clamp(from + (performance.now() - this.formationStartedAt) / 180 * (1 - from), from, 1);
          }
        }
        const formation = this.formationProgress;
        ctx.save();
        ctx.translate(layout.left, layout.top);
        ctx.scale(layout.scale, layout.scale);
        const clearStill = formation <= 0.001;
        const density = clearStill ? 0.40 : formation;
        ctx.globalAlpha = 1;
        ctx.drawImage(this.clearCompositeCanvas || this.staticCompositeCanvas, 0, 0);
        if (formation > 0) {
          ctx.globalAlpha = formation;
          ctx.drawImage(this.staticCompositeCanvas, 0, 0);
        }
        ctx.globalAlpha = 1;
        const mainCtx = ctx;
        if (!this.dynamicBodyCanvas || this.dynamicBodyCanvas.width !== this.canvas.width || this.dynamicBodyCanvas.height !== this.canvas.height) {
          this.dynamicBodyCanvas = document.createElement('canvas');
          this.dynamicBodyCanvas.width = this.canvas.width;
          this.dynamicBodyCanvas.height = this.canvas.height;
        }
        const bodyCtx = this.dynamicBodyCanvas.getContext('2d');
        bodyCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
        bodyCtx.clearRect(0, 0, layout.width, layout.height);
        bodyCtx.save();
        bodyCtx.translate(layout.left, layout.top);
        bodyCtx.scale(layout.scale, layout.scale);
        ctx = bodyCtx;
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
          if (clearStill) continue;
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
          ctx.globalAlpha = clamp((isBoundary ? alpha * 1.55 : alpha) * density, 0, 1);
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
        // The dynamic body result is clipped once, after all body layers have
        // been composited. Orbit elements will use a separate pass later.
        ctx.globalCompositeOperation = 'destination-in';
        ctx.drawImage(this.silhouetteMaskCanvas, 0, 0);
        ctx.restore();
        ctx = mainCtx;
        ctx.restore();
        ctx.drawImage(this.dynamicBodyCanvas, 0, 0, layout.width, layout.height);
        if (formation < 1) this.drawClearStill(ctx, layout, formation);
        if (this.interactionVisualState === 'press' && this.pressPoint) this.drawPressOverlay(ctx, layout);
        this.drawMaterial(layout, t, clearStill ? 0.08 : 0.78);
      }
      const left = layout.cx - layout.hitRadius, top = layout.cy - layout.hitRadius, diameter = layout.hitRadius * 2;
      Object.assign(this.button.style, {left: `${left}px`, top: `${top}px`, width: `${diameter}px`, height: `${diameter}px`, borderRadius: '50%'});
      this.button.setAttribute('aria-label', '轻触水球，开始或继续冥想');
      this.host.dataset.visualState = this.state;
      this.frames++;
    }
    drawPressOverlay(ctx, layout) {
      const p = this.pressPoint;
      if (!p) return;
      const dx = p.x - layout.cx, dy = p.y - layout.cy;
      const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, layout.radius * 0.34);
      gradient.addColorStop(0, 'rgba(156,235,226,0.18)');
      gradient.addColorStop(0.48, 'rgba(84,176,181,0.08)');
      gradient.addColorStop(1, 'rgba(84,176,181,0)');
      ctx.save();
      ctx.beginPath(); ctx.arc(layout.cx, layout.cy, layout.radius, 0, Math.PI * 2); ctx.clip();
      ctx.globalAlpha = this.pressAmount;
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = gradient;
      ctx.fillRect(p.x - layout.radius * 0.38, p.y - layout.radius * 0.38, layout.radius * 0.76, layout.radius * 0.76);
      ctx.globalCompositeOperation = 'multiply';
      ctx.globalAlpha = this.pressAmount * 0.42;
      ctx.fillStyle = `rgba(25,105,115,${(0.10 + Math.min(1, Math.hypot(dx, dy) / layout.radius) * 0.05).toFixed(3)})`;
      ctx.beginPath(); ctx.ellipse(p.x + layout.radius * 0.035, p.y + layout.radius * 0.045, layout.radius * 0.10, layout.radius * 0.065, -0.25, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
    drawClearStill(ctx, layout, formation = 0) {
      const {cx, cy, radius} = layout;
      const residual = 1 - formation;
      ctx.save();
      ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.clip();
      const volume = ctx.createRadialGradient(cx - radius * 0.08, cy - radius * 0.02, radius * 0.06, cx, cy, radius * 0.84);
      volume.addColorStop(0, 'rgba(102,190,194,0.22)');
      volume.addColorStop(0.52, 'rgba(118,202,204,0.13)');
      volume.addColorStop(1, 'rgba(118,202,204,0)');
      ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = volume;
      ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
      ctx.globalCompositeOperation = 'source-over';
      // Clear the two diagonal still-pose cores with the same pale water tint,
      // then place a quieter, symmetric pair across the middle of the sphere.
      const wash = (x, y, r, color) => {
        const g = ctx.createRadialGradient(x, y, 0, x, y, r);
        g.addColorStop(0, color); g.addColorStop(0.55, 'rgba(142,211,211,0.34)'); g.addColorStop(1, 'rgba(142,211,211,0)');
        ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
        ctx.globalCompositeOperation = 'source-over';
      };
      const coolOld = {x: cx - radius * 0.40, y: cy - radius * 0.45};
      const warmOld = {x: cx + radius * 0.50, y: cy + radius * 0.45};
      wash(coolOld.x, coolOld.y, radius * 0.24, `rgba(108,184,190,${(0.82 * residual).toFixed(3)})`);
      wash(warmOld.x, warmOld.y, radius * 0.24, `rgba(108,184,190,${(0.82 * residual).toFixed(3)})`);
      const [clearCool, clearWarm] = profile.clearCorePositions;
      const left = {x: cx + (clearCool[0] + (profile.gravity.points[0].position[0] - clearCool[0]) * formation) * radius, y: cy - (clearCool[1] + (profile.gravity.points[0].position[1] - clearCool[1]) * formation) * radius};
      const right = {x: cx + (clearWarm[0] + (profile.gravity.points[1].position[0] - clearWarm[0]) * formation) * radius, y: cy - (clearWarm[1] + (profile.gravity.points[1].position[1] - clearWarm[1]) * formation) * radius};
      const point = (p, rgb) => {
        const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, radius * 0.105);
        glow.addColorStop(0, `rgba(${rgb},0.62)`); glow.addColorStop(0.28, `rgba(${rgb},0.28)`); glow.addColorStop(1, `rgba(${rgb},0)`);
        ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = residual; ctx.fillStyle = glow;
        ctx.fillRect(p.x - radius * 0.12, p.y - radius * 0.12, radius * 0.24, radius * 0.24);
        ctx.globalCompositeOperation = 'source-over';
        ctx.beginPath(); ctx.arc(p.x, p.y, radius * 0.030, 0, Math.PI * 2); ctx.fillStyle = `rgba(${rgb},0.88)`; ctx.fill();
      };
      point(left, '91,184,195');
      point(right, '240,181,136');
      ctx.restore();
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
    bodyMaskDiagnostics() {
      if (!this.dynamicBodyCanvas || !this.silhouetteMaskCanvas || !this.geometry) return {ready: false, outsidePixelCount: null, maxOutsideAlpha: null};
      const {width, height, left, top, scale} = this.geometry;
      const mask = document.createElement('canvas'); mask.width = this.dynamicBodyCanvas.width; mask.height = this.dynamicBodyCanvas.height;
      const maskCtx = mask.getContext('2d'); const dpr = Math.min(window.devicePixelRatio || 1, 2);
      maskCtx.setTransform(dpr, 0, 0, dpr, 0, 0); maskCtx.translate(left, top); maskCtx.scale(scale, scale); maskCtx.drawImage(this.silhouetteMaskCanvas, 0, 0);
      const bodyData = this.dynamicBodyCanvas.getContext('2d').getImageData(0, 0, this.dynamicBodyCanvas.width, this.dynamicBodyCanvas.height).data;
      const maskData = maskCtx.getImageData(0, 0, mask.width, mask.height).data;
      let outsidePixelCount = 0, maxOutsideAlpha = 0;
      for (let i = 3; i < bodyData.length; i += 4) {
        if (bodyData[i] > 0 && maskData[i] === 0) { outsidePixelCount++; maxOutsideAlpha = Math.max(maxOutsideAlpha, bodyData[i]); }
      }
      return {ready: true, outsidePixelCount, maxOutsideAlpha, source: profile.silhouetteAuthority.layer};
    }
    inspect() {
      const l = this.geometry || this.layout();
      const effectiveVisualTime = this.now();
      return {renderer: profile.renderer, version: profile.version, state: this.state,
        productState: this.productState, ProductState: this.productState,
        interactionVisualState: this.interactionVisualState, InteractionVisualState: this.interactionVisualState,
        ready: this.ready, VisualReady: this.ready,
        idleAnimation: this.state === 'still' && !this.reducedMotion, idleTime: effectiveVisualTime, visualTime: effectiveVisualTime,
        effectiveVisualTime, transitionProgress: null, movingPhase: null, idlePhase: this.idlePhase,
        lifecycle: {suspended: this.lifecycleSuspended, animationLoopRunning: this.animationLoopRunning,
          animationLoopStarts: this.animationLoopStarts, suspendCount: this.suspendCount, resumeCount: this.resumeCount},
        reducedMotion: this.reducedMotion, frame: {width: profile.frame[0], height: profile.frame[1]},
        center: {x: l.cx, y: l.cy}, radius: l.radius, hitRadius: l.hitRadius,
        hitRegion: {type: 'circle', x: l.cx, y: l.cy, radius: l.hitRadius},
        silhouette: {authority: profile.silhouetteAuthority, maskReady: !!this.silhouetteMaskReady, bodyDomain: profile.bodyDomain, orbitDomain: profile.orbitDomain},
        silhouetteMaskReady: !!this.silhouetteMaskReady,
        silhouetteMaskSource: profile.silhouetteAuthority.layer,
        activationCommitted: this.activationCommitted,
        activationCount: this.activationCount,
        activationCommitCount: this.activationCount,
        visualPose: this.activationCommitted
          ? (this.formationProgress < 1 ? 'forming-still-pose' : 'still-pose')
          : (this.interactionVisualState === 'press' ? 'press-forming' : 'clear-still'),
        formationProgress: this.formationProgress,
        gestureActive: this.gesture.active,
        gestureValid: this.gesture.valid,
        gestureStartedInside: this.gesture.startedInside,
        gestureLeftHitRadius: this.gesture.leftHitRadius,
        bodyDomainReady: !!this.silhouetteMaskReady && !!this.dynamicBodyCanvas,
        bodyDomainMaskDiagnostics: this.bodyMaskDiagnostics(),
        orbitDomainReady: false,
        orbitDomain: {ready: false, status: 'notImplemented'},
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
