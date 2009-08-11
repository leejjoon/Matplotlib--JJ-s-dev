
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
from matplotlib.image import BboxImage
import numpy as np
from matplotlib.transforms import Affine2D, IdentityTransform

import matplotlib.font_manager as font_manager
from matplotlib.ft2font import FT2Font, KERNING_DEFAULT, LOAD_NO_HINTING
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
import matplotlib.patches as mpatches

from matplotlib.collections import CircleCollection


from matplotlib.offsetbox import AnnotationBbox,\
     AnchoredOffsetbox, AuxTransformBox

#from matplotlib.offsetbox import

from matplotlib.cbook import get_sample_data

import matplotlib as mpl
import matplotlib.cm as cm

mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 12
mpl.rcParams['axes.edgecolor'] = 'gray'


axalpha = 0.05
#figcolor = '#EFEFEF'
figcolor = 'white'
dpi = 80
fig = plt.figure(figsize=(6, 1.1),dpi=dpi)
fig.figurePatch.set_edgecolor(figcolor)
fig.figurePatch.set_facecolor(figcolor)


def add_math_background():
    ax = fig.add_axes([0., 0., 1., 1.])

    text = []
    text.append((r"$W^{3\beta}_{\delta_1 \rho_1 \sigma_2} = U^{3\beta}_{\delta_1 \rho_1} + \frac{1}{8 \pi 2} \int^{\alpha_2}_{\alpha_2} d \alpha^\prime_2 \left[\frac{ U^{2\beta}_{\delta_1 \rho_1} - \alpha^\prime_2U^{1\beta}_{\rho_1 \sigma_2} }{U^{0\beta}_{\rho_1 \sigma_2}}\right]$", (0.7, 0.2), 20))
    text.append((r"$\frac{d\rho}{d t} + \rho \vec{v}\cdot\nabla\vec{v} = -\nabla p + \mu\nabla^2 \vec{v} + \rho \vec{g}$",
                (0.35, 0.9), 20))
    text.append((r"$\int_{-\infty}^\infty e^{-x^2}dx=\sqrt{\pi}$",
                (0.15, 0.3), 25))
    #text.append((r"$E = mc^2 = \sqrt{{m_0}^2c^4 + p^2c^2}$",
    #            (0.7, 0.42), 30))
    text.append((r"$F_G = G\frac{m_1m_2}{r^2}$",
                (0.85, 0.7), 30))
    for eq, (x, y), size in text:
        ax.text(x, y, eq, ha='center', va='center', color="#11557c", alpha=0.25,
                transform=ax.transAxes, fontsize=size)
    ax.set_axis_off()
    return ax

def add_matplotlib_text(ax):

    logo_text, logo_size = 'matplotlib', 65
    shadow1 = TextPatch((3, -2), logo_text, fc="none", ec="0.7", lw=2,
                        transform=IdentityTransform(), size=logo_size)
    shadow2 = TextPatch((3, -2), logo_text, fc="0.5", ec="none", lw=1,
                        transform=IdentityTransform(), size=logo_size)

    arr = np.arange(256).reshape(1,256)/256.
    text_path1 = TextPatch((0, 0), logo_text, fc="w", ec=(1., 0.7, 0.5, 0.5), lw=5,
                           transform=IdentityTransform(), size=logo_size)
    text_path2 = TextPatch((0, 0), logo_text, fc="w", ec="w", lw=1,
                           transform=IdentityTransform(), size=logo_size)
    text_path3 = TextPatchEffect((0, 0), logo_text, fc="none", ec="b", lw=1,
                                 transform=IdentityTransform(), size=logo_size)

    # make offset box
    offsetbox = AuxTransformBox(IdentityTransform())
    offsetbox.add_artist(shadow1)
    offsetbox.add_artist(shadow2)
    offsetbox.add_artist(text_path1)
    offsetbox.add_artist(text_path2)
    offsetbox.add_artist(text_path3)

    # place the anchored offset box using AnnotationBbox
    ab = AnnotationBbox(offsetbox, (0.95, 0.5),
                        xycoords='data',
                        boxcoords="offset points",
                        box_alignment=(1.,0.5),
                        )
    ab.patch.set_visible(False)

    ax.add_artist(ab)


