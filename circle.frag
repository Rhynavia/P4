#version 120

uniform vec2 resolution;
uniform vec2 center;
uniform float radius;
uniform float time;

uniform vec3 color1;
uniform vec3 color2;
uniform vec3 color3;
uniform float alpha;

float noise(vec2 p) {
    return fract(sin(dot(p ,vec2(12.9898,78.233))) * 43758.5453);
}

float smoothNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = noise(i);
    float b = noise(i + vec2(1.0, 0.0));
    float c = noise(i + vec2(0.0, 1.0));
    float d = noise(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

float fractal(vec2 p) {
    float total = 0.0;
    float amplitude = 1.0;
    float frequency = 1.0;
    for (int i = 0; i < 5; i++) {
        total += amplitude * smoothNoise(p * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
    }
    return total;
}

void main() {
    vec2 uv = gl_FragCoord.xy;
    float dist = distance(uv, center);

    if (dist > radius) discard;

    vec2 pos = (uv - center) / radius;

    vec2 wavePos = pos + 0.3 * vec2(
        sin(pos.y * 10.0 + time * 2.0),
        sin(pos.x * 10.0 + time * 2.5)
    );

    float pattern = fractal(wavePos * 5.0 - vec2(time * 0.5));

    vec3 color = mix(color1, color2, pattern);
    color = mix(color, color3, pattern * pattern);

    gl_FragColor = vec4(color, alpha);
}
