#define N 500

// x, y position of the light
uniform vec2 lightPosition;

// Size of light in pixels
uniform float lightSize;

// Amount to mix the colors
uniform float iMix;

float terrain(vec2 samplePoint)
{
    float samplePointAlpha = texture(iChannel0, samplePoint).a;
    float sampleStepped = step(0.1, samplePointAlpha);
    float returnValue = 1.0 - sampleStepped;

    // Soften the edges of the shadows
    returnValue = mix(0.96, 1.0, returnValue);

    return returnValue;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Distance in pixels to the light
    float distanceToLight = length(lightPosition - fragCoord);

    // Normalize the fragment coordinate from (0.0, 0.0) to (1.0, 1.0)
    vec2 normalizedFragCoord = fragCoord/iResolution.xy;
    vec2 normalizedLightCoord = lightPosition.xy/iResolution.xy;

    // Start our mixing variable at 1.0
    float lightAmount = 1.0;
    for(float i = 0.0; i < N; i++)
    {
        // A 0.0 - 1.0 ratio between where our current pixel is, and where the light is
        float t = i / N;
        // Grab a coordinate between where we are and the light
        vec2 samplePoint = mix(normalizedFragCoord, normalizedLightCoord, t);
        // Is there something there? If so, we'll assume we are in shadow
        float shadowAmount = terrain(samplePoint);
        // Multiply the light amount.
        // (Multiply in case we want to upgrade to soft shadows)
        lightAmount *= shadowAmount;
    }

    // Find out how much light we have based on the distance to our light
    lightAmount *= 1.0 - smoothstep(0.1, lightSize, distanceToLight);

    // Make the starting colors and ending colors, then mix them together so that over time the color changes from
    // the starting color to the ending color.
    vec4 startColor = vec4(30.0/256.0, 33.0/256.0, 40.0/256.0, 1.0);
    vec4 endColor = vec4(199.0/256.0, 82.0/256.0, 42.0/256.0, 1.0);

    vec4 blackColor = mix (startColor, endColor, iMix);

    // Our fragment color will be somewhere between black and channel 1
    // dependent on the value of b.
    fragColor = mix(blackColor, texture(iChannel1, normalizedFragCoord), lightAmount), iChannel0;
}