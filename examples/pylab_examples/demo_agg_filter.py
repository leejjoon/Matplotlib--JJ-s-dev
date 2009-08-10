import matplotlib.pyplot as plt

import numpy as np
import scipy.ndimage as NI
import matplotlib.cm as cm
import matplotlib.mlab as mlab

mmm = []

def gauss(im, dpi):
    "simple gauss filter"
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
    "enlarge the area"
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

    # Add white background to improve visibility of labels.
    white_glows = FilteredArtistList(cl, grow)
    ax.add_artist(white_glows)
    white_glows.set_zorder(cl[0].get_zorder()-0.1)

    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)


def drop_shadow_line(ax):
    # copyed from examples/misc/svg_filter_line.py

    # draw lines
    l1, = ax.plot([0.1, 0.5, 0.9], [0.1, 0.9, 0.5], "bo-",
                  mec="b", lw=5, ms=10, label="Line 1")
    l2, = ax.plot([0.1, 0.5, 0.9], [0.5, 0.2, 0.7], "r-",
                  mec="r", lw=5, ms=10, color="r", label="Line 2")

    #l1.set_rasterized(True) # to support mixed-mode renderers
    l1.set_visible(False)
    l2.set_visible(False)
    
    for l in [l1, l2]:

        # draw shadows with same lines with slight offset.

        xx = l.get_xdata()
        yy = l.get_ydata()
        shadow, = ax.plot(xx, yy)
        shadow.update_from(l)
        shadow.set_visible(True)

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

    

    
if 1:

    plt.figure(figsize=(6, 3))

    #ax = plt.subplot(121)
    #filtered_text(ax)

    ax = plt.subplot(122)
    drop_shadow_line(ax)
    
    plt.show()
