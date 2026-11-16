# Arlecchino avatar integration

The desktop assistant now uses an Arlecchino roleplay persona and exposes a constrained mood label in structured model replies. The mood is not spoken; it is sent to the avatar renderer as an animation cue.

## Model asset

`genshin-impact-arlecchino.zip` contains the FBX source and five textures. The avatar asset workflow converts it to `assets/avatar/arlecchino.glb` and downloads a pinned local Three.js build into `assets/vendor/`. The conversion report is in `assets/avatar/manifest.json`.

The imported model has four meshes, one skin with 126 joints, and no animation clips or facial morph targets. The first renderer therefore uses procedural idle, listening, thinking, speaking and acting poses (head, neck, spine, arms and hair). It does not claim true lip-sync or facial morph animation.

## Runtime flow

1. `Assistant` builds the Arlecchino system prompt and requests a mood enum with each structured reply.
2. `Bridge.expression` transfers the selected mood to the Qt UI.
3. `MainWindow` forwards assistant state and audio level to `AvatarWidget`.
4. `AvatarWidget` sends small state updates to the local Three.js scene in Qt WebEngine.
5. The old lightweight orb remains as a fallback if Qt WebEngine or the avatar assets are unavailable.

## Packaging

The renderer uses local files only; remote WebEngine content access is disabled. Windows builds require the PySide6 Addons package (Qt WebEngine), and the PyInstaller spec includes the avatar and vendor asset folders.
