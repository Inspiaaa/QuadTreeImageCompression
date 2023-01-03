import numpy as np
from PIL import Image
from tqdm import tqdm, trange
from sortedcontainers import SortedListWithKey


# Image credits:
# flower.jpg: Photo by Lucía Garó on Unsplash
# mountain.jpg: Photo by Neha Maheen Mahfin on Unsplash


class ImageCompressor:
    def __init__(self, image_data):
        self.areas = SortedListWithKey(key=lambda node: node.detail)
        self.simplified_image_data = np.zeros(image_data.shape, dtype=np.uint8)
        QuadTreeNode(self, image_data, (0, 0))

    def register_area(self, quad_tree_node):
        self.areas.add(quad_tree_node)

    def add_detail(self):
        if not self.areas:
            return

        node_with_highest_detail = self.areas.pop()
        node_with_highest_detail.draw(self.simplified_image_data)
        node_with_highest_detail.subdivide()


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

        self.bottom_left_node = None
        self.bottom_right_node = None
        self.top_left_node = None
        self.top_right_node = None

        compressor.register_area(self)

    def subdivide(self):
        height, width = self.size
        y, x = self.position

        if width <= 1 or height <= 1:
            self.image_data = None
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

    def draw(self, image: np.array):
        start_y, start_x = self.position
        height, width = self.size
        end_y = start_y + height
        end_x = start_x + width
        image[start_y: end_y, start_x: end_x] = self.average_color


print("Loading image")
image = Image.open("mountain.jpg")

print("Processing")
image_data = np.array(image)

print("Starting compression")
compressor = ImageCompressor(image_data)

for i in trange(10000):
    compressor.add_detail()

print("Showing image")
compressed = Image.fromarray(compressor.simplified_image_data)
compressed.show()
