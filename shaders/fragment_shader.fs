#version 300 es
#define MAX_LIGHTS 4

precision highp float;

in vec3 fragNormal;
in vec2 fragTexCoord;
in vec4 fragColor;
in vec4 fragPosition;

uniform sampler2D texture0;
uniform vec4 colDiffuse;
uniform vec3 lightDir;
uniform vec3 lightColor;
uniform sampler2D shadowMap;
uniform mat4 lightVP;
uniform int shadowMapSize;
uniform int lightCount;
uniform vec3 lightPos[MAX_LIGHTS];
uniform vec3 lightColorList[MAX_LIGHTS];

const float lightRadius = 2.0;
const vec3 bitShift = vec3(1.0/(256.0*256.0), 1.0/256.0, 1.0);


const int SAMPLE_COUNT = 16;

const vec2 poissonSamples[16] = vec2[](
	vec2(-0.94201624, -0.39906216),
    vec2( 0.94558609, -0.76890725),
    vec2(-0.09418410, -0.92938870),
    vec2( 0.34495938,  0.29387760),
    vec2(-0.91588581,  0.45771432),
    vec2(-0.81544232, -0.87912464),
    vec2(-0.38277543,  0.27676845),
    vec2( 0.97484398,  0.75648379),
    vec2( 0.44323325, -0.97511554),
    vec2( 0.53742981, -0.47373420),
    vec2(-0.26496911, -0.41893023),
    vec2( 0.79197514,  0.19090188),
    vec2(-0.24188840,  0.99706507),
    vec2(-0.81409955,  0.91437590),
    vec2( 0.19984126,  0.78641367),
    vec2( 0.14383161, -0.14100790)
    );

out vec4 finalColor;


float shadowFactor()
{   vec3 normal = normalize(fragNormal);
    vec3 l = normalize(lightDir);

    vec4 fragPosLightSpace = lightVP*fragPosition;
    fragPosLightSpace.xyz /= fragPosLightSpace.w;
    fragPosLightSpace.xyz = (fragPosLightSpace.xyz + 1.0)/2.0;

    float bias = max(0.0008*(1.0 - dot(normal, l)), 0.00008);
    //float sampleDepth = texture(shadowMap, fragPosLightSpace.xy).r;

    //return fragPosLightSpace.z - bias > sampleDepth ? 0.3 : 1.0;
    float shadowCounter = 0.0;

    vec2 texelSize = vec2(1.0/float(shadowMapSize));
    for (int i = 0; i < SAMPLE_COUNT; i++){
    	vec3 sampleDepth = texture(shadowMap, fragPosLightSpace.xy + texelSize*poissonSamples[i]).rgb;
    	if (fragPosLightSpace.z * 30.0 - bias > dot(sampleDepth, bitShift)) shadowCounter++;
    }

    return mix(1.0, 0.4, shadowCounter / float(SAMPLE_COUNT));
    
}

vec3 pointLightGlow()
{
	vec3 pointLights = vec3(0.0);
	for (int i = 0; i < lightCount; i++)
	{
		float distance = length(lightPos[i] - fragPosition.xyz);
		float attenuation = clamp(1.0 - distance/lightRadius, 0.0, 1.0);
		pointLights += (attenuation * attenuation * lightColorList[i]);
	}
	return pointLights;
}

void main()
{
	vec3 normal = normalize(fragNormal);
	float diff = max(dot(fragNormal, -normalize(lightDir)), 0.25);
	float shadow = shadowFactor();

	vec3 pointLights = pointLightGlow();



	vec4 lighting = vec4(diff * lightColor * shadow + pointLights, 1.0);

	vec4 texel = texture(texture0, fragTexCoord);

	finalColor = lighting * texel * colDiffuse * fragColor;
	
}