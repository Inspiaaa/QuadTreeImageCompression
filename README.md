# Quadtree Image Compression

This library implements an image compression algorithm that is based on quadtrees. It can radically reduce the size of images while still preserving detail.

Features

- **Compressing** images and rendering the simplified version

- **Encoding** the compressed data to a compact binary representation

- **Decoding** the binary and reconstructing the image

The algorithm works by starting with an empty image and **incrementally adding detail** where it is important. At the beginning the compressed image is filled with the average color of the original image. Then, it recursively **subdivides** the regions that have the most detail into 4 quads that each have the average color of the area they represent in the original image.

https://user-images.githubusercontent.com/28511584/211117608-29ff4349-64de-4250-a7fa-931b76a1392b.mp4

How does the algorithm determine the **amount of detail** in a given quad region? The metric used is the standard deviation of the colors of the pixels in the region multiplied by the size of the region (simply the number of pixels `width * height`). If all the pixels have the same color, then the standard deviation is 0, meaning that it does not need to be divided any further. If there are many different colors over a large area, than the detail metric will have a high value.

## Examples

| 100 Iterations           | 1000 Iterations           | 20000 Iterations           |
| ------------------------ | ------------------------- | -------------------------- |
| ![](docs/night_100.jpg)  | ![](docs/night_1000.jpg)  | ![](docs/night_20000.jpg)  |
| ![](docs/plant_100.jpg)  | ![](docs/plant_1000.jpg)  | ![](docs/plant_20000.jpg)  |
| ![](docs/sunset_100.jpg) | ![](docs/sunset_1000.jpg) | ![](docs/sunset_20000.jpg) |

## Usage

To use the quadtree image compression algorithm, simply copy the `quad_tree_compression.py` and import into your scripts. It requires `numpy`, `Pillow`, `tqdm` and `sortedcontainers` to be installed. If you also want to run the image benchmark (`benchmark.py`), you will also need `scikit-image` which is used for analysing the input image.

The `quad_tree_compression` file provides easy helper functions for performing common operations (such as compressing and loading images) but also gives you access to the underlying classes.

Compressing and loading an image:

```python
from quad_tree_compression import compress_image_file, reconstruct_image_from_file

# Compress the image and encode is a binary file (any file extension can be chosen)
compress_image_file("input/mountain.jpg", "output/mountain_qt.qid", iterations=20_000)

# Reconstruct the image from the binary file. (Returns a PIL.Image object)
image = reconstruct_image_from_file("output/mountain_qt.qid")
image.show()
```

Using the compressed image data (a numpy array) directly:

```python
from quad_tree_compression import compress_image_data
from PIL import Image
import numpy as np

# Load the image and convert it to a numpy array
image = Image.open("input/mountain.jpg")
image_data = np.array(image)

# Compress the image
compressed_data = compress_image_data(image_data, iterations=20_000)

# Show the simplified image
compressed_image = Image.fromarray(compressed_data)
compressed_image.show()
```

Working with the binary representation directly:

```python
from quad_tree_compression import compress_and_encode_image_data, reconstruct_image_data
from PIL import Image
import numpy as np

# Load the image and convert it to a numpy array
image = Image.open("input/mountain.jpg")
image_data = np.array(image)

# Compress the image and encode it to the binary representation (a "bytes" object).
compressed_binary = compress_and_encode_image_data(image_data, iterations=20_000)

# Decode the compressed binary and convert it to a numpy array
compressed_image_data = reconstruct_image_data(compressed_binary)

# Show the simplified image
compressed_image = Image.fromarray(compressed_image_data)
compressed_image.show()
```

Advanced: interacting with the image compressing class directly:

```python
from quad_tree_compression import ImageCompressor
from PIL import Image
import numpy as np

# Load the image and convert it to a numpy array
image = Image.open("input/mountain.jpg")
image_data = np.array(image)

# Create a new ImageCompressor which allows you to incrementally add detail
compressor = ImageCompressor(image_data)

# Perform 10000 iterations
compressor.add_detail(10_000)

# Render the compressed image to a numpy array and display it
compressed_data = compressor.draw()
compressed_image = Image.fromarray(compressed_data)
compressed_image.show()

# Perform another 50000 iterations (total is 60000 then)
compressor.add_detail(50_000)

# Convert the output to a compressed binary representation
compressed_binary = compressor.encode_to_binary()
```

Advanced: Interacting with the underlying quadtree datastructure:

Internally, there are three classes that are used for compressing and reconstructing images. The base class `QuadTreeNode` takes care of positioning, sizing and subdividing. When compressing the image, the `CompressNode` class is used (which inherits from `QuadTreeNode`). When reconstructing the image, the `ReconstructNode` class is used (which also inherits from `QuadTreeNode`).

```python
from quad_tree_compression import ImageCompressor, reconstruct_quadtree
from PIL import Image
import numpy as np

# ...

compressor = ImageCompressor(image_data)
compressor.add_detail(10_000)

# You can access the compression quadtree directly 
# (type: CompressNode which is a subclass of the QuadTreeNode class)
tree = compressor.root_node
print(tree)
print(tree.top_left_node)
print(tree.color)

# ...

# When you are loadinng the tree from the binary representation, you 
# can also access the quadtree:
# (type: ReconstructNode which is a subclass of the QuadTreeNode class)
tree = reconstruct_quadtree(compressed_binary_data)
print(tree)
```

Binary representation
Benchmark