def add_polar_bar():
    ax = fig.add_axes([0.025, 0.075, 0.2, 0.85], polar=True, resolution=50)


    ax.axesPatch.set_alpha(axalpha)
    ax.set_axisbelow(True)
    N = 7
    arc = 2. * np.pi
    theta = np.arange(0.0, arc, arc/N)
    radii = 10 * np.array([0.2, 0.6, 0.8, 0.7, 0.4, 0.5, 0.8])
    width = np.pi / 4 * np.array([0.4, 0.4, 0.6, 0.8, 0.2, 0.5, 0.3])
    bars = ax.bar(theta, radii, width=width, bottom=0.0)
    for r, bar in zip(radii, bars):
        bar.set_facecolor(cm.jet(r/10.))
        bar.set_alpha(0.6)

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_visible(False)

    for line in ax.get_ygridlines() + ax.get_xgridlines():
        line.set_lw(0.8)
        line.set_alpha(0.9)
        line.set_ls('-')
        line.set_color('0.5')

    ax.set_yticks(np.arange(1, 9, 2))
    ax.set_rmax(9)





class TextPatch(mpatches.PathPatch):

    FONT_SCALE = 100.

    def __init__(self, xy, s, size=None, prop=None, bbox_image=None,
                 *kl, **kwargs):
        if prop is None:
            prop = FontProperties()

        if size is None:
            size = prop.get_size_in_points()

        self._xy = xy
        self.set_size(size)

        self.text_path = self.text_get_path(prop, s)

        mpatches.PathPatch.__init__(self, self.text_path, *kl, **kwargs)

        self._init_bbox_image(bbox_image)


    def _init_bbox_image(self, im):

        if im is None:
            self.bbox_image = None
        else:
            bbox_image = BboxImage(self.get_window_extent,
                                   norm = None,
                                   origin=None,
                                   )
            bbox_image.set_transform(IdentityTransform())

            bbox_image.set_data(im)
            self.bbox_image = bbox_image

    def draw(self, renderer=None):

        if self.bbox_image is not None:
            # the clip path must be updated every draw. any solution? -JJ
            self.bbox_image.set_clip_path(self.text_path, self.get_transform())
            self.bbox_image.draw(renderer)

        mpatches.PathPatch.draw(self, renderer)


    def set_size(self, size):
        self._size = size

    def get_size(self):
        return self._size

    def get_patch_transform(self):
        tr = Affine2D().scale(self._size/self.FONT_SCALE, self._size/self.FONT_SCALE)
        return tr.translate(*self._xy)

    def glyph_char_path(self, glyph, currx=0.):

        verts, codes = [], []
        for step in glyph.path:
            if step[0] == 0:   # MOVE_TO
                verts.append((step[1], step[2]))
                codes.append(Path.MOVETO)
            elif step[0] == 1: # LINE_TO
                verts.append((step[1], step[2]))
                codes.append(Path.LINETO)
            elif step[0] == 2: # CURVE3
                verts.extend([(step[1], step[2]),
                               (step[3], step[4])])
                codes.extend([Path.CURVE3, Path.CURVE3])
            elif step[0] == 3: # CURVE4
                verts.extend([(step[1], step[2]),
                              (step[3], step[4]),
                              (step[5], step[6])])
                codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])
            elif step[0] == 4: # ENDPOLY
                verts.append((0, 0,))
                codes.append(Path.CLOSEPOLY)

        verts = [(x+currx, y) for (x,y) in verts]

        return verts, codes


    def text_get_path(self, prop, s):

        fname = font_manager.findfont(prop)
        font = FT2Font(str(fname))

        font.set_size(self.FONT_SCALE, 72)

        cmap = font.get_charmap()
        lastgind = None

        currx = 0

        verts, codes = [], []

        for c in s:

            ccode = ord(c)
            gind = cmap.get(ccode)
            if gind is None:
                ccode = ord('?')
                gind = 0
            glyph = font.load_char(ccode, flags=LOAD_NO_HINTING)


            if lastgind is not None:
                kern = font.get_kerning(lastgind, gind, KERNING_DEFAULT)
            else:
                kern = 0
            currx += (kern / 64.0) #/ (self.FONT_SCALE)

            verts1, codes1 = self.glyph_char_path(glyph, currx)
            verts.extend(verts1)
            codes.extend(codes1)


            currx += (glyph.linearHoriAdvance / 65536.0) #/ (self.FONT_SCALE)
            lastgind = gind

        return Path(verts, codes)



