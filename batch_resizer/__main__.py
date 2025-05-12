#!/usr/bin/env python3
import argparse
import io
from pathlib import Path
from typing import Union
from PIL import Image

def process_image(
    path: Path,
    min_width: int,
    min_height: int,
    max_size_kb: int,
    suffix: str = "resized"
) -> None:
    """
    Process a single image:
      - Ensure resolution >= (min_width, min_height) by upscaling if needed.
      - Compress to ensure file size <= max_size_kb KB by lowering JPEG quality.
      - Save a new file with '_<suffix>' in the same directory, overwriting if exists.
    """
    try:
        with Image.open(path) as img:
            # Convert to RGB to avoid issues with palettes or alpha channels
            img = img.convert("RGB")
            orig_w, orig_h = img.size

            # 1) Upscale if below minimum dimensions
            scale = max(1.0, min_width / orig_w, min_height / orig_h)
            if scale > 1.0:
                new_size = (int(orig_w * scale), int(orig_h * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # 2) Compress by adjusting JPEG quality
            quality = 85
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)
            while buffer.tell() > max_size_kb * 1000 and quality > 10:
                quality -= 5
                buffer.seek(0)
                buffer.truncate(0)
                img.save(buffer, format="JPEG", quality=quality)

            # 3) Write out new file, overwriting if necessary
            new_name = f"{path.stem}_{suffix}{path.suffix}"
            new_path = path.with_name(new_name)
            with open(new_path, "wb") as f:
                f.write(buffer.getvalue())

    except Exception as e:
        raise Exception(f"Failed to process image {path!s}: {e}")

def process_directory(
    dir_path: Union[str, Path],
    min_width: int = 560,
    min_height: int = 740,
    max_size_kb: int = 500,
    suffix: str = "resized"
) -> None:
    """
    Traverse the given directory (and subdirectories), and process all .jpg/.jpeg images.
    """
    base = Path(dir_path)
    if not base.is_dir():
        raise NotADirectoryError(f"{dir_path!s} is not a directory.")

    for path in base.rglob("*"):
        # Only process .jpg/.jpeg files that do NOT already have the suffix in their name
        if (path.is_file()
            and path.suffix.lower() in (".jpg", ".jpeg")
            and f"_{suffix}" not in path.stem):
            process_image(path, min_width, min_height, max_size_kb, suffix)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch-resizer is a batch image resizing tool."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Target directory (default: current directory)"
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=560,
        help="Minimum width in pixels (default: 560)"
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=740,
        help="Minimum height in pixels (default: 740)"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=500,
        help="Maximum file size in KB (default: 500)"
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="resized",
        help="Suffix for processed files (without underscore, default: resized)"
    )

    args = parser.parse_args()
    process_directory(
        args.directory,
        min_width=args.min_width,
        min_height=args.min_height,
        max_size_kb=args.max_size,
        suffix=args.suffix
    )
