from pkg_resources import resource_filename

import matplotlib.pyplot as plt
import matplotlib.image as img


def plot_results():
    """Plot my dog Ava."""

    # get stock image of Ava
    dog = resource_filename('cerf', 'data/figure_1.png')

    # read in PNG
    im = img.imread(dog)

    return plt.imshow(im)
