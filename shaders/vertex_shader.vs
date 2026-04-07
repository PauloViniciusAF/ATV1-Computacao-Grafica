#version 300 es

precision highp float;

in vec3 vertexPosition;
in vec3 vertexNormal;
in vec2 vertexTexCoord;
in vec4 vertexColor;

uniform mat4 mvp;
uniform mat4 matModel;

out vec3 fragNormal;
out vec2 fragTexCoord;
out vec4 fragColor;
out vec4 fragPosition;
out float vDepth;


void main()
{
	fragPosition = vec4(matModel*vec4(vertexPosition, 1.0));
	fragNormal = mat3(matModel) * vertexNormal;
	fragTexCoord = vertexTexCoord;
	fragColor = vertexColor;
	gl_Position = mvp * vec4(vertexPosition, 1.0);
	vDepth = gl_Position.z / gl_Position.w;
	
}