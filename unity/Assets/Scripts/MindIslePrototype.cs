using System;
using UnityEngine;

namespace MindIsle
{
    // One analytic water volume. The shader and hit test share the same polar boundary.
    [RequireComponent(typeof(Camera))]
    public sealed class MindIslePrototype : MonoBehaviour
    {
        public enum FocusState { still, transitioning, moving }
        [SerializeField] private FocusState state = FocusState.still;
        [SerializeField, Range(.8f, 1.2f)] private float transitionDuration = 1f;
        public FocusState CurrentState => state;
        public string CurrentStateName => state.ToString();
        public float TransitionProgress { get; private set; }
        public double FlowClock { get; private set; }
        public bool VisualReady => water && water.shader.isSupported;
        public bool Interactable => VisualReady && isActiveAndEnabled;
        public Vector2 GreenPoint { get; private set; }
        public Vector2 WarmPoint { get; private set; }
        public float ShapeAmount { get; private set; }
        public float TrailAmount { get; private set; }
        public int SurfaceInstanceId => surface ? surface.GetHashCode() : 0;
        public int MaterialInstanceId => water ? water.GetHashCode() : 0;
        public float RadiusUV => .32f * cam.aspect;
        public const float CenterY = .46f;
        public Camera FocusCamera => cam;
        const int Segments = 32;
        readonly Vector4[] greenTrail = new Vector4[Segments + 1];
        readonly Vector4[] warmTrail = new Vector4[Segments + 1];
        Material water;
        Material ribbonMaterial;
        GameObject surface;
        GameObject greenRibbonObject;
        GameObject warmRibbonObject;
        Mesh greenRibbonMesh;
        Mesh warmRibbonMesh;
        MeshFilter greenRibbonFilter;
        MeshFilter warmRibbonFilter;
        MeshRenderer greenRibbonRenderer;
        MeshRenderer warmRibbonRenderer;
        Camera cam;
        double breathClock;
        float shapeClock;
        bool suspended;
        bool previewFreezeClock;
        double previewClock;
        int width, height;

