from PIL import Image
import quad_tree_compression as qtc
import numpy as np
from tqdm import tqdm


def animate_subdivision(image_path: str, iteration_counts: list):
    image = Image.open(image_path)
    image_data = np.array(image, dtype=np.uint8)

    compressor = qtc.ImageCompressor(image_data)

    last_iteration_count = 0
    frame = 0
    for iteration_count in tqdm(iteration_counts):
        frame += 1
        compressor.add_detail(iteration_count - last_iteration_count)
        last_iteration_count = iteration_count

        compressed_image = compressor.draw()
        Image.fromarray(compressed_image).save(f"animation/frame_{frame:0>4}.jpg")


# Command to convert the frames to a video:
# (Sometimes the scale parameter needs to be changed)
# ffmpeg -framerate 2 -i animation/frame_%04d.jpg -vf scale=1200:-1 -vcodec libx264 -pix_fmt yuv420p animation/animation.mp4


iteration_counts = [0, *range(10), *range(20, 100, 10), 200, 300, 500, 1000, *range(2000, 20000, 1000), 80000, 80000]
print(iteration_counts)
animate_subdivision("input/mountain.jpg", iteration_counts)
