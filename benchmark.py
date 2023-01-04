import math
from io import BytesIO

import numpy as np
from PIL import Image
from tabulate import tabulate

import quad_tree_compression as qtc


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


def compute_image_entropy(image: np.array, radius=5) -> float:
    from skimage.filters.rank import entropy as sk_entropy
    from skimage.morphology import disk as sk_disk
    from skimage.color import rgb2gray

    gray = rgb2gray(image)
    local_entropy = sk_entropy(gray, sk_disk(radius))
    entropy = np.mean(local_entropy)

    # from skimage.io import imshow
    # imshow(local_entropy)
    # import matplotlib.pyplot as plt
    # plt.show()

    return float(entropy)


def benchmark_image(image_path: str, iteration_counts: list):
    title = f"Image '{image_path}'"
    print(title)
    print("=" * len(title))

    image = Image.open(image_path)
    image_data = np.array(image)

    png_size = get_image_file_size(image, "png")
    jpg_size = get_image_file_size(image, "jpeg")

    print(tabulate([
        ["PNG", f"{(png_size / 1000):,.1f}"],
        ["JPG (90% quality)",  f"{(jpg_size / 1000):,.1f}"]
    ], headers=["File Type", "Size (KB)"], stralign="right"))

    entropy = compute_image_entropy(image_data)
    print(tabulate([["Entropy", f"{entropy:.3f}"]]))

    compressor = qtc.ImageCompressor(image_data)

    last_iteration_count = 0
    results_table = []
    for iteration_count in iteration_counts:
        compressor.add_detail(iteration_count - last_iteration_count)
        last_iteration_count = iteration_count

        compressed_size = len(compressor.encode_to_binary())
        compressed_image = compressor.draw()

        # similarity_to_uncompressed = compute_image_similarity(image_data, compressed_image)
        # print(similarity_to_uncompressed)
        # print(mean_average_error(image_data, compressed_image))
        # print(root_mean_squared_error(image_data, compressed_image))

        error = mean_average_error(image_data, compressed_image)
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

    print(tabulate(results_table, headers=[
        "Iterations",
        "Compressed\nSize (KB)",
        "Mean Average\nError",
        "Size Reduction\nPNG (%)",
        "Size Reduction\nJPG (%)",
        "Compression\nFactor PNG",
        "Compression\nFactor JPG",
    ], stralign="right"))


# benchmark_image("input/flowers.jpg", iteration_counts=[100, 1000, 20000, 80000])
# benchmark_image("input/bug.png", iteration_counts=[100, 1000, 20000, 80000])
benchmark_image("input/flowers.jpg", iteration_counts=[100, 1000, 20000, 80000])
