from __future__ import division
from cStringIO import StringIO

from matplotlib import verbose
from matplotlib.backend_bases import RendererBase, GraphicsContextBase,\
     FigureManagerBase, FigureCanvasBase, error_msg

from matplotlib.cbook import True, False
from matplotlib.colors import rgb2hex
from matplotlib.figure import Figure
from matplotlib.font_manager import fontManager
from matplotlib.ft2font import FT2Font
from matplotlib._matlab_helpers import Gcf
from matplotlib import rcParams

try: from matplotlib.mathtext import math_parse_s_ft2font_svg
except ImportError:
    print >>sys.stderr, 'backend_svg could not import mathtext (build with ft2font)'
    useMathText = False
else: useMathText = True

import sys,os,math

def _nums_to_str(seq, fmt='%1.3f'):
    return ' '.join([_int_or_float(val, fmt) for val in seq])

def draw_if_interactive():
    pass

def show():
    """
    Show all the figures and enter the gtk mainloop

    This should be the last line of your script
    """
    pass

def new_figure_manager(num, *args):
    thisFig = Figure(*args)
    canvas = FigureCanvasSVG(thisFig)
    manager = FigureManagerSVG(canvas, num)
    return manager


_fontd = {}
_clipd = {}
class RendererSVG(RendererBase):
    def __init__(self, width, height, svgwriter, basename='_svg'):
        # use basename to generate image files
        self._svgwriter = svgwriter
        self.width=width
        self.height=height
        self.basename = basename
        self._groupd = {}
        self._imaged = {} 

    def flipy(self):
        'return true if y small numbers are top for renderer'
        return True

    def get_canvas_width_height(self):
        'return the canvas width and height in display coords'
        return self.width, self.height

    def draw_image(self, x, y, im, origin, bbox):
        self._imaged[self.basename] = self._imaged.get(self.basename,0) + 1
        imName = '%s.image%d.png'%(self.basename, self._imaged[self.basename])
        verbose.report( 'Writing image file for include: %s' % imName)
        im.write_png(imName)
        width = bbox.width()
        height = bbox.height()
    
        svg = """
<image xlink:href="%(imName)s"
  x="%(x)f" y="%(y)f"
  width="%(width)f" height="%(height)f"
/>""" % locals()
        self._draw_rawsvg(svg)
          
        
    def _draw_rawsvg(self, svg):
        self._svgwriter.write(svg)

    def _get_font(self, prop):
        key = hash(prop)
        font = _fontd.get(key)
        if font is None:
            fname = fontManager.findfont(prop)
            try:
                font = FT2Font(str(fname))
            except RuntimeError, msg:
                verbose.report_error('Could not load filename for text "%s"'%fname)
                return None
            else:
                _fontd[key] = font
        font.clear()
        size = prop.get_size_in_points()
        font.set_size(size, 72.0)
        return font


    def get_text_width_height(self, s, prop, ismath):
        """
        get the width and height in display coords of the string s
        with FontPropertry prop
        """
        if ismath and useMathText:
            width, height, glyphs = math_parse_s_ft2font_svg(
                s, 72, prop.get_size_in_points())
            return width, height
        font = self._get_font(prop)
        font.set_text(s, 0.0)
        w, h = font.get_width_height()
        w /= 64.0  # convert from subpixels
        h /= 64.0
        return w, h

    def open_group(self, s):
        'open a grouping element with label s'

        self._groupd[s] = self._groupd.get(s,0) + 1
        svg = '<g id="%s%d">\n' % (s, self._groupd[s])
        self._draw_rawsvg(svg)

    def close_group(self, s):
        'close a grouping element with label s'
        self._draw_rawsvg('</g>\n')

    def draw_arc(self, gc, rgbFace, x, y, width, height, angle1, angle2):  #for now, draws a circle of diameter width
        """
        Draw a circle at x,y of diameter 'width'
        """
        type = '<circle '
        details = ' cx="%f" \n cy="%f" \n r="%f"\n' % (x,self.height-y,width/2)
        self._draw_svg(type, details, gc, rgbFace)

    def draw_line(self, gc, x1, y1, x2, y2):
        """
        Draw a single line from x1,y1 to x2,y2
        """
        type = '<path '
        details = ' d="M %f,%f L %f,%f" ' % (x1,self.height-y1,x2,self.height-y2)
        self._draw_svg(type, details, gc, None)

    def draw_lines(self, gc, x, y):
        """
        x and y are equal length arrays, draw lines connecting each
        point in x, y
        """

        if len(x)==0: return
        if len(x)!=len(y): error_msg('x and y must be the same length')
        type = '<path '

        y = self.height - y
        details = [' d="M %f,%f' % (x[0], y[0]) ]
        xys = zip(x[1:], y[1:])
        details.extend(['L %f,%f' % tup for tup in xys])
        details.append('" ')
        details = ' '.join(details)
        self._draw_svg(type, details, gc, None)

    def draw_rectangle(self, gc, rgbFace, x, y, width, height):
        type = '<rect '
        details = 'width="%f" height="%f" x="%f" y="%f" ' % (width, height, x, self.height-y-height)
        self._draw_svg(type, details, gc, rgbFace)

    def draw_polygon(self, gc, rgbFace, points):
        type = '<polygon '        
        details = '   points = "%s"' % ' '.join(['%f,%f'%(x,self.height-y) for x, y in points])
        self._draw_svg(type, details, gc, rgbFace)

    def draw_point(self, gc, x, y):
        """
        Draw a point at x,y
        """
        self.draw_arc(gc, gc.get_rgb(), x, y, 1, 0, 0, 0)  # result seems to have a hole in it...

    def draw_mathtext(self, gc, x, y, s, prop, angle):
        """
        Draw math text using matplotlib.mathtext
        """
        fontsize = prop.get_size_in_points()
        width, height, svg_glyphs = math_parse_s_ft2font_svg(s, 72, fontsize)
        color = rgb2hex(gc.get_rgb())

        svg = ""
        self.open_group("mathtext")
        for fontname, fontsize, num, ox, oy, metrics in svg_glyphs:
            thetext=unichr(num)
            thetext.encode('utf-8')
            style = 'font-size: %f; font-family: %s; stroke-width: 0.5; stroke: %s; fill: %s;'%(fontsize, fontname, color, color)
            if angle!=0:
                transform = 'transform="translate(%f,%f) rotate(%1.1f) translate(%f,%f)"' % (x,y,-angle,-x,-y) # Inkscape doesn't support rotate(angle x y)
            else: transform = ''
            newx, newy = x+ox, y-oy
            svg += """\
<text style="%(style)s" x="%(newx)f" y="%(newy)f" %(transform)s>%(thetext)s</text>
""" % locals()

        self._draw_rawsvg(svg.encode('utf-8'))
        self.close_group("mathtext")

    def draw_text(self, gc, x, y, s, prop, angle, ismath):
        """
        draw text
        """
        if ismath and useMathText:
             return self.draw_mathtext(gc, x, y, s, prop, angle)
        
        font = self._get_font(prop)

        fontsize = prop.get_size_in_points()
        
        thetext = '%s' % s
        fontname = font.get_sfnt()[(1,0,0,6)]
        fontsize = prop.get_size_in_points()
        color = rgb2hex(gc.get_rgb())
        style = 'font-size: %f; font-family: %s; stroke-width: 0.5; stroke: %s; fill: %s;'%(fontsize, fontname, color, color)
        #style = 'font-size: %f; font-family: %s; stroke: %s;'%(fontsize, fontname, color)
        if angle!=0:
            transform = 'transform="translate(%f,%f) rotate(%1.1f) translate(%f,%f)"' % (x,y,-angle,-x,-y) # Inkscape doesn't support rotate(angle x y)
        else: transform = ''


        svg = """\
<text style="%(style)s" x="%(x)f" y="%(y)f" %(transform)s>
  %(thetext)s
</text>
""" % locals()
        self._draw_rawsvg(svg)


    def get_svg(self):
        return self._svgwriter.getvalue()

    def finish(self):
        self._svgwriter.write('</svg>')

    def new_gc(self):
        return GraphicsContextSVG()

    def _draw_svg(self, type, details, gc, rgbFace):
        if rgbFace is not None:
            rgbhex='fill: %s; '%rgb2hex(rgbFace)
        else:
            rgbhex='fill: none; '
        style = self._get_gc_props_svg(gc)
        cliprect,id = self._get_gc_clip_svg(gc)
        if id is not None:  clippath = ' clip-path:url(#%s); ' % id
        else: clippath = ''

        if len(cliprect) and id is not None: header = cliprect + type
        else: header = type

        svg = """\
%(header)s        
style="%(style)s %(rgbhex)s %(clippath)s "
%(details)s  />
""" % locals()
        self._svgwriter.write(svg)

    def _get_gc_props_svg(self, gc):
        color='stroke: %s; ' % rgb2hex(gc.get_rgb())
        linewidth = 'stroke-width: %f; ' % gc.get_linewidth()
        join = 'stroke-linejoin: %s; ' % gc.get_joinstyle()
        cap = 'stroke-linecap: %s; ' % gc.get_capstyle()
        alpha = 'opacity: %f; '% gc.get_alpha()
        offset, seq = gc.get_dashes()
        if seq is not None:
            dvals = ' '.join(['%f'%val for val in seq])
            dashes = 'stroke-dasharray: %s; stroke-dashoffset: %f; ' % (dvals, offset)
        else:
            dashes = ''
        return '%(color)s %(linewidth)s %(join)s %(cap)s %(dashes)s %(alpha)s'%locals()


    def _get_gc_clip_svg(self, gc):
        cliprect = gc.get_clip_rectangle()
        if cliprect is not None:
            key = hash(cliprect)  # See if we've already seen this clip rectangle
            cr = _clipd.get(key)

            if cr is None:        # If not, store a new clipPath
                _clipd[key] = cliprect
                x, y, w, h = cliprect

                y = self.height-(y+h)
                box = """
<defs>
    <clipPath id="%(key)s">
    <rect x="%(x)f" y="%(y)f" width="%(w)f" height="%(h)f"
    style="stroke: gray; fill: none;"/>
    </clipPath>
</defs>

""" % locals()

                return box, key
            else: return '',key   # If we're using a previously defined clipPath, reference its id
        return '',None

    def new_gc(self):
        """
        Return an instance of a GraphicsContextTemplate
        """
        return GraphicsContextSVG()

