from skimage.io import imshow
from skimage.filters.rank import entropy as sk_entropy
from skimage.morphology import disk as sk_disk
from skimage.exposure import histogram as sk_histogram
from skimage.color import rgb2gray

import matplotlib.pyplot as plt
import numpy as np


def compute_channel_histogram_entropy(image_channel: np.array) -> float:
    histogram, _ = sk_histogram(image_channel, nbins=256, source_range="dtype")
    relative_occurrence = histogram / histogram.sum()
    return -(relative_occurrence * np.ma.log2(relative_occurrence)).sum()


np.random.seed(100)

random_image = (
       np.random.uniform(0, 255, (256, 256, 1))
       .astype(np.uint8)
       .repeat(3, axis=2)
)
plt.imshow(random_image)
plt.show()

smooth_gradient_image = (
    np.linspace(0, 255, 256)
    .astype(np.uint8)[:, np.newaxis, np.newaxis]
    .repeat(256, axis=1)
    .repeat(3, axis=2)
)
plt.imshow(smooth_gradient_image)
plt.show()

print("Random histogram entropy:", compute_channel_histogram_entropy(random_image[:, :, 0]))
print("Gradient histogram entropy:", compute_channel_histogram_entropy(smooth_gradient_image[:, :, 0]))

random_local_entropy = sk_entropy(random_image[:, :, 0], sk_disk(5))
gradient_local_entropy = sk_entropy(smooth_gradient_image[:, :, 0], sk_disk(5))

print("Random mean local entropy:", np.mean(random_local_entropy))
print("Gradient mean local entropy:", np.mean(gradient_local_entropy))

min_entropy = min(random_local_entropy.min(), gradient_local_entropy.min())
max_entropy = max(random_local_entropy.max(), gradient_local_entropy.max())

plt.imshow(random_local_entropy, cmap="plasma", vmin=min_entropy, vmax=max_entropy)
plt.colorbar()
plt.tight_layout()
plt.savefig("noise_entropy.jpg")
# plt.show()

plt.imshow(gradient_local_entropy, cmap="plasma", vmin=min_entropy, vmax=max_entropy)
plt.savefig("gradient_entropy.jpg")
# plt.show()

print(min_entropy, max_entropy)
