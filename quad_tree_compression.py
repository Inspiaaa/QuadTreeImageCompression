# Image processing
import numpy as np
from PIL import Image
import math

from sortedcontainers import SortedListWithKey

# Progress bar
from tqdm import trange

# Binary encoding and compression
from io import BytesIO
import lzma


# QuadTree data structures

class QuadTreeNode:
    """ Base quad tree data structure that handles the positioning, subdivision and rendering of nodes. """

    def __init__(self, position: tuple, size: tuple):
        self.position = position
        self.size = size

        self.color = None

        self.is_subdivided = False

        self.bottom_left_node = None
        self.bottom_right_node = None
        self.top_left_node = None
        self.top_right_node = None

    def _create_child_node(self, position, size):
        return QuadTreeNode(position, size)

    def subdivide(self):
        """ Splits the current quad into 4 child quads if this is possible.
        :return: Child quads or None or an empty list if it cannot be further subdivided.
        """
        if self.is_subdivided:
            return []

        width, height = self.size
        x, y = self.position

        if width <= 1 or height <= 1:
            return []

        self.is_subdivided = True

        split_width = width // 2
        split_height = height // 2

        self.bottom_left_node = self._create_child_node(
            (x, y),
            (split_width, split_height))

        self.bottom_right_node = self._create_child_node(
            (x + split_width, y),
            (width - split_width, split_height))

        self.top_left_node = self._create_child_node(
            (x, y + split_height),
            (split_width, height - split_height))

        self.top_right_node = self._create_child_node(
            (x + split_width, y + split_height),
            (width - split_width, height - split_height))

        return self.bottom_left_node, self.bottom_right_node, self.top_left_node, self.top_right_node

    def draw(self, image_data: np.array):
        if self.is_subdivided:
            self.bottom_left_node.draw(image_data)
            self.bottom_right_node.draw(image_data)
            self.top_left_node.draw(image_data)
            self.top_right_node.draw(image_data)
        else:
            self.draw_self(image_data)

    def draw_self(self, image_data: np.array):
        if self.color is None:
            return
        start_x, start_y = self.position
        width, height = self.size
        end_x = start_x + width
        end_y = start_y + height
        image_data[start_y: end_y, start_x: end_x] = self.color

    def use_average_leaf_color(self):
        if not self.is_subdivided:
            return

        self.bottom_left_node.use_average_leaf_color()
        self.bottom_right_node.use_average_leaf_color()
        self.top_left_node.use_average_leaf_color()
        self.top_right_node.use_average_leaf_color()

        self.color = tuple(np.mean([
            self.bottom_left_node.color,
            self.bottom_right_node.color,
            self.top_left_node.color,
            self.top_right_node.color
        ], axis=0))


class CompressNode (QuadTreeNode):
    """ QuadTree node used for incrementally compressing an image. """

    def __init__(self, position, image_data: np.array):
        height, width, _ = image_data.shape
        super().__init__(position, (width, height))

        self.image_data = image_data

        # Compute the detail as the sum of the standard deviation of each channel (RGB)
        # weighted by the number of pixels in this region.
        self.detail = np.sum(np.std(image_data, axis=(0, 1))) * self.image_data.size

        self.color = np.mean(image_data, axis=(0, 1)).astype(np.uint8)

    def _create_child_node(self, position, size):
        width, height = size
        child_x, child_y = position
        own_x, own_y = self.position

        start_x = child_x - own_x
        start_y = child_y - own_y
        return CompressNode(position, self.image_data[start_y: start_y + height, start_x: start_x + width])

    def subdivide(self):
        nodes = super().subdivide()
        # Memory of the image is no longer needed as the relevant areas
        # have been passed on to the child nodes.
        self.image_data = None
        return nodes

    def extract_data(self, subdivided_flags, colors):
        subdivided_flags.append(self.is_subdivided)

        if self.is_subdivided:
            self.bottom_left_node.extract_data(subdivided_flags, colors)
            self.bottom_right_node.extract_data(subdivided_flags, colors)
            self.top_left_node.extract_data(subdivided_flags, colors)
            self.top_right_node.extract_data(subdivided_flags, colors)
        else:
            r, g, b = self.color
            colors.append((int(r), int(g), int(b)))


class ReconstructNode (QuadTreeNode):
    """ QuadTree node for reconstructing a compressed image. """

    def __init__(self, position, size, subdivided_flags: list, colors: list):
        super().__init__(position, size)

        # Hint:
        # subdivided_flags and colors must be reversed!
        # (Improves performance, as popping a value off the back is faster than removing from the front)

        self._subdivided_flags = subdivided_flags
        self._colors = colors

        is_subdivided = subdivided_flags.pop()
        if is_subdivided:
            self.subdivide()
        else:
            self.color = colors.pop()

    def _create_child_node(self, position, size):
        return ReconstructNode(position, size, self._subdivided_flags, self._colors)


