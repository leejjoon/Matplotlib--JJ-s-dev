import matplotlib.pyplot as plt

import numpy as np
import scipy.ndimage as NI
import matplotlib.cm as cm
import matplotlib.mlab as mlab

mmm = []

<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
def gauss(im, dpi):
=======
class BaseFilter(object):
    pass

class GaussianFilter(BaseFilter):
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
    "simple gauss filter"
<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
    pad = 5
    ny, nx, depth = im.shape
    new_alpha = np.zeros([pad*2+ny, pad*2+nx], dtype="d")
    new_alpha[pad:-pad, pad:-pad] = np.sum(im[:,:,:3]*[0.3,0.3,0.3], axis=-1)*im[:,:,-1]
    aaa = NI.grey_dilation(new_alpha, size=(3, 3))
    alpha2 = NI.gaussian_filter(aaa, 2)
    new_im = np.zeros([pad*2+ny, pad*2+nx, depth], dtype="d")
    new_im[:,:,-1] = alpha2
    new_im[:,:,:-1] = 0.
    offsetx, offsety = -pad, -pad
    mmm.append(im)
    return new_im, offsetx, offsety



def grow(im, dpi):
=======
    def __init__(self, sigma, alpha=0.3, offsets=None, color=None):
        self.sigma = sigma
        self.alpha = alpha
        if color is None:
            self.color=(0, 0, 0)
        else:
            self.color=color
        if offsets is None:
            self.offsets = (0, 0)
        else:
            self.offsets = offsets

    def __call__(self, im, dpi):
        pad = int(self.sigma*3)
        offsetx, offsety = int(self.offsets[0]), int(self.offsets[1])
        ny, nx, depth = im.shape
        new_im = np.empty([pad*2+ny, pad*2+nx, depth], dtype="d")
        alpha = new_im[:,:,3]
        alpha.fill(0.)
        alpha[pad+offsetx:-pad+offsetx, pad+offsety:-pad+offsety] = \
                                        im[:,:,-1]*self.alpha
        alpha2 = NI.gaussian_filter(alpha, self.sigma)
        new_im[:,:,-1] = alpha2
        new_im[:,:,:-1] = self.color
        
        return new_im, -pad, -pad



class GrowFilter(BaseFilter):
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
    "enlarge the area"
<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
    pad = 5
    ny, nx, depth = im.shape
    new_alpha = np.zeros([pad*2+ny, pad*2+nx], dtype="d")
    new_alpha[pad:-pad, pad:-pad] = im[:,:,-1]
    alpha2 = NI.grey_dilation(new_alpha, size=(3, 3))
    new_im = np.zeros([pad*2+ny, pad*2+nx, depth], dtype="d")
    new_im[:,:,-1] = alpha2
    new_im[:,:,:-1] = 1.
    offsetx, offsety = -pad, -pad
    return new_im, offsetx, offsety
=======
    def __init__(self, pixels, color=None):
        self.pixels = pixels
        if color is None:
            self.color=(1, 1, 1)
        else:
            self.color=color

    def __call__(self, im, dpi):
        pad = self.pixels
        ny, nx, depth = im.shape
        new_im = np.empty([pad*2+ny, pad*2+nx, depth], dtype="d")
        alpha = new_im[:,:,3]
        alpha.fill(0)
        alpha[pad:-pad, pad:-pad] = im[:,:,-1]
        alpha2 = NI.grey_dilation(alpha, size=(self.pixels, self.pixels))
        new_im[:,:,-1] = alpha2
        new_im[:,:,:-1] = self.color
        offsetx, offsety = -pad, -pad

        return new_im, offsetx, offsety
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py


from matplotlib.artist import Artist

class FilteredArtistList(Artist):
    """
    A simple container to draw filtered artist.
    """
    def __init__(self, artist_list, filter):
        self._artist_list = artist_list
        self._filter = filter
        Artist.__init__(self)
        
    def draw(self, renderer):
        renderer.start_rasterizing()
        renderer.start_filter()
        for a in self._artist_list:
            a.draw(renderer)
        renderer.stop_filter(self._filter)
        renderer.stop_rasterizing()



import matplotlib.transforms as mtransforms

