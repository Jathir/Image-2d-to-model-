"""Entry point for the image-to-model pipeline using OpenCV and Blender."""
from dataclasses import dataclass
from pathlib import Path
from src.image_prep import prepare_image_with_contours
from src.model_from_contours import build_model_from_contours

@dataclass
class PipelineConfig:
    """Configuration for the two-stage pipeline."""
    source_image: Path = Path(r"Example\example_image.png")
    output_dir: Path = Path("outputs")
    save_stl: Path = Path("outputs/model.stl")
    threshold: int = 180
    blur: int = 1
    extrude_depth: float = 0.1  # extrusion thickness in Blender units

def run_pipeline(config: PipelineConfig) -> None:
    """Run image prep (OpenCV) followed by curve/mesh build (Blender)."""
    paths = prepare_image_with_contours(
        input_path=config.source_image,
        output_dir=config.output_dir,
        threshold=config.threshold,
        blur=config.blur,
    )

    build_model_from_contours(
        json_path=paths["contours_json"],
        extrude_depth=config.extrude_depth,
        save_stl=config.save_stl,
    )

def main() -> None:
    """Convenience entry point when running this file directly."""
    run_pipeline(PipelineConfig())

if __name__ == "__main__":
    main()