class ImageCompressor:
    """ Helper class that manages the CompressNodes and allows you to incrementally add detail. """

    def __init__(self, image_data: np.array):
        self.areas = SortedListWithKey(key=lambda node: node.detail)
        self._image_shape = image_data.shape
        self.height, self.width, _ = self._image_shape

        self.root_node = CompressNode((0, 0), image_data)
        self.areas.add(self.root_node)

    def add_detail(self, max_iterations: int = 1, detail_error_threshold: float = 100):
        iterations = 0

        for i in trange(max_iterations, leave=False):
            if not self.areas:
                break

            node_with_most_detail = self.areas.pop()
            for node in node_with_most_detail.subdivide():
                if node.detail > detail_error_threshold:
                    self.areas.add(node)

            if i > max_iterations:
                break

    def draw(self):
        new_image_data = np.zeros(self._image_shape, dtype=np.uint8)
        self.root_node.draw(new_image_data)
        return new_image_data

    def extract_data(self):
        subdivided_flags = []
        colors = []

        self.root_node.extract_data(subdivided_flags, colors)

        return subdivided_flags, colors

    def encode_to_binary(self) -> bytes:
        subdivided_flags, colors = self.extract_data()
        return encode_image_data(self.width, self.height, subdivided_flags, colors)


# Encoding / Decoding

def encode_uint32(number: int) -> bytes:
    return number.to_bytes(4, byteorder="little", signed=False)


def decode_uint32(data: bytes) -> int:
    return int.from_bytes(data, byteorder="little", signed=False)


def encode_uint8(number: int) -> bytes:
    return number.to_bytes(1, byteorder="little", signed=False)


def decode_uint8(data: bytes) -> int:
    return int.from_bytes(data, byteorder="little", signed=False)


def encode_bitset(boolean_flags: list, stream: BytesIO):
    # Encode the number of booleans
    stream.write(encode_uint32(len(boolean_flags)))

    # Encode the booleans
    # As each boolean only needs one bit, 8 booleans can be densely packed into a single byte.
    byte_count = math.ceil(len(boolean_flags) / 8)
    for byte_index in range(byte_count):
        byte = 0

        for bit_index in range(8):
            list_index = byte_index * 8 + bit_index
            if list_index >= len(boolean_flags) or not boolean_flags[list_index]:
                continue
            # Fill the byte from left to right
            byte |= 1 << bit_index

        stream.write(encode_uint8(byte))


def decode_bitset(stream: BytesIO) -> list:
    flag_count = decode_uint32(stream.read(4))
    boolean_flags = []

    byte_count = math.ceil(flag_count / 8)
    for byte_index in range(byte_count):
        byte = decode_uint8(stream.read(1))

        for bit_index in range(8):
            list_index = byte_index * 8 + bit_index
            if list_index >= flag_count:
                continue

            boolean_flags.append((byte & (1 << bit_index)) > 0)

    return boolean_flags


def encode_image_data(width: int, height: int, subdivided_flags: list, colors: list) -> bytes:
    stream = BytesIO()
    # Encode the image dimensions.
    stream.write(encode_uint32(width))
    stream.write(encode_uint32(height))

    # Encode the is_subdivided flags.
    encode_bitset(subdivided_flags, stream)

    # Encode the colors.
    for color in colors:
        r, g, b = color
        stream.write(encode_uint8(r))
        stream.write(encode_uint8(g))
        stream.write(encode_uint8(b))

    blob = stream.getvalue()
    return lzma.compress(blob)


def decode_image_data(compressed: bytes) -> tuple:
    stream = BytesIO(lzma.decompress(compressed))

    width = decode_uint32(stream.read(4))
    height = decode_uint32(stream.read(4))

    subdivided_flags = decode_bitset(stream)

    # Only the leaf nodes (nodes that are not subdivided => flag is False) can draw a color
    color_count = sum(0 if flag else 1 for flag in subdivided_flags)
    colors = []

    for i in range(color_count):
        r = decode_uint8(stream.read(1))
        g = decode_uint8(stream.read(1))
        b = decode_uint8(stream.read(1))
        colors.append((r, g, b))

    return width, height, subdivided_flags, colors


# Top-level compression and reconstruction functions

def compress_image_data(
        image_data: np.array,
        iterations: int = 20000,
        detail_error_threshold: float = 10) -> np.array:

    compressor = ImageCompressor(image_data)
    compressor.add_detail(iterations, detail_error_threshold)
    return compressor.draw()


def compress_and_encode_image_data(
        image_data: np.array,
        iterations: int = 20000,
        detail_error_threshold: float = 10) -> bytes:

    compressor = ImageCompressor(image_data)
    compressor.add_detail(iterations, detail_error_threshold)
    return compressor.encode_to_binary()


def reconstruct_quadtree(data: bytes) -> ReconstructNode:
    width, height, subdivided_flags, colors = decode_image_data(data)

    # The ReconstructNode requires these to be reversed for performance reasons.
    subdivided_flags = list(reversed(subdivided_flags))
    colors = list(reversed(colors))

    image_data = np.zeros((height, width, 3), dtype=np.uint8)
    return ReconstructNode((0, 0), (width, height), subdivided_flags, colors)


def reconstruct_image_data(data: bytes) -> np.array:
    tree = reconstruct_quadtree(data)
    width, height = tree.size

    image_data = np.zeros((height, width, 3), dtype=np.uint8)
    tree.draw(image_data)
    return image_data

# Simpler API

def compress_image_file(
        image_path: str,
        output_path: str,
        iterations: int = 20000,
        detail_error_threshold: float = 10):

    image = Image.open(image_path)
    image_data = np.array(image)

    data = compress_and_encode_image_data(image_data, iterations, detail_error_threshold)

    with open(output_path, "wb") as file:
        file.write(data)


def reconstruct_image_from_file(compressed_image_file: str) -> Image:
    with open(compressed_image_file, "rb") as file:
        data = file.read()

    image_data = reconstruct_image_data(data)
    return Image.fromarray(image_data)