def filtered_text(ax):
    # mostly copied from contour_demo.py

    # prepare image
    delta = 0.025
    x = np.arange(-3.0, 3.0, delta)
    y = np.arange(-2.0, 2.0, delta)
    X, Y = np.meshgrid(x, y)
    Z1 = mlab.bivariate_normal(X, Y, 1.0, 1.0, 0.0, 0.0)
    Z2 = mlab.bivariate_normal(X, Y, 1.5, 0.5, 1, 1)
    # difference of Gaussians
    Z = 10.0 * (Z2 - Z1)


    # draw
    im = ax.imshow(Z, interpolation='bilinear', origin='lower',
                   cmap=cm.gray, extent=(-3,3,-2,2))
    levels = np.arange(-1.2, 1.6, 0.2)
    CS = ax.contour(Z, levels,
                    origin='lower',
                    linewidths=2,
                    extent=(-3,3,-2,2))

    ax.set_aspect("auto")
    
    # contour label
    cl = ax.clabel(CS, levels[1::2],  # label every second level
                   inline=1,
                   fmt='%1.1f',
                   fontsize=11)

    # change clable color to black
    for t in cl:
        t.set_color("k")

<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
    # Add white background to improve visibility of labels.
    white_glows = FilteredArtistList(cl, grow)
=======
    # Add white glows to improve visibility of labels.
    white_glows = FilteredArtistList(cl, GrowFilter(3))
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
    ax.add_artist(white_glows)
    white_glows.set_zorder(cl[0].get_zorder()-0.1)

    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)


def drop_shadow_line(ax):
    # copyed from examples/misc/svg_filter_line.py

    # draw lines
    l1, = ax.plot([0.1, 0.5, 0.9], [0.1, 0.9, 0.5], "bo-",
<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
                  mec="b", lw=5, ms=10, label="Line 1")
    l2, = ax.plot([0.1, 0.5, 0.9], [0.5, 0.2, 0.7], "r-",
                  mec="r", lw=5, ms=10, color="r", label="Line 2")
=======
                  mec="b", mfc="w", lw=5, mew=3, ms=10, label="Line 1")
    l2, = ax.plot([0.1, 0.5, 0.9], [0.5, 0.2, 0.7], "ro-",
                  mec="r", mfc="w", lw=5, mew=3, ms=10, label="Line 1")
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py

<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
    #l1.set_rasterized(True) # to support mixed-mode renderers
    l1.set_visible(False)
    l2.set_visible(False)
=======
    
    gauss = GaussianFilter(2)
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
    
    for l in [l1, l2]:

        # draw shadows with same lines with slight offset.

        xx = l.get_xdata()
        yy = l.get_ydata()
        shadow, = ax.plot(xx, yy)
        shadow.update_from(l)
<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
        shadow.set_visible(True)
=======
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py

        # offset transform
        ot = mtransforms.offset_copy(l.get_transform(), ax.figure,
                                     x=4.0, y=-6.0, units='points')

        shadow.set_transform(ot)


        # adjust zorder of the shadow lines so that it is drawn below the
        # original lines
        shadow.set_zorder(l.get_zorder()-0.5)
        shadow.set_agg_filter(gauss)
        shadow.set_rasterized(True) # to support mixed-mode renderers
        


    ax.set_xlim(0., 1.)
    ax.set_ylim(0., 1.)

    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
=======



def drop_shadow_patches(ax):
    # copyed from barchart_demo.py
    N = 5
    menMeans = (20, 35, 30, 35, 27)

    ind = np.arange(N)  # the x locations for the groups
    width = 0.35       # the width of the bars

    rects1 = ax.bar(ind, menMeans, width, color='r', ec="w", lw=2)

    womenMeans = (25, 32, 34, 20, 25)
    rects2 = ax.bar(ind+width+0.1, womenMeans, width, color='y', ec="w", lw=2)

    gauss = GaussianFilter(1.5, offsets=(1,1), )
    shadow = FilteredArtistList(rects1+rects2, gauss)
    ax.add_artist(shadow)
    shadow.set_zorder(rects1[0].get_zorder()-0.1)

    ax.set_xlim(ind[0]-0.5, ind[-1]+1.5)
    ax.set_ylim(0, 40)
    
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
    

    
if 1:

<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
    plt.figure(figsize=(6, 3))
=======
    plt.figure(figsize=(8, 3))
    plt.subplots_adjust(left=0.05, right=0.95)
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py

<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
    #ax = plt.subplot(121)
    #filtered_text(ax)
=======
    ax = plt.subplot(131)
    filtered_text(ax)
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py

<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
    ax = plt.subplot(122)
=======
    ax = plt.subplot(132)
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
    drop_shadow_line(ax)
<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
=======

    ax = plt.subplot(133)
    drop_shadow_patches(ax)
>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
    
    plt.show()
<<<<<<< HEAD:examples/pylab_examples/demo_agg_filter.py
=======


>>>>>>> agg_filter:examples/pylab_examples/demo_agg_filter.py
