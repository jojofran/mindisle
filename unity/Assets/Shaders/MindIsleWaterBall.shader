Shader "MindIsle/WaterBall"
{
 Properties {
   _Clock("Controlled clock",Float)=0
   [HideInInspector]_Breath("Breath",Float)=0
   [HideInInspector]_State("Focus state",Float)=0
   [HideInInspector]_Progress("Transition progress",Float)=0
   [HideInInspector]_Shape("Shape amount",Float)=0
   [HideInInspector]_Trail("Trail amount",Float)=0
   [HideInInspector]_Aspect("Aspect",Float)=.462
   [HideInInspector]_Radius("Radius",Float)=.148
   [HideInInspector]_Green("Green node",Vector)=(0,0,0,0)
   [HideInInspector]_Warm("Warm node",Vector)=(0,0,0,0)
 }
 SubShader {
 Tags {"RenderType"="Opaque"}
 Pass {
 Cull Off ZWrite Off
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment frag
 #pragma target 3.0
 #include "UnityCG.cginc"
 float _Clock,_Breath,_State,_Progress,_Shape,_Trail,_Aspect,_Radius;
 float4 _Green,_Warm,_GreenTrail[33],_WarmTrail[33];
 float3 background(float2 p) {
   float cloud=.5+.24*sin(p.x*5+p.y*3)+.18*cos(p.y*6-p.x*4);
   float haze=.5+.5*sin(p.x*2.1-p.y*1.7+sin(p.y*3.2)*.35);
   float3 c=lerp(float3(.878,.918,.925),float3(.974,.976,.966),saturate(cloud*.72+haze*.28));
   float mist=exp(-pow((p.x*.75-p.y*.45+.12)*2.4,2));
   float light=exp(-pow((p.x+p.y*.62-.72)*5,2));
   float movingWarm=(_State>1.5)?1:0;
   return c+float3(.010,.008,.004)*mist+float3(.014,.005,-.005)*light*_Shape+float3(.012,.004,-.004)*light*movingWarm;
 }
 float boundary(float a) {
   float d=.042*sin(3*a+_Clock*.47)+.024*sin(5*a-_Clock*.31)+.016*cos(2*a+_Clock*.23)+.009*sin(7*a+_Clock*.17);
   float ripple=(_State>.5&&_State<1.5)?sin(UNITY_PI*saturate((_Progress-.27)/.63))*.024:0;
   return 1+_Shape*d+ripple*exp(-12*pow(sin(a-2),2))*sin(_Progress*13);
 }
 float ribbon(float2 q, bool warm) {
   float ink=0;
   [loop]for(int k=0;k<32;k++) {
     float2 a=warm?_WarmTrail[k].xy:_GreenTrail[k].xy;
     float2 b=warm?_WarmTrail[k+1].xy:_GreenTrail[k+1].xy;
     float2 ab=b-a; float h=saturate(dot(q-a,ab)/max(dot(ab,ab),.0000001));
     float s=(k+h)/32.;
     float width=(.006+.062*pow(sin(s*UNITY_PI),1.18))*(warm?.76:1)*_Trail;
     float dist=length(q-a-h*ab);
     float fade=pow(s,1.12)*smoothstep(0,.10,s);
     float depth=.62+.26*sin((a.x+a.y)*2);
     float core=exp(-pow(dist/max(.001,width),2))*fade*depth;
     float halo=exp(-pow(dist/max(.001,width*2.2),2))*fade*.22;
     ink=max(ink,core+halo);
   }
   return ink*_Trail;
 }
 float segmentInk(float2 q,float2 a,float2 b,float strength,float warm) {
   float2 ab=b-a; float h=saturate(dot(q-a,ab)/max(dot(ab,ab),.00001));
   float d=length(q-(a+h*ab));
   return exp(-pow(d/(warm>.5?.040:.052),2))*strength;
 }
 float3 blendPoint(float3 col,float2 q,float2 pos,float3 tint) {
   float d=length(q-pos); float aa=max(fwidth(d),.001);
   float mask=1-smoothstep(.018-aa,.021+aa,d);
   return lerp(col,tint,mask*.58);
 }
 fixed4 frag(v2f_img i):SV_Target {
   float2 uv=i.uv;
   float2 q=(uv-float2(.5,.46))*float2(_Aspect,1)/_Radius;
   float a=atan2(q.y,q.x), edge=boundary(a), r=length(q)/edge;
   float3 base=background(uv), col=base;
   float greenInk=0,warmInk=0;
   if(_Trail>.001) {greenInk=ribbon(q,false);warmInk=ribbon(q,true);}
   if(_State>.5 && _State<1.5) {
     float reveal=smoothstep(.1,.9,_Progress);
     greenInk=max(greenInk,segmentInk(q,float2(-.34,.43),_Green.xy,reveal,false));
     warmInk=max(warmInk,segmentInk(q,float2(.34,-.43),_Warm.xy,reveal,true));
   }
   if(_State>1.5) {
     float greenBridge=segmentInk(q,normalize(_Green.xy)*.97,_Green.xy,.62,false);
     float warmBridge=segmentInk(q,normalize(_Warm.xy)*.97,_Warm.xy,.48,true);
     greenInk=max(greenInk,greenBridge*_Trail);
     warmInk=max(warmInk,warmBridge*_Trail);
   }
   col=lerp(col,float3(.34,.65,.64),greenInk*.62);
   col=lerp(col,float3(.83,.64,.51),warmInk*.34);
   float coverage=1-smoothstep(1-fwidth(r),1+fwidth(r),r);
   if(r<1.01) {
     float z=sqrt(saturate(1-r*r));
     float e1=boundary(a+.004),e0=boundary(a-.004);
     float slope=(e1-e0)/.008;
     float3 n=normalize(float3(q.x/edge+slope*sin(a),q.y/edge-slope*cos(a),-z));
     float3 ray=refract(float3(0,0,1),n,1/1.333);
     float2 refracted=uv+ray.xy*.055*z;
     float3 water=background(refracted);
     float clock=_State<.5?_Breath*.006:_Clock*.24;
     float2 coreQ=q-float2(-.035,-.025);
     float coreRadius=length(coreQ);
     float coreWeight=exp(-dot(coreQ*float2(1.18,.92),coreQ*float2(1.18,.92))*3.4);
     float radialWave=exp(-pow((coreRadius-.34)/.075,2))*
       (.5+.5*sin(coreRadius*23.0-clock*1.35+a*1.8));
     float squeezeWarp=.075*coreWeight*sin(coreRadius*15.0-clock*1.2+a*1.4);
     float2 flowQ=q+coreQ/max(coreRadius,.001)*squeezeWarp;
     float density=0,filmLight=0,flowLight=0;
     // Thin continuous membranes through one volume, with changing local curvature (no textures).
     [loop]for(int k=0;k<32;k++) {
       float depth=(k+.5)/32.;
       float3 p=float3(q/edge,-z)+ray*(2*z*depth);
       float bend=.36*sin(p.y*2.8+clock*.7)+.16*sin(p.z*3.8+p.y*1.8-clock*.53)+.09*sin(p.x*4.4-p.y*2.2+clock*.21);
       float sheet=p.x-bend+.10*cos(p.y*3.5-p.z*2.1+clock*.31)+.045*sin(p.z*5.4+clock*.43);
       float envelope=saturate(1-dot(p,p));
       density+=exp(-sheet*sheet*8.5)*envelope/32.;
       filmLight+=exp(-pow(sheet-.20,2)*88)*envelope/32.;
       flowLight+=(.5+.5*sin((p.x*1.7+p.y*2.1+p.z*2.8)+clock*.78))*envelope/32.;
     }
     float pool=exp(-dot(q-float2(-.07,-.03),q-float2(-.07,-.03))*3.3);
     // Keep the outside transparent and let the center carry the visual weight.
     // The volume reads through layered absorption instead of a flat cyan wash.
     float depthTint=saturate(density*.72+pool*.22);
     water=lerp(water,float3(.29,.53,.53),depthTint);
     // A denser cyan water core with a squeezed, displaced ring around it.
     water=lerp(water,float3(.16,.40,.41),coreWeight*(.16+.16*(_State>.5)));
     water+=float3(.018,.048,.046)*radialWave*(.34+.48*(_State>.5));
     // A displaced ripple catches only one side of the compressed core.
     float rippleRadius=.37+.052*sin(a*2.0-clock*.18)+.022*sin(a*5.0+clock*.31);
     float rippleBand=exp(-pow((coreRadius-rippleRadius)/.062,2));
     float rippleSide=.35+.65*saturate(.5+.5*sin(a-0.8));
     water-=float3(.015,.031,.030)*rippleBand*rippleSide*(.5+.5*(_State>.5));
     water+=float3(.020,.046,.044)*exp(-pow((coreRadius-rippleRadius-.052)/.046,2))*rippleSide*(.3+.4*(_State>.5));
     // The compressed center pushes a broad, uneven shelf into the surrounding water.
     float shelfRadius=.59+.075*sin(a*2.0+clock*.22)+.025*sin(a*4.0-clock*.37);
     float shelf=exp(-pow((coreRadius-shelfRadius)/.105,2));
     float shelfFlow=.5+.5*sin(a*3.0-coreRadius*11.0+clock*.48);
     water=lerp(water,float3(.245,.48,.49),shelf*(.035+.075*(_State>.5))*(.55+.45*shelfFlow));
     water-=float3(.010,.020,.019)*shelf*(.35+.65*(1-shelfFlow))*(_State>.5);
     float streamA=pow(saturate(.5+.5*sin(flowQ.x*2.05+flowQ.y*1.20+sin(flowQ.y*3.4+clock*.35)*.34+clock*.55)),6.0);
     float streamB=pow(saturate(.5+.5*sin(-flowQ.x*1.15+flowQ.y*2.35+sin(flowQ.x*2.8-clock*.28)*.28-clock*.39)),7.0);
     float streamSoft=pow(saturate(.5+.5*sin(flowQ.x*1.35-flowQ.y*1.65+sin(flowQ.x*2.1+clock*.22)*.25+clock*.25)),2.2);
     float activeFlow=saturate(_State*.5);
     float streamMask=.08+.68*activeFlow;
     water+=float3(.018,.045,.043)*streamSoft*streamMask;
     water+=float3(.060,.125,.116)*streamA*streamMask;
     water+=float3(.036,.078,.071)*streamB*streamMask;
     // Narrow curved flow ridges sit inside the broad membranes. A signed
     // companion band gives each ridge a shaded side instead of a glow stripe.
     float ridgePhase=flowQ.x*3.6+flowQ.y*2.2+sin(flowQ.y*4.0+clock*.5)*.5+clock*.6;
     float flowRidge=pow(saturate(.5+.5*sin(ridgePhase)),10.0);
     float flowShadow=pow(saturate(.5+.5*sin(ridgePhase+1.35)),7.0);
     water+=float3(.040,.086,.081)*flowRidge*activeFlow;
     water-=float3(.016,.037,.035)*flowShadow*activeFlow;
     // Two broad, bent membranes make the water direction readable at a glance.
     // They are volume lines, not decals: their shape is warped by the same flowQ.
     float membraneA=flowQ.y*.72-.105-.145*sin(flowQ.x*3.1+clock*.62)-.070*sin(flowQ.y*4.2-clock*.34);
     float membraneB=flowQ.x*.64+.135+.125*sin(flowQ.y*3.6-clock*.48)+.055*sin(flowQ.x*5.0+clock*.27);
     float membraneMask=exp(-dot(flowQ,flowQ)*.92)*activeFlow;
     float lineA=exp(-pow(membraneA/.052,2))*membraneMask;
     float lineB=exp(-pow(membraneB/.046,2))*membraneMask;
     float edgeA=exp(-pow((membraneA-.058)/.038,2))*membraneMask;
     float edgeB=exp(-pow((membraneB+.050)/.034,2))*membraneMask;
     water-=float3(.014,.031,.030)*(lineA*.74+lineB*.58);
     water+=float3(.022,.050,.047)*(edgeA*.52+edgeB*.38);
     float swirl=.5+.5*sin((flowQ.x*1.6-flowQ.y*2.2+sin(flowQ.y*2.4)*.45)*2.1+clock*.72);
     float volumeCloud=exp(-dot(q-float2(.10,-.05),q-float2(.10,-.05))*1.6);
     water=lerp(water,float3(.22,.47,.48),volumeCloud*(.04+.08*swirl)*(_State>.5));
     water+=filmLight*.105+flowLight*.045;
     // Uneven translucent folds, broad shadow side and a much thinner light side.
     [unroll]for(int j=0;j<3;j++) {
       float f=j;
       float fold=.50+f*.15+.067*sin(a*2+clock*.63+f*.9)+.038*cos(a*3-clock*.41+f);
       float d=r-fold;
       float weight=(.5+.5*sin(a+f*1.8+clock*.18))*(.18+f*.065);
       float shadow=exp(-pow((d+.030)/.074,2));
       float shine=exp(-pow(d/.020,2));
       water-=float3(.085,.108,.103)*shadow*weight;
       water+=float3(.115,.13,.125)*shine*weight;
     }
     float fresnel=.0204+.9796*pow(1-z,4.4);
     float rimLight=.5+.5*sin(a*2+.5+_Shape*sin(_Clock*.19)*.4);
     water=lerp(water,lerp(float3(.67,.78,.77),float3(.99,.994,.985),rimLight),fresnel*.58);
     float rim=exp(-pow((r-.984)/.010,2));
     water+=rim*(.020+.032*rimLight);
     float crescent=exp(-pow((r-.91)/.045,2))*pow(saturate(dot(normalize(q+float2(.0001,0)),normalize(float2(-.55,.85)))),7);
     water+=crescent*.12;
     float warm=exp(-pow((r-.91)/.032,2))*pow(saturate(dot(normalize(q+float2(.0001,0)),normalize(float2(.7,.65)))),12);
     water+=float3(.035,.020,.003)*warm;
     col=lerp(col,water,coverage);
     // Depth attenuation provides a back/front relation when a node's recent trail crosses the water.
     col=lerp(col,float3(.22,.56,.54),greenInk*(_State>.5&&_State<1.5?.78:.16));
     col=lerp(col,float3(.83,.60,.47),warmInk*(_State>.5&&_State<1.5?.40:.09));
   }
   col=blendPoint(col,q,_Green.xy,float3(.41,.66,.62));
   col=blendPoint(col,q,_Warm.xy,float3(.85,.71,.59));
   return float4(col,1);
 }
 ENDCG
 }
 }
 Fallback "Unlit/Color"
}
