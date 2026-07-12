import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from image_utils import figure_to_pil_image, persist_or_cache_figure


def test_figure_to_pil_image_returns_image():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    image = figure_to_pil_image(fig, dpi=100)

    assert isinstance(image, Image.Image)
    assert image.size[0] > 0 and image.size[1] > 0


def test_persist_or_cache_figure_can_skip_disk(tmp_path):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    cache = {}
    image = persist_or_cache_figure(
        fig,
        output_path=str(tmp_path / "plot.png"),
        image_cache=cache,
        category="signals",
        name="sample",
        save_to_disk=False,
        dpi=100,
    )

    assert isinstance(image, Image.Image)
    assert "signals" in cache
    assert cache["signals"][0][0] == "sample"
    assert not os.path.exists(tmp_path / "plot.png")
