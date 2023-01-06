# Path Handling
import os.path
from pathlib import Path

# Entropy calculation
import matplotlib.pyplot as plt
from skimage.filters.rank import entropy as sk_entropy
from skimage.morphology import disk as sk_disk
from skimage.exposure import histogram as sk_histogram
from skimage.color import rgb2gray

# Image processing and maths
import numpy as np
import math
from PIL import Image
import quad_tree_compression as qtc

# "Virtual files" for estimating size of the images
from io import BytesIO

# String formatting
from tabulate import tabulate


def get_image_file_size(image: Image, format: str = "png"):
    stream = BytesIO()
    image.save(stream, format, quality=90)
    return len(stream.getvalue())


def mean_squared_error(image_a: np.array, image_b: np.array) -> float:
    image_a = image_a.astype(np.single)
    image_b = image_b.astype(np.single)

    mse_per_channel = np.mean((image_a - image_b) ** 2, axis=(0, 1))
    mse = np.sum(mse_per_channel) / 3
    return float(mse)


def root_mean_squared_error(image_a: np.array, image_b: np.array) -> float:
    return math.sqrt(mean_squared_error(image_a, image_b))


def mean_average_error(image_a: np.array, image_b: np.array) -> float:
    image_a = image_a.astype(np.single)
    image_b = image_b.astype(np.single)
    mae_per_channel = np.mean(np.abs(image_a - image_b), axis=(0, 1))
    mae = np.sum(mae_per_channel) / 3
    return float(mae)


def compute_image_similarity(image_a: np.array, image_b: np.array) -> float:
    return 1 - mean_average_error(image_a, image_b) / 255


def compute_mean_local_entropy(image: np.array, radius=5) -> float:
    gray = (rgb2gray(image) * 255).astype(np.uint8)
    local_entropy = sk_entropy(gray, sk_disk(radius))
    entropy = np.mean(local_entropy)
    return float(entropy)


def compute_channel_histogram_entropy(image_channel: np.array) -> float:
    histogram, _ = sk_histogram(image_channel, nbins=256, source_range="dtype")
    relative_occurrence = histogram / histogram.sum()
    return -(relative_occurrence * np.ma.log2(relative_occurrence)).sum()


def compute_histogram_entropy(image: np.array) -> float:
    return (compute_channel_histogram_entropy(image[:, :, 0])
            + compute_channel_histogram_entropy(image[:, :, 1])
            + compute_channel_histogram_entropy(image[:, :, 2])) / 3


def benchmark_image(image_path: str, iteration_counts: list):
    image_name = Path(image_path).stem
    title = f"Image '{image_name}'"
    print("=" * len(title))
    print(title)
    print("=" * len(title))

    image = Image.open(image_path)
    image_data = np.array(image, dtype=np.uint8)

    png_size = get_image_file_size(image, "png")
    jpg_size = get_image_file_size(image, "jpeg")

    print()
    print(tabulate([
        ["PNG", f"{(png_size / 1000):,.1f}"],
        ["JPG (90% quality)", f"{(jpg_size / 1000):,.1f}"]
    ], headers=["File Type", "Size (KB)"], stralign="right"))

    local_entropy = compute_mean_local_entropy(image_data)
    histogram_entropy = compute_histogram_entropy(image_data)
    print()
    print("Dimensions of difficulty (0 = empty image; the higher the more difficult)")
    print(tabulate([
        ["Mean Local Entropy", f"{local_entropy:.3f}"],
        ["Histogram Entropy", f"{histogram_entropy:.3f}"]
    ]))

    compressor = qtc.ImageCompressor(image_data)

    last_iteration_count = 0
    results_table = []
    for iteration_count in iteration_counts:
        compressor.add_detail(iteration_count - last_iteration_count)
        last_iteration_count = iteration_count

        compressed_size = len(compressor.encode_to_binary())
        compressed_image_data = compressor.draw()
        Image.fromarray(compressed_image_data).save(os.path.join(f"output/{image_name}_{iteration_count}.jpg"))

        error = mean_average_error(image_data, compressed_image_data)
        size_reduction_png = (png_size - compressed_size) / png_size
        size_reduction_jpg = (jpg_size - compressed_size) / jpg_size
        compression_factor_png = png_size / compressed_size
        compression_factor_jpg = jpg_size / compressed_size

        results_table.append([
            iteration_count,
            f"{(compressed_size / 1000):,.2f}",
            f"{error:.2f}",
            f"{(size_reduction_png * 100):.2f}",
            f"{(size_reduction_jpg * 100):.2f}",
            f"{compression_factor_png:.2f}",
            f"{compression_factor_jpg:.2f}"
        ])

    print()
    print(tabulate(results_table, headers=[
        "Iterations",
        "Compressed\nSize (KB)",
        "Mean Average\nError",
        "Size Reduction\nPNG (%)",
        "Size Reduction\nJPG (%)",
        "Compression\nFactor PNG",
        "Compression\nFactor JPG",
    ], stralign="right"))
    print()
    print()
    print()


if __name__ == '__main__':
    detail_levels = [100, 1000, 20000, 80000]
    benchmark_image("input/flowers.jpg", iteration_counts=detail_levels)
    benchmark_image("input/mountain.jpg", iteration_counts=detail_levels)
    benchmark_image("input/night.jpg", iteration_counts=detail_levels)
    benchmark_image("input/penguins.jpg", iteration_counts=detail_levels)
    benchmark_image("input/plant.jpg", iteration_counts=detail_levels)
    benchmark_image("input/squares.png", iteration_counts=detail_levels)
    benchmark_image("input/hiking.jpg", iteration_counts=detail_levels)
    benchmark_image("input/sunset.jpg", iteration_counts=detail_levels)
    benchmark_image("input/computer.jpg", iteration_counts=detail_levels)


# TODO: Add totally empty image to the examples
