# Credits and asset provenance

## Original project work

The fourteen historical RAN hull studies, the current Australis 2030 geometry, native definitions, original solid-colour textures, controller source and model renders were created for this project. British and US carrier families provide historical design cues; the carrier is an alternate-history design rather than a reproduction of a donor hull.

The v0.8.2 model includes the project's original symmetric broad-stern hull, eight open intake/nozzle paths and connecting wet ducts, internal impellers, steering sleeves, parked reverse-bucket shapes and recessed lift-wall fittings. Those parametric shapes are preliminary game geometry. They are not a selected manufacturer's pump design, certified naval architecture or a CFD-validated installation.

The lift-light controller and its tests are original project code. The 193 checks use a minimal Unity-shaped fixture for policy and reflection integration; they do not run the Sea Power renderer or prove the in-game appearance.

## References and runtime dependencies

For approximate OBJ scale calibration, the user-supplied `ran_majestic_melb98.ini` (217 m length) and `Melbourne_test_3.obj` (3.161967 Z units) were measured. The reference files came from [Project Southern Cross, Workshop item 3574957049](https://steamcommunity.com/sharedfiles/filedetails/?id=3574957049), whose page lists **Peter Garrett** as creator. Its additional contributor credits and the Majestic model's complete lineage must be checked before any third-party asset reuse. The original reference model, texture and INI bytes are not redistributed in the current native package.

User-supplied stock and Workshop INIs were used as schema references. The user's `Seapower-Scripts.dll` was inspected privately to verify the loader, telegraph-speed table, aviation state logic, native mount axes and the stern-foam requirement for rudder initialization. **The game DLL and private inspection material are not included.**

[AnchorChain](https://github.com/SeaPower-Modders/AnchorChain) and Harmony are external runtime/compile dependencies. Their development assemblies were used as compile references; this release distributes the project's own `RAN.Australis.DeckController.dll`, not AnchorChain, Harmony, Unity or game assemblies. Install the compatible external loader/framework separately. Existing stock resource and weapon-profile references resolve through the user's game installation; naming a fallback resource does not bundle that asset.

The [waterjet engineering review](WATERJET-ENGINEERING-REVIEW.md) identifies the ITTC procedures and manufacturer publications used for the preliminary numerical screen. Their use does not imply supplier selection, endorsement or validation of this carrier.

## Renders and concept images

Current model PNGs and the offline 3D viewer derive from the exported OBJ/INI hierarchy. The lift cutaway omits surrounding hull/deck geometry to expose the shaft and uses illustrative lamp shading. These are not gameplay screenshots and do not simulate Unity runtime illumination.

Earlier AI-generated images are appearance studies. They may contain finishing details absent from the model and are not evidence of geometry, performance or engineering validation. They must not be labelled as actual model renders.

Installed Workshop content retains its creators' ownership and permission requirements. No permission for reuse is inferred from having a local installation.
