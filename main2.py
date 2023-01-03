import numpy as np
from PIL import Image
from tqdm import tqdm, trange
from sortedcontainers import SortedListWithKey


# Image credits:
# flower.jpg: Photo by Lucía Garó on Unsplash
# mountain.jpg: Photo by Neha Maheen Mahfin on Unsplash

# TODO: Compressed data format

"""
Idea: create a minimal quad tree representation and then zip it

Format (based on tree traversal):
1. For each node store whether it is subdivided or not (position needn't be stored as it
   can be reconstructed from the tree structure
2. if it is not subdivided, then its color must be stored

As 1. is only a true / false, it theoretically only requires one bit, thus using a whole byte would be
a waste.
Solution: Store the subdivided bits and the colors separately (subdivided can then be densely packed)

Example:
true (root node is subdivided)
false (bottom left is not subdivided)
true (bottom right is subdivided) 
false (its bottom left is not subdivided) 
false (bottom right is not subdivided)
false (top left is not subdivided)
false (top right is not subdivided)
false (root node's top left is not subdivided)
false (top right not subdivided)

Formatted more neatly:
true (root)
    false
    true 
        false 
        false
        false
        false
    false
    false
    
Each leaf node has a color associated with it
=> In this case store 7 colors.
"""


class ImageCompressor:
    def __init__(self, image_data):
        self.areas = SortedListWithKey(key=lambda node: node.detail)
        self.simplified_image_data = np.zeros(image_data.shape, dtype=np.uint8)
        self.quad_count = 0
        self.root_node = QuadTreeNode(self, image_data, (0, 0))

    def register_area(self, quad_tree_node):
        self.areas.add(quad_tree_node)
        self.quad_count += 1

    def add_detail(self):
        if not self.areas:
            return

        node_with_highest_detail = self.areas.pop()
        node_with_highest_detail.subdivide_and_draw(self.simplified_image_data)


class QuadTreeNode:
    def __init__(self, compressor, image_data: np.array, position):
        self.compressor = compressor

        self.image_data = image_data
        self.position = position
        self.size = np.shape(image_data)[:2]

        self.average_color = np.mean(image_data, axis=(0, 1)).astype(np.uint8)
        # TODO: Why does the variance based approach not work?
        # Compute the detail as the sum of the variance of each channel (RGB)
        # self.detail = np.sum(np.var(image_data, axis=(0, 1)))
        self.detail = np.sum(np.std(image_data, axis=(0, 1))) * self.image_data.size

        self.is_subdivided = False
        self.bottom_left_node = None
        self.bottom_right_node = None
        self.top_left_node = None
        self.top_right_node = None

        compressor.register_area(self)

    def subdivide_and_draw(self, image: np.array):
        self.subdivide()
        self.bottom_left_node.draw(image)
        self.bottom_right_node.draw(image)
        self.top_left_node.draw(image)
        self.top_right_node.draw(image)

    def subdivide(self):
        height, width = self.size
        y, x = self.position

        if width <= 1 or height <= 1:
            return

        split_y = height // 2
        split_x = width // 2

        self.bottom_left_node = QuadTreeNode(
            self.compressor,
            self.image_data[:split_y, :split_x, ...],
            (y, x)
        )

        self.bottom_right_node = QuadTreeNode(
            self.compressor,
            self.image_data[:split_y, split_x:, ...],
            (y, x + split_x)
        )

        self.top_left_node = QuadTreeNode(
            self.compressor,
            self.image_data[split_y:, :split_x, ...],
            (y + split_y, x)
        )

        self.top_right_node = QuadTreeNode(
            self.compressor,
            self.image_data[split_y:, split_x:, ...],
            (y + split_y, x + split_x)
        )

        # Memory of the image is no longer needed as the relevant areas
        # have been passed on to the child nodes.
        self.image_data = None
        self.is_subdivided = True

    def draw(self, image: np.array):
        start_y, start_x = self.position
        height, width = self.size
        end_y = start_y + height
        end_x = start_x + width
        image[start_y: end_y, start_x: end_x] = self.average_color

    def extract_data(self, subdivided_flags: list, colors: list):
        subdivided_flags.append(self.is_subdivided)

        if self.is_subdivided:
            self.bottom_left_node.extract_data(subdivided_flags, colors)
            self.bottom_right_node.extract_data(subdivided_flags, colors)
            self.top_left_node.extract_data(subdivided_flags, colors)
            self.top_right_node.extract_data(subdivided_flags, colors)
        else:
            colors.append(self.average_color)


print("Loading image")
image = Image.open("flowers.jpg")

print("Processing")
image_data = np.array(image)

print("Starting compression")
compressor = ImageCompressor(image_data)

for i in trange(100000):
    compressor.add_detail()

print(f"Total: {compressor.quad_count} quads")

print("Showing image")
compressed = Image.fromarray(compressor.simplified_image_data)
compressed.show()

print("Encoding to binary")
import math

subdivided_flags = []
colors = []
compressor.root_node.extract_data(subdivided_flags, colors)

# Pad the flags to the nearest multiple of 8
count = len(subdivided_flags)
subdivided_flags.extend(False for i in range(8 - count % 8))
subdivided_byte_count = math.ceil(count / 8)

binary_data = []
for i in trange(subdivided_byte_count - 0):
    byte = 0

    for bit_index in range(8):
        if not subdivided_flags[i*8 + bit_index]:
            continue
        byte |= 1 << (7 - bit_index)

    # Is the endianness correct?
    binary_data.append(byte.to_bytes(1, "little", signed=False))

for color in colors:
    r, g, b = color
    r = int(r)
    g = int(g)
    b = int(b)
    binary_data.append(r.to_bytes(1, "little", signed=False))
    binary_data.append(g.to_bytes(1, "little", signed=False))
    binary_data.append(b.to_bytes(1, "little", signed=False))

blob = b"".join(binary_data)
print("Blob:")
# print(blob)
print(len(blob))

print("Zipped:")
import gzip
zipped_blob = gzip.compress(blob)
# print(zipped_blob)
print(len(zipped_blob))

print("LZMA:")
import lzma
lzma_blob = lzma.compress(blob)
print(len(lzma_blob))