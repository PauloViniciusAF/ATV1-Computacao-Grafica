#version 300 es
precision highp float;

in vec3 fragNormal;
in vec2 fragTexCoord;
in vec4 fragColor;
in vec4 fragPosition;
in float vDepth;

out vec4 finalColor;

const vec3 bitShift = vec3(256.0*256.0, 256.0, 1.0);
const vec3 bitMask  = vec3(0.0, 1.0/256.0, 1.0/256.0);

void main()
{   
    float dummy = 0.00000001*fragColor.r+ 0.00000001*fragNormal.x+ 0.00000001*fragTexCoord.x + 0.00000001*fragPosition.x;
    //float depth = gl_FragCoord.z*60.0-0.4;
    float depth = clamp((vDepth * 0.5 + 0.5)*30.0, 0.0, 1.0);
    
    vec3 res = fract(depth * bitShift);
    res -= res.xxy * bitMask;

    finalColor = vec4(res.x, res.y, res.z, 1.0+dummy*0.0000000000001);
    //finalColor = vec4(new_depth, new_depth, new_depth, 1.0+dummy*0.0000000000001);

}