"""Image preprocessing: thresholding and contour extraction to JSON."""
from __future__ import annotations
from pathlib import Path
import cv2
import json


def prepare_image_with_contours(
    input_path: Path,
    output_dir: Path,
    threshold: int = 180,
    blur: int = 3,
) -> dict[str, Path]:
    """Create a binary mask, find hierarchical contours, and persist both.

    Args:
        input_path: Path to the source image; read as grayscale.
        output_dir: Destination folder for generated files.
        threshold: Intensity threshold (0-255) for binarization.
        blur: Odd kernel size for Gaussian blur; use 1 to skip blurring.

    Returns:
        Mapping with paths for the binary image and the saved contours JSON.

    Raises:
        FileNotFoundError: If the image cannot be loaded.
        RuntimeError: If no contours are detected.
    """
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(input_path)

    if blur > 1:
        img_blur = cv2.GaussianBlur(img, (blur, blur), 0)
    else:
        img_blur = img

    # Produce a binary mask (white foreground, black background) by inversion.
    _, binary = cv2.threshold(img_blur, threshold, 255, cv2.THRESH_BINARY)
    binary_inv = cv2.bitwise_not(binary)

    binary_path = output_dir / "binary.png"
    cv2.imwrite(str(binary_path), binary_inv)

    # Extract contours with hierarchy (external + holes).
    contours, hierarchy = cv2.findContours(
        binary_inv,
        cv2.RETR_CCOMP,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if hierarchy is None:
        raise RuntimeError("No contours found")

    h = hierarchy[0]
    data = {
        "width": int(binary_inv.shape[1]),
        "height": int(binary_inv.shape[0]),
        "contours": [],
    }

    for i, cnt in enumerate(contours):
        pts = cnt[:, 0, :].tolist()  # [[x, y], ...]
        parent = int(h[i][3])        # -1 if it has no parent
        data["contours"].append({
            "points": pts,
            "parent": parent,
        })

    json_path = output_dir / "contours.json"
    with json_path.open("w", encoding="utf8") as f:
        json.dump(data, f, indent=2)

    return {
        "binary": binary_path,
        "contours_json": json_path,
    }