        void Awake() => Initialize();
        public void Initialize()
        {
            if (water) return;
            cam = GetComponent<Camera>();
            cam.orthographic = true; cam.orthographicSize = 5;
            cam.nearClipPlane = .1f; cam.farClipPlane = 30;
            cam.transform.SetPositionAndRotation(new Vector3(0,0,-10), Quaternion.identity);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(.94f,.956f,.951f);
            cam.allowHDR = false; cam.allowMSAA = false;
            Application.targetFrameRate = 60;
            Screen.orientation = ScreenOrientation.Portrait;
            surface = GameObject.CreatePrimitive(PrimitiveType.Quad);
            surface.name = "Water volume · procedural surface";
            surface.transform.SetParent(transform, false);
            surface.transform.localPosition = new Vector3(0,0,10);
            var collider = surface.GetComponent<Collider>();
            collider.enabled = false;
            if (Application.isPlaying) Destroy(collider); else DestroyImmediate(collider);
            water = new Material(Shader.Find("MindIsle/WaterBall"));
            surface.GetComponent<Renderer>().sharedMaterial = water;
            CreateRibbonResources();
            Layout(); ResetToStill();
        }
        void CreateRibbonResources()
        {
            ribbonMaterial = new Material(Shader.Find("MindIsle/FlowRibbon"));
            greenRibbonObject = CreateRibbonObject("Green flow ribbon", out greenRibbonFilter, out greenRibbonRenderer, out greenRibbonMesh);
            warmRibbonObject = CreateRibbonObject("Warm flow ribbon", out warmRibbonFilter, out warmRibbonRenderer, out warmRibbonMesh);
            greenRibbonRenderer.sharedMaterial = ribbonMaterial;
            warmRibbonRenderer.sharedMaterial = ribbonMaterial;
        }
        GameObject CreateRibbonObject(string objectName, out MeshFilter filter, out MeshRenderer renderer, out Mesh mesh)
        {
            var go = new GameObject(objectName);
            go.transform.SetParent(transform, false);
            go.transform.localPosition = new Vector3(0, 0, 10.05f);
            filter = go.AddComponent<MeshFilter>();
            renderer = go.AddComponent<MeshRenderer>();
            mesh = new Mesh { name = objectName + " mesh" };
            mesh.MarkDynamic();
            filter.sharedMesh = mesh;
            renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            renderer.enabled = false;
            return go;
        }
        void Layout()
        {
            // Native portrait ratios fill the screen; wide editor windows retain a portrait canvas.
            float aspect = (float)Screen.width / Mathf.Max(1,Screen.height);
            float portrait = Mathf.Min(aspect, .5625f);
            cam.rect = aspect > .5625f ? new Rect((1-portrait/aspect)*.5f,0,portrait/aspect,1) : new Rect(0,0,1,1);
            cam.aspect = portrait;
            surface.transform.localScale = new Vector3(10*portrait,10,1);
            width = Screen.width; height = Screen.height;
        }
        void Update()
        {
            if (width != Screen.width || height != Screen.height) Layout();
#if UNITY_EDITOR
            if (Input.GetKeyDown(KeyCode.R)) ResetToStill();
#endif
            if (!suspended)
            {
                if (Input.touchCount > 0)
                {
                    var touch = Input.GetTouch(0);
                    if (touch.phase == TouchPhase.Began) Tap(touch.position);
                }
                else if (Input.GetMouseButtonDown(0)) Tap(Input.mousePosition);
                Advance(Time.deltaTime);
            }
        }
        public void InitializeForPreview() { Initialize(); }
#if UNITY_EDITOR
        // Editor-only visual keyframe control. It freezes the procedural pose for
        // screenshot comparison without changing the runtime state contract.
        public void FreezePreviewVisual(double clock)
        {
            previewFreezeClock = true;
            previewClock = Math.Max(0, clock);
            Apply();
        }
        public void ReleasePreviewVisual()
        {
            previewFreezeClock = false;
            Apply();
        }
#endif
        public bool Contains(Vector2 screen)
        {
            if (!cam || !cam.pixelRect.Contains(screen)) return false;
            Vector3 uv = cam.ScreenToViewportPoint(screen);
            Vector2 q = new Vector2((uv.x-.5f)*cam.aspect, uv.y-CenterY)/RadiusUV;
            return q.magnitude <= Boundary(Mathf.Atan2(q.y,q.x));
        }
        public bool Tap(Vector2 screen)
        {
            if (!Interactable || state != FocusState.still || !Contains(screen)) return false;
            state = FocusState.transitioning; TransitionProgress = 0; FlowClock = 0;
            Apply(); return true;
        }
        public void Advance(float deltaTime)
        {
            if (!water || suspended || deltaTime < 0 || float.IsNaN(deltaTime) || float.IsInfinity(deltaTime)) return;
            breathClock += deltaTime;
            if (state != FocusState.still)
            {
                FlowClock += deltaTime;
                TransitionProgress = Mathf.Clamp01((float)(FlowClock / transitionDuration));
                if (TransitionProgress >= 1) state = FocusState.moving;
            }
            Apply();
        }
        public void ResetToStill()
        {
            state = FocusState.still; TransitionProgress = 0; FlowClock = 0; breathClock = 0;
            if (water) Apply();
        }
        void OnApplicationPause(bool paused) { suspended = paused; }
        public float Boundary(float a)
        {
            float deformation = .042f*Mathf.Sin(3*a+shapeClock*.47f) + .024f*Mathf.Sin(5*a-shapeClock*.31f) + .016f*Mathf.Cos(2*a+shapeClock*.23f) + .009f*Mathf.Sin(7*a+shapeClock*.17f);
            float p = TransitionProgress;
            float ripple = state == FocusState.transitioning ? Mathf.Sin(Mathf.PI*Mathf.InverseLerp(.27f,.9f,p))*.024f : 0;
            return 1+ShapeAmount*deformation + ripple*Mathf.Exp(-12*Mathf.Pow(Mathf.Sin(a-2.0f),2))*Mathf.Sin(p*13);
        }
        Vector2 Node(double clock, int index)
        {
            Vector2 inside = index == 0 ? new Vector2(-.34f,.43f) : new Vector2(.34f,-.43f);
            double moving = Math.Max(0,clock-transitionDuration);
            float a = (index == 0 ? 2.0f : 5.14f) + (float)(moving*(index == 0 ? .23 : -.185) % (Math.PI*2));
            float r = 1.08f+.032f*Mathf.Sin(a*3+index);
            Vector2 orbit = new Vector2(Mathf.Cos(a),Mathf.Sin(a))*r;
            if (clock >= transitionDuration) return orbit;
            float p = Mathf.Clamp01((float)(clock/transitionDuration));
            // A curved, continuously accelerating release with zero endpoint velocity.
            return CurvedRelease(inside,orbit,p,index);
        }
        void Apply()
        {
            float p = TransitionProgress;
            ShapeAmount = state == FocusState.still ? 0 : Mathf.SmoothStep(0,1,Mathf.InverseLerp(.27f,1,p));
            TrailAmount = state == FocusState.still ? 0 : Mathf.SmoothStep(0,1,Mathf.InverseLerp(.18f,.92f,p));
            double visualClock = previewFreezeClock ? previewClock : FlowClock;
            shapeClock = (float)(visualClock % 100000);
            float breath = (float)(breathClock % 100000);
            GreenPoint = state == FocusState.still ? new Vector2(-.34f+.003f*Mathf.Sin(breath*.31f),.43f+.004f*Mathf.Sin(breath*.47f)) : Node(visualClock,0);
            WarmPoint = state == FocusState.still ? new Vector2(.34f-.003f*Mathf.Sin(breath*.29f),-.43f+.004f*Mathf.Sin(breath*.41f)) : Node(visualClock,1);
            // Sample the actual node history: both ribbons always terminate at their corresponding node.
            if (state == FocusState.transitioning)
            {
                Vector2 g0 = new Vector2(-.34f,.43f), w0 = new Vector2(.34f,-.43f);
                for (int i=0;i<=Segments;i++)
                {
                    float s=i/(float)Segments;
                    Vector2 g=CurvedRelease(g0,GreenPoint,s,0), w=CurvedRelease(w0,WarmPoint,s,1);
                    greenTrail[i]=new Vector4(g.x,g.y,s,0); warmTrail[i]=new Vector4(w.x,w.y,s,0);
                }
            }
            else
            {
                // Moving ribbons sample only the continuous orbital portion; the release is already visible during transitioning.
                double span = Math.Min(8,Math.Max(0,FlowClock-transitionDuration));
                for (int i=0;i<=Segments;i++)
                {
                    float s=i/(float)Segments;
                    Vector2 g=Node(Math.Max(0,visualClock-span*s),0), w=Node(Math.Max(0,visualClock-span*s),1);
                    greenTrail[i]=new Vector4(g.x,g.y,s,0); warmTrail[i]=new Vector4(w.x,w.y,s,0);
                }
            }
            water.SetFloat("_Aspect",cam.aspect); water.SetFloat("_Radius",RadiusUV);
            water.SetFloat("_State",(float)state); water.SetFloat("_Progress",p);
            water.SetFloat("_Clock",shapeClock); water.SetFloat("_Breath",breath);
            water.SetFloat("_Shape",ShapeAmount); water.SetFloat("_Trail",state == FocusState.moving ? TrailAmount*.24f : TrailAmount);
            water.SetVector("_Green",GreenPoint); water.SetVector("_Warm",WarmPoint);
            water.SetVectorArray("_GreenTrail",greenTrail); water.SetVectorArray("_WarmTrail",warmTrail);
            UpdateRibbonMeshes();
        }
        static Vector2 CurvedRelease(Vector2 start, Vector2 end, float t, int index)
        {
            float eased = t*t*(3-2*t);
            Vector2 chord = end-start;
            Vector2 normal = new Vector2(-chord.y,chord.x).normalized;
            float bend = (index == 0 ? .16f : -.13f) * Mathf.Sin(Mathf.PI*t) * (0.72f + .28f*t);
            return Vector2.Lerp(start,end,eased) + normal*bend;
        }
        void UpdateRibbonMeshes()
        {
            bool visible = state == FocusState.moving && TrailAmount > .001f;
            if (greenRibbonRenderer) greenRibbonRenderer.enabled = visible;
            if (warmRibbonRenderer) warmRibbonRenderer.enabled = visible;
            if (!visible) return;
            BuildRibbon(greenRibbonMesh, greenTrail, false);
            BuildRibbon(warmRibbonMesh, warmTrail, true);
        }
        void BuildRibbon(Mesh mesh, Vector4[] trail, bool warm)
        {
            const int count = Segments + 1;
            var vertices = new Vector3[count * 2];
            var colors = new Color[count * 2];
            var uv = new Vector2[count * 2];
            var triangles = new int[(count - 1) * 6];
            float scale = 10f * RadiusUV;
            for (int i = 0; i < count; i++)
            {
                Vector2 p = new Vector2(trail[i].x, trail[i].y);
                Vector2 prev = i == 0 ? p : new Vector2(trail[i - 1].x, trail[i - 1].y);
                Vector2 next = i == count - 1 ? p : new Vector2(trail[i + 1].x, trail[i + 1].y);
                Vector2 tangent = (next - prev).normalized;
                if (tangent.sqrMagnitude < .001f) tangent = Vector2.right;
                Vector2 normal = new Vector2(-tangent.y, tangent.x);
                float s = i / (float)(count - 1);
                float width = (warm ? .040f : .050f) + (warm ? .100f : .135f) * Mathf.Sin(s * Mathf.PI);
                width *= 1f - Mathf.SmoothStep(.82f, 1f, s);
                Vector2 center = p * scale;
                Vector2 offset = normal * width * scale;
                vertices[i * 2] = new Vector3(center.x - offset.x, center.y - offset.y, 0);
                vertices[i * 2 + 1] = new Vector3(center.x + offset.x, center.y + offset.y, 0);
                float alpha = Mathf.Pow(Mathf.Clamp01(s), 1.05f) * (warm ? .70f : .94f);
                colors[i * 2] = new Color(warm ? .94f : .32f, warm ? .66f : .76f, warm ? .47f : .70f, alpha);
                colors[i * 2 + 1] = colors[i * 2];
                uv[i * 2] = new Vector2(0, s);
                uv[i * 2 + 1] = new Vector2(1, s);
                if (i < count - 1)
                {
                    int t = i * 6, v = i * 2;
                    triangles[t] = v; triangles[t + 1] = v + 2; triangles[t + 2] = v + 1;
                    triangles[t + 3] = v + 1; triangles[t + 4] = v + 2; triangles[t + 5] = v + 3;
                }
            }
            mesh.Clear();
            mesh.vertices = vertices;
            mesh.colors = colors;
            mesh.uv = uv;
            mesh.triangles = triangles;
            mesh.RecalculateBounds();
        }
        void OnDestroy()
        {
            if (water) Destroy(water);
            if (ribbonMaterial) Destroy(ribbonMaterial);
            if (greenRibbonMesh) Destroy(greenRibbonMesh);
            if (warmRibbonMesh) Destroy(warmRibbonMesh);
        }
    }
}
