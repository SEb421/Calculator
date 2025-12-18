---
description: Launch the iOS 26 Liquid Glass demo to view advanced glass/refraction effects
---

# iOS 26 Liquid Glass Demo

This workflow launches the interactive demo showcasing Apple's iOS 26 "Liquid Glass" design language with advanced optical effects.

## Features Demonstrated

- **Chromatic Aberration**: RGB channel splitting through different refraction indices
- **Fresnel Effect**: Angle-dependent reflection/refraction blending
- **Dynamic Specular Highlights**: Orbiting light source for realistic reflections
- **Internal Caustics**: Light concentration patterns inside the glass
- **Ambient Occlusion & Soft Shadows**: Realistic depth perception
- **Interactive Controls**: Adjust IOR, dispersion, Fresnel power, and more

## Steps

// turbo
1. Start a local server in the demo directory:
```powershell
npx -y http-server ./demo -p 8080 -o
```

2. The browser will open automatically to http://localhost:8080

## Interaction

- **Move your cursor/finger** across the screen to interact with the liquid glass blob
- Use the **control panel** (bottom-left) to adjust:
  - IOR (Index of Refraction) - how much light bends
  - Dispersion - chromatic aberration strength  
  - Fresnel Power - edge reflection intensity
  - Specular Light - highlight brightness
  - Glass Opacity - translucency amount

## Technical Details

The demo uses:
- **Three.js** for WebGL rendering
- **GLSL fragment shaders** for raymarching SDFs
- **React** for the UI overlay and controls
