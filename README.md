# Quadtree Image Compression

This library implements an image compression algorithm that is based on quadtrees. It can radically reduce the size of images while still preserving detail.

Features

- **Compressing** images and rendering the simplified version

- **Encoding** the compressed data to a compact binary representation

- **Decoding** the binary and reconstructing the image

The algorithm works by starting with an empty image and incrementally adding detail where it is important. At the beginning the compressed image is filled with the average color of the original image. Then, it recursively subdivides the regions that have the most detail into 4 quads that each have the average color of the area they represent in the original image.

![Subdivision Animation](docs/subdivision_animation.mp4)

How does the algorithm determine the amount of detail in a given quad region? The metric used is the standard deviation of the colors of the pixels in the region multiplied by the size of the region (simply the number of pixels `width * height`).

## Examples

| 100 Iterations           | 1000 Iterations           | 20000 Iterations           |
| ------------------------ | ------------------------- | -------------------------- |
| ![](docs/night_100.jpg)  | ![](docs/night_1000.jpg)  | ![](docs/night_20000.jpg)  |
| ![](docs/plant_100.jpg)  | ![](docs/plant_1000.jpg)  | ![](docs/plant_20000.jpg)  |
| ![](docs/sunset_100.jpg) | ![](docs/sunset_1000.jpg) | ![](docs/sunset_20000.jpg) |



Binary representation
Usage
Libraries
Benchmark
