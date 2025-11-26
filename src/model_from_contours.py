"""Rebuild curves from contour JSON in Blender and extrude to a mesh."""
from __future__ import annotations
from pathlib import Path
import json


def build_model_from_contours(
    json_path: Path,
    *,
    extrude_depth: float = 0.1,
    scale: float = 2.0,
    save_stl: Path | None = None,
    bezier_step: int = 1,
) -> None:
    """Load contour data, create Bezier curves, and export an STL inside Blender.

    This function must run inside Blender's Python (bpy) context. It clears the
    current scene, reconstructs closed curves for outer contours and holes,
    extrudes to a mesh, smooths shading, and exports an STL.

    Args:
        json_path: Path to the contours JSON produced by image_prep.py.
        extrude_depth: Extrusion thickness in Blender units.
        scale: World-space scaling factor for the normalized contour coordinates.
        save_stl: Optional path for the output STL; defaults to outputs/.
        bezier_step: Subsampling factor; 1 keeps all points, 3 keeps one of every 3.
    """
    import bpy

    json_path = json_path.resolve()
    with json_path.open("r", encoding="utf8") as f:
        data = json.load(f)

    width = data["width"]
    height = data["height"]
    contours = data["contours"]

    # Start from a clean scene to avoid mixing with existing objects.
    bpy.ops.wm.read_factory_settings(use_empty=False)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    output_stl = (save_stl or Path("outputs/model_from_contours_bezier.stl")).resolve()
    output_stl.parent.mkdir(parents=True, exist_ok=True)

    def touches_border(cnt, w, h, margin: int = 2) -> bool:
        """Return True if any point touches the image border within a margin."""
        for x, y in cnt["points"]:
            if x <= margin or y <= margin or x >= w - margin or y >= h - margin:
                return True
        return False

    # Only keep top-level contours that are not clipped by the image border.
    top_indices = [
        i for i, c in enumerate(contours)
        if c["parent"] == -1 and not touches_border(c, width, height)
    ]

    curve_data = bpy.data.curves.new("TreeCurve", type="CURVE")
    curve_data.dimensions = "2D"
    curve_data.fill_mode = "BOTH"
    curve_data.resolution_u = 16  # Higher curve resolution for smoother edges.

    def add_bezier_spline(points, reverse: bool = False, step: int = 1) -> None:
        """Create a closed Bezier spline from the supplied contour points."""
        if reverse:
            points = list(reversed(points))

        # Optionally subsample to reduce control point count.
        if step > 1:
            points = points[::step]

        if len(points) < 3:
            return

        spline = curve_data.splines.new("POLY")
        spline.points.add(len(points) - 1)

        for i, (x, y) in enumerate(points):
            u = x / (width - 1)
            v = y / (height - 1)
            xw = (u - 0.5) * scale
            yw = (0.5 - v) * scale

            spline.points[i].co = (xw, yw, 0.0, 1.0)

        spline.use_cyclic_u = True

    # Outer contours and holes.
    for i in top_indices:
        outer = contours[i]
        add_bezier_spline(outer["points"], reverse=False, step=bezier_step)

        for j, c in enumerate(contours):
            if c["parent"] == i:
                add_bezier_spline(c["points"], reverse=True, step=bezier_step)

    curve_obj = bpy.data.objects.new("TreeCurveObj", curve_data)
    bpy.context.collection.objects.link(curve_obj)

    # Extrude and convert to mesh.
    curve_data.extrude = extrude_depth
    bpy.context.view_layer.objects.active = curve_obj
    curve_obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    mesh_obj = bpy.context.object
    mesh_obj.name = "Tree_Extruded"

    bpy.ops.object.shade_smooth()

    # Export selection to STL (requires Blender's built-in io_mesh_stl add-on).
    bpy.ops.wm.stl_export(filepath=str(output_stl))
