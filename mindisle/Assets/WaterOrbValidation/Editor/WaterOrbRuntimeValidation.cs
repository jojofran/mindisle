using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class WaterOrbRuntimeValidation
{
    const string Root = "Assets/WaterOrbValidation";
    const string ShaderPath = Root + "/Runtime/WaterOrbRuntime.shader";
    const string MeshPath = Root + "/Runtime/Mesh/water_orb.obj";
    const string TextureRoot = Root + "/Runtime/Textures/";
    const int Width = 512;
    const int Height = 512;

    [Serializable]
    class Report
    {
        public string project;
        public string shader;
        public bool shaderFound;
        public bool shaderHasErrors;
        public string[] shaderMessages;
        public int vertices;
        public int triangles;
        public string[] captures;
        public string[] textureProperties;
    }

    [MenuItem("WaterOrb/Run Runtime Validation")]
    public static void Run()
    {
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        AssetDatabase.ImportAsset(ShaderPath, ImportAssetOptions.ForceSynchronousImport);
        AssetDatabase.ImportAsset(MeshPath, ImportAssetOptions.ForceSynchronousImport);
        ConfigureTexture(TextureRoot + "water_orb_normal.png", TextureImporterType.NormalMap);
        ConfigureTexture(TextureRoot + "water_orb_thickness.png", TextureImporterType.Default);
        ConfigureTexture(TextureRoot + "water_orb_flow_mask.png", TextureImporterType.Default);
        ConfigureTexture(TextureRoot + "water_orb_caustic.png", TextureImporterType.Default);
        ConfigureTexture(TextureRoot + "water_orb_emission.png", TextureImporterType.Default);

        var report = new Report
        {
            project = Application.unityVersion,
            shader = ShaderPath,
            captures = new List<string>().ToArray(),
            textureProperties = new[] { "_ThicknessTex", "_FlowMaskTex", "_CausticTex", "_NormalTex", "_EmissionTex" }
        };

        var shader = AssetDatabase.LoadAssetAtPath<Shader>(ShaderPath);
        report.shaderFound = shader != null;
        var messages = new List<string>();
        if (shader != null)
        {
            foreach (var message in ShaderUtil.GetShaderMessages(shader))
            {
                messages.Add(message.severity + ": " + message.message);
                if (message.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error) report.shaderHasErrors = true;
            }
        }
        report.shaderMessages = messages.ToArray();
        if (!report.shaderFound) report.shaderHasErrors = true;
        if (report.shaderHasErrors) throw new Exception("WaterOrbRuntime shader compile failed: " + string.Join(" | ", report.shaderMessages));

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var cameraObject = new GameObject("WaterOrb Validation Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.orthographic = true;
        camera.orthographicSize = 1.35f;
        camera.allowHDR = true;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.82f, 0.88f, 0.89f, 1f);
        camera.nearClipPlane = 0.01f;
        camera.farClipPlane = 20f;

        var lightObject = new GameObject("WaterOrb Validation Light");
        var light = lightObject.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 0.7f;
        light.color = new Color(0.92f, 0.98f, 1f);
        light.transform.rotation = Quaternion.Euler(35f, -25f, 0f);

        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(MeshPath);
        if (prefab == null) throw new Exception("Could not import validation mesh: " + MeshPath);
        var orb = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        orb.name = "WaterOrb Runtime Validation Orb";
        var renderer = orb.GetComponentInChildren<Renderer>();
        if (renderer == null) throw new Exception("Imported OBJ has no Renderer");
        var material = new Material(shader) { name = "WaterOrb Runtime Validation Material" };
        material.SetTexture("_ThicknessTex", LoadTexture("water_orb_thickness.png"));
        material.SetTexture("_FlowMaskTex", LoadTexture("water_orb_flow_mask.png"));
        material.SetTexture("_CausticTex", LoadTexture("water_orb_caustic.png"));
        material.SetTexture("_NormalTex", LoadTexture("water_orb_normal.png"));
        material.SetTexture("_EmissionTex", LoadTexture("water_orb_emission.png"));
        material.SetFloat("_FlowSpeed", 0f);
        material.SetFloat("_FlowDirectionScale", 1f);
        material.SetFloat("_FlowDistortion", 0.035f);
        renderer.sharedMaterial = material;

        var meshFilter = orb.GetComponentInChildren<MeshFilter>();
        report.vertices = meshFilter != null && meshFilter.sharedMesh != null ? meshFilter.sharedMesh.vertexCount : 0;
        report.triangles = meshFilter != null && meshFilter.sharedMesh != null ? meshFilter.sharedMesh.triangles.Length / 3 : 0;
        camera.targetTexture = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32);
        var captures = new List<string>();
        var outDir = Path.GetFullPath(Path.Combine(Application.dataPath, "WaterOrbValidation/Verification"));
        Directory.CreateDirectory(outDir);

        Capture(camera, "front", 0f, 0f, orb, outDir, captures);
        Capture(camera, "yaw_plus10", 10f, 0f, orb, outDir, captures);
        Capture(camera, "yaw_minus10", -10f, 0f, orb, outDir, captures);
        Capture(camera, "pitch_plus10", 0f, 10f, orb, outDir, captures);
        Capture(camera, "pitch_minus10", 0f, -10f, orb, outDir, captures);

        orb.transform.position = new Vector3(0.35f, 0.08f, 0.15f);
        Capture(camera, "moved", 0f, 0f, orb, outDir, captures);
        orb.transform.position = Vector3.zero;
        orb.transform.localScale = Vector3.one * 1.25f;
        Capture(camera, "scaled", 0f, 0f, orb, outDir, captures);
        orb.transform.localScale = Vector3.one;
        camera.backgroundColor = new Color(0.18f, 0.21f, 0.22f, 1f);
        Capture(camera, "background_changed", 0f, 0f, orb, outDir, captures);
        camera.backgroundColor = new Color(0.82f, 0.88f, 0.89f, 1f);
        light.intensity = 1.05f;
        light.color = new Color(1f, 0.82f, 0.68f);
        Capture(camera, "lighting_changed", 0f, 0f, orb, outDir, captures);

        report.captures = captures.ToArray();
        File.WriteAllText(Path.Combine(outDir, "runtime_validation_report.json"), JsonUtility.ToJson(report, true));
        EditorSceneManager.SaveScene(scene, Root + "/WaterOrbValidation.unity");
        Debug.Log("WATER_ORB_RUNTIME_VALIDATION_PASS shader=" + report.shaderFound + " errors=" + report.shaderHasErrors + " vertices=" + report.vertices + " triangles=" + report.triangles + " captures=" + captures.Count);
        UnityEngine.Object.DestroyImmediate(camera.targetTexture);
        UnityEngine.Object.DestroyImmediate(material);
        UnityEngine.Object.DestroyImmediate(orb);
        UnityEngine.Object.DestroyImmediate(cameraObject);
        UnityEngine.Object.DestroyImmediate(lightObject);
    }

    static void ConfigureTexture(string path, TextureImporterType type)
    {
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null) return;
        importer.textureType = type;
        importer.sRGBTexture = false;
        importer.mipmapEnabled = false;
        importer.wrapMode = TextureWrapMode.Repeat;
        importer.SaveAndReimport();
    }

    static Texture2D LoadTexture(string fileName) => AssetDatabase.LoadAssetAtPath<Texture2D>(TextureRoot + fileName);

    static void Capture(Camera camera, string name, float yaw, float pitch, GameObject orb, string outDir, List<string> captures)
    {
        orb.transform.rotation = Quaternion.identity;
        var rotation = Quaternion.Euler(pitch, yaw, 0f);
        camera.transform.position = rotation * new Vector3(0f, 0f, -4.5f);
        camera.transform.LookAt(Vector3.zero);
        camera.Render();
        RenderTexture.active = camera.targetTexture;
        var image = new Texture2D(Width, Height, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0, 0, Width, Height), 0, 0);
        image.Apply();
        var file = Path.Combine(outDir, name + ".png");
        File.WriteAllBytes(file, image.EncodeToPNG());
        captures.Add(file);
        RenderTexture.active = null;
        UnityEngine.Object.DestroyImmediate(image);
    }
}