class GraphicsContextSVG(GraphicsContextBase):

    def set_linestyle(self, style):
        GraphicsContextBase.set_linestyle(self, style)
        offset, dashes = self._dashd[style]
        self.set_dashes(offset, dashes)

    def get_capstyle(self):
        'one of butt/round/square/none'
        d = {'projecting' : 'square',
             'butt' : 'butt',             
             'round' : 'round',
             }
        return d[self._capstyle.lower()]
        
    
class FigureCanvasSVG(FigureCanvasBase):

    def draw(self):
        pass

    def print_figure(self, filename, dpi=80,
                     facecolor='w', edgecolor='w',
                     orientation='portrait'):
        # save figure settings
        origDPI       = self.figure.dpi.get()
        origfacecolor = self.figure.get_facecolor()
        origedgecolor = self.figure.get_edgecolor()

        self.figure.dpi.set(72)
        self.figure.set_facecolor(facecolor)
        self.figure.set_edgecolor(edgecolor)
        width, height = self.figure.get_size_inches()

        basename, ext = os.path.splitext(filename)
        if not len(ext): filename += '.svg'

        self._svgwriter = StringIO()
        w = width*72
        h = height*72
        renderer = RendererSVG(w, h, self._svgwriter, basename)

        self._svgwriter.write(_svgProlog%(w,h) )

        self.figure.draw(renderer)
        renderer.finish()

        # restore figure settings
        self.figure.dpi.set(origDPI)
        self.figure.set_facecolor(origfacecolor)
        self.figure.set_edgecolor(origedgecolor)
        
        try:
            fh = file(filename, 'w')
        except IOError:
            verbose.report_error('Backend SVG failed to save %s' % filename)
            raise

        print >>fh, renderer.get_svg()

class FigureManagerSVG(FigureManagerBase):
    pass

FigureManager = FigureManagerSVG

_svgProlog = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
"http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<!-- Created with matplotlib (http://matplotlib.sourceforge.net/) -->
<svg
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   version="1.0"
   x="0.0"
   y="0.0"
   width="%f"
   height="%f"   
   id="svg1">
"""
