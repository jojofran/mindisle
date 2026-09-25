Shader "MindIsle/WaterOrbRuntime"
{
    Properties
    {
        _ThicknessTex ("Thickness", 2D) = "gray" {}
        _FlowMaskTex ("Flow Mask", 2D) = "gray" {}
        _CausticTex ("Caustic", 2D) = "black" {}
        _NormalTex ("Normal", 2D) = "bump" {}
        _EmissionTex ("Emission Mask", 2D) = "black" {}
        _CoreDark ("Core Dark", Color) = (0.03, 0.18, 0.20, 1)
        _CoreLight ("Core Light", Color) = (0.18, 0.52, 0.54, 1)
        _FlowColor ("Flow Color", Color) = (0.46, 0.78, 0.79, 1)
        _EmissionColor ("Emission Color", Color) = (1.0, 0.84, 0.62, 1)
        _Alpha ("Base Alpha", Range(0,1)) = 0.22
        _Transmission ("Thickness Alpha", Range(0,1)) = 0.28
        _RimAlpha ("Rim Alpha", Range(0,1)) = 0.35
        _RimPower ("Rim Power", Range(0.5,8)) = 2.6
        _FlowStrength ("Flow Strength", Range(0,2)) = 0.28
        _CausticStrength ("Caustic Strength", Range(0,2)) = 0.12
        _EmissionStrength ("Emission Strength", Range(0,2)) = 0.22
        _FlowSpeed ("Flow Speed", Range(0,0.2)) = 0.0
        _FlowDirectionScale ("Procedural Direction Scale", Range(0,2)) = 1.0
        _FlowDistortion ("Flow Distortion", Range(0,0.2)) = 0.035
    }

    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Cull Back

        Pass
        {
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_ThicknessTex); SAMPLER(sampler_ThicknessTex);
            TEXTURE2D(_FlowMaskTex); SAMPLER(sampler_FlowMaskTex);
            TEXTURE2D(_CausticTex); SAMPLER(sampler_CausticTex);
            TEXTURE2D(_NormalTex); SAMPLER(sampler_NormalTex);
            TEXTURE2D(_EmissionTex); SAMPLER(sampler_EmissionTex);

            CBUFFER_START(UnityPerMaterial)
                float4 _ThicknessTex_ST, _FlowMaskTex_ST, _CausticTex_ST, _NormalTex_ST, _EmissionTex_ST;
                float4 _CoreDark, _CoreLight, _FlowColor, _EmissionColor;
                float _Alpha, _Transmission, _RimAlpha, _RimPower;
                float _FlowStrength, _CausticStrength, _EmissionStrength, _FlowSpeed;
                float _FlowDirectionScale, _FlowDistortion;
            CBUFFER_END

            struct Attributes { float3 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionHCS : SV_POSITION; float3 positionWS : TEXCOORD0; float3 normalWS : TEXCOORD1; float2 uv : TEXCOORD2; };

            Varyings Vert(Attributes IN)
            {
                Varyings OUT;
                VertexPositionInputs pos = GetVertexPositionInputs(IN.positionOS);
                VertexNormalInputs n = GetVertexNormalInputs(IN.normalOS);
                OUT.positionHCS = pos.positionCS;
                OUT.positionWS = pos.positionWS;
                OUT.normalWS = n.normalWS;
                OUT.uv = IN.uv;
                return OUT;
            }

            half4 Frag(Varyings IN) : SV_Target
            {
                float2 flowUv = TRANSFORM_TEX(IN.uv, _FlowMaskTex);
                float phase = _Time.y * _FlowSpeed;
                // The grayscale texture is only an influence mask.  Direction
                // comes from this procedural, divergence-free-like field.
                float2 field = float2(
                    0.55 + 0.45 * sin(flowUv.y * 6.2831 + phase * 0.7),
                    0.35 + 0.45 * cos(flowUv.x * 4.7124 - phase * 0.5));
                field = normalize(field) * _FlowDirectionScale;
                float2 animatedFlowUv = flowUv + field * phase * _FlowDistortion;
                half thickness = SAMPLE_TEXTURE2D(_ThicknessTex, sampler_ThicknessTex, TRANSFORM_TEX(IN.uv, _ThicknessTex)).r;
                half flowMask = SAMPLE_TEXTURE2D(_FlowMaskTex, sampler_FlowMaskTex, animatedFlowUv).r;
                float2 causticUv = TRANSFORM_TEX(IN.uv, _CausticTex) + field * phase * (_FlowDistortion * 0.45);
                half caustic = SAMPLE_TEXTURE2D(_CausticTex, sampler_CausticTex, causticUv).r * (0.45h + 0.55h * flowMask);
                half emission = SAMPLE_TEXTURE2D(_EmissionTex, sampler_EmissionTex, TRANSFORM_TEX(IN.uv, _EmissionTex)).r;
                float2 normalUv = TRANSFORM_TEX(IN.uv, _NormalTex) + field * phase * (_FlowDistortion * 0.25);
                half3 tangentNormal = UnpackNormal(SAMPLE_TEXTURE2D(_NormalTex, sampler_NormalTex, normalUv));
                tangentNormal.xy *= (0.35h + 0.65h * flowMask);
                float3 N = normalize(IN.normalWS + tangentNormal * 0.16);
                float3 V = SafeNormalize(GetWorldSpaceViewDir(IN.positionWS));
                half fresnel = pow(1.0h - saturate(dot(N, V)), _RimPower);
                half3 core = lerp(_CoreDark.rgb, _CoreLight.rgb, saturate(thickness));
                half3 color = core + _FlowColor.rgb * flowMask * _FlowStrength + caustic.xxx * _CausticStrength;
                color += _EmissionColor.rgb * emission * _EmissionStrength;
                half alpha = saturate(_Alpha + thickness * _Transmission + fresnel * _RimAlpha);
                return half4(color, alpha);
            }
            ENDHLSL
        }
    }
}