class TextPatchEffect(TextPatch):
    def draw_effect(self, renderer):
        transformed_path = self.get_transform().transform_path(self.text_path)
        offsets = transformed_path.vertices[::4]
        def get_color(offsets):
            offsetx = offsets[:,0]
            minx, maxx = min(offsetx), max(offsetx)
            x = (offsetx - minx)/(maxx-minx)
            #return [0.9, 0.9, 0.9, 0.], plt.cm.jet(x)*[1, 1, 1, 0.5]
            return plt.cm.jet(x)*[1, 1, 1, 0.1], plt.cm.jet(x)*[1, 1, 1, .4]
            
        facecolors, edgecolors = get_color(offsets)

        circs = CircleCollection(np.ones(len(offsets))*500,
                                 facecolors=facecolors,
                                 edgecolors=edgecolors,
                                 offsets=offsets,
                                 transOffset=IdentityTransform())
        circs.set_axes(self.axes)
        circs.set_figure(self.figure)
        circs.set_clip_path(self.text_path, self.get_transform())
        circs.draw(renderer)
        
    def draw(self, renderer=None):

#         if self.bbox_image is not None:
#             # the clip path must be updated every draw. any solution? -JJ
#             self.bbox_image.set_clip_path(self.text_path, self.get_transform())
#             self.bbox_image.draw(renderer)
        self.draw_effect(renderer)

        mpatches.PathPatch.draw(self, renderer)

if __name__ == '__main__':
    main_axes = add_math_background()
    add_polar_bar()
    add_matplotlib_text(main_axes)
    plt.show()

if 0:

    fig = plt.figure(1)

    # EXAMPLE 1

    ax = plt.subplot(211)

    from matplotlib._png import read_png
    fn = get_sample_data("lena.png", asfileobj=False)
    arr = read_png(fn)
    p = TextPatch((0, 0), "!?", size=150, fc="none", ec="k",
                  bbox_image=arr,
                  transform=IdentityTransform())
    p.set_clip_on(False)

    # make offset box
    offsetbox = AuxTransformBox(IdentityTransform())
    offsetbox.add_artist(p)

    # make anchored offset box
    ao = AnchoredOffsetbox(loc=2, child=offsetbox, frameon=True, borderpad=0.2)

    ax.add_artist(ao)



    # EXAMPLE 2

    ax = plt.subplot(212)

    shadow1 = TextPatch((3, -2), "TextPath", size=70, fc="none", ec="0.6", lw=3,
                   transform=IdentityTransform())
    shadow2 = TextPatch((3, -2), "TextPath", size=70, fc="0.3", ec="none",
                   transform=IdentityTransform())

    arr = np.arange(256).reshape(1,256)/256.
    text_path = TextPatch((0, 0), "TextPath", size=70, fc="none", ec="none", lw=1,
                          bbox_image=arr,
                          transform=IdentityTransform())

    # make offset box
    offsetbox = AuxTransformBox(IdentityTransform())
    #offsetbox.add_artist(shadow1)
    #offsetbox.add_artist(shadow2)
    offsetbox.add_artist(text_path)

    # place the anchored offset box using AnnotationBbox
    ab = AnnotationBbox(offsetbox, (0.5, 0.5),
                        xycoords='data',
                        boxcoords="offset points",
                        box_alignment=(0.5,0.5),
                        )


    ax.add_artist(ab)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)





    plt.draw()
    plt.show()
