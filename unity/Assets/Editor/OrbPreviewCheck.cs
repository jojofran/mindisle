using System;
using System.IO;
using MindIsle;
using UnityEditor;
using UnityEngine;

public static class OrbPreviewCheck
{
    [MenuItem("MindIsle/Run Orb Preview Check")]
    public static void RunFromMenu() => Run();
    public static void Run()
    {
        var obj = new GameObject("Preview Camera", typeof(Camera));
        var app = obj.AddComponent<MindIslePrototype>();
        app.InitializeForPreview();
        var cam = obj.GetComponent<Camera>();
        var rt = new RenderTexture(780, 1688, 24);
        cam.targetTexture = rt;
        cam.rect = new Rect(0, 0, 1, 1);
        cam.aspect = 390f / 844f;
        var path = Path.GetFullPath(Path.Combine(Application.dataPath, "../../verification"));
        Directory.CreateDirectory(path);
        Capture(cam, rt, Path.Combine(path, "still-state.png"));
        Debug.Log($"ORB_CAPTURE still state={app.CurrentState} progress={app.TransitionProgress:0.000} trail={app.TrailAmount:0.000}");
        if (app.CurrentState != MindIslePrototype.FocusState.still) throw new Exception("Initial state is not still");
        var center = cam.ViewportToScreenPoint(new Vector3(.5f, .48f, 0));
        if (!app.Tap(center) || app.CurrentState != MindIslePrototype.FocusState.transitioning) throw new Exception("Orb tap did not enter transitioning");
        app.Advance(0.5f);
        Capture(cam, rt, Path.Combine(path, "transitioning-mid.png"));
        Debug.Log($"ORB_CAPTURE transitioning state={app.CurrentState} progress={app.TransitionProgress:0.000} trail={app.TrailAmount:0.000}");
        if (app.CurrentState != MindIslePrototype.FocusState.transitioning) throw new Exception("Mid transition state incorrect");
        app.Advance(0.6f);
        app.Advance(4f);
        app.FreezePreviewVisual(5.6);
        Capture(cam, rt, Path.Combine(path, "moving-keyframe.png"));
        Debug.Log($"ORB_KEYFRAME moving state={app.CurrentState} progress={app.TransitionProgress:0.000} trail={app.TrailAmount:0.000}");
        app.ReleasePreviewVisual();
        app.Advance(0.5f);
        Capture(cam, rt, Path.Combine(path, "moving-state.png"));
        Debug.Log($"ORB_CAPTURE moving state={app.CurrentState} progress={app.TransitionProgress:0.000} trail={app.TrailAmount:0.000}");
        if (app.CurrentState != MindIslePrototype.FocusState.moving) throw new Exception("Transition did not finish moving");
        var before = app.FlowClock;
        int surfaceId = app.SurfaceInstanceId, materialId = app.MaterialInstanceId;
        app.ReleasePreviewVisual();
        app.Advance(10f);
        if (app.FlowClock <= before) throw new Exception("Moving state did not advance");
        if (app.Tap(cam.ViewportToScreenPoint(new Vector3(.05f, .95f, 0)))) throw new Exception("Outside tap changed state");
        app.ResetToStill();
        if (app.CurrentState != MindIslePrototype.FocusState.still || app.FlowClock != 0 || app.TrailAmount != 0) throw new Exception("Reset failed");
        if (app.SurfaceInstanceId != surfaceId || app.MaterialInstanceId != materialId) throw new Exception("Reset recreated runtime resources");
        var errors = ShaderUtil.GetShaderMessages(Shader.Find("MindIsle/WaterBall"));
        foreach (var e in errors) if (e.severity.ToString() == "Error") throw new Exception(e.message);
        Debug.Log("ORB_CHECK_PASS: still -> transitioning -> moving -> reset; runtime captures rendered; shader checked.");
        cam.targetTexture = null;
        rt.Release();
        UnityEngine.Object.DestroyImmediate(obj);
    }

    static void Capture(Camera cam, RenderTexture rt, string file)
    {
        cam.Render();
        RenderTexture.active = rt;
        var image = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        image.Apply();
        File.WriteAllBytes(file, image.EncodeToPNG());
        RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(image);
    }
}
