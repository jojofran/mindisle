Shader "MindIsle/FlowRibbon"
{
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha
        Cull Off
        ZWrite Off
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
            };
            struct v2f
            {
                float4 vertex : SV_POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
            };
            v2f vert(appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.color = v.color;
                o.uv = v.uv;
                return o;
            }
            fixed4 frag(v2f i) : SV_Target
            {
                float edge = smoothstep(0.0, .22, i.uv.x) * (1.0 - smoothstep(.78, 1.0, i.uv.x));
                float body = .76 + .24 * sin(i.uv.y * UNITY_PI);
                return fixed4(i.color.rgb, i.color.a * edge * body);
            }
            ENDCG
        }
    }
    Fallback Off
}
