import os
from io import BytesIO
import matplotlib.pyplot as plt
from PIL import Image as PILImage


def figure_to_pil_image(fig, dpi=150):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi)
    plt.close(fig)
    buf.seek(0)
    image = PILImage.open(buf)
    return image.copy()


def persist_or_cache_figure(fig, output_path=None, image_cache=None, category=None, name=None, save_to_disk=True, dpi=150):
    image = figure_to_pil_image(fig, dpi=dpi)

    if image_cache is not None and category is not None:
        image_cache.setdefault(category, []).append((name or "plot", image))

    if save_to_disk and output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)

    return image
