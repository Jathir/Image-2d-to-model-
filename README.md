# Image to Model Pipeline

Two-stage workflow to convert a 2D silhouette into geometry using Blender.

## Setup
- Create the environment: `conda env create -f environment.yml && conda activate image-to-model`
- Ensure you have Blender installed (script tested with Blender 4.5.4 / Python 3.11).

## Full Pipeline (image prep + Blender trace)
1) Edit `PipelineConfig` in `main.py` and set:
   - `source_image`: your source path (e.g., `"Example\Example_image"`).
   - Optional: `threshold`, `blur` (odd kernel size), `extrude_depth`, `output_dir`, `save_stl`.
2) Run from Blender Python so `bpy` is available:
   ```bash
   blender --python main.py
   ```
   - Outputs go to `outputs/` by default:
     - `binary.png`: thresholded, inverted mask (white foreground).
     - `contours.json`: contour coordinates + hierarchy extracted with OpenCV.
     - `model.stl`: extruded Bezier trace built from the contours.

## Notes
- If your Blender version differs, match `python` and `bpy` versions in `environment.yml`.
- The Blender script starts from a clean scene (`read_factory_settings`) and deletes any existing objects.
