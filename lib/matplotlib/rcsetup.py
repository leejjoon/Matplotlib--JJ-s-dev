"""
This file contains the default values and the validation code for the options.

The code for parsing the matplotlibrc file and setting the values of rcParams
uses the values from this file to set default values.

Ultimately, the setup code should also use these values to write a default
matplotlibrc file that actually reflects the values given here.
"""

import os

class ValidateInStrings:
    def __init__(self, key, valid, ignorecase=False):
        'valid is a list of legal strings'
        self.key = key
        self.ignorecase = ignorecase
        def func(s):
            if ignorecase: return s.lower()
            else: return s
        self.valid = dict([(func(k),k) for k in valid])

    def __call__(self, s):
        if self.ignorecase: s = s.lower()
        if s in self.valid: return self.valid[s]
        raise ValueError('Unrecognized %s string "%s": valid strings are %s'
                         % (self.key, s, self.valid.values()))

def validate_path_exists(s):
    'If s is a path, return s, else False'
    if os.path.exists(s): return s
    else:
        raise RuntimeError('"%s" should be a path but it does not exist'%s)

def validate_bool(b):
    'Convert b to a boolean or raise'
    if type(b) is str:
        b = b.lower()
    if b in ('t', 'y', 'yes', 'true', '1', 1, True): return True
    elif b in ('f', 'n', 'no', 'false', '0', 0, False): return False
    else:
        raise ValueError('Could not convert "%s" to boolean' % b)

def validate_float(s):
    'convert s to float or raise'
    try: return float(s)
    except ValueError:
        raise ValueError('Could not convert "%s" to float' % s)

def validate_int(s):
    'convert s to int or raise'
    try: return int(s)
    except ValueError:
        raise ValueError('Could not convert "%s" to int' % s)

def validate_psfonttype(s):
    'confirm that this is a Postscript font type that we know how to convert to'
    fonttype = validate_int(s)
    if fonttype not in (3, 42):
        raise ValueError('Supported Postscript font types are 3 and 42')
    return fonttype

validate_backend = ValidateInStrings('backend',[
    'Agg2', 'Agg', 'Aqt', 'Cairo', 'CocoaAgg', 'EMF', 'GD', 'GDK',
    'GTK', 'GTKAgg', 'GTKCairo', 'FltkAgg', 'Paint', 'Pdf', 'PS',
    'QtAgg', 'Qt4Agg', 'SVG', 'Template', 'TkAgg', 'WX', 'WXAgg',
    ], ignorecase=True)

validate_numerix = ValidateInStrings('numerix',[
    'Numeric','numarray','numpy',
    ], ignorecase=True)

validate_toolbar = ValidateInStrings('toolbar',[
    'None','classic','toolbar2',
    ], ignorecase=True)

class validate_nseq_float:
    def __init__(self, n):
        self.n = n
    def __call__(self, s):
        'return a seq of n floats or raise'
        if type(s) is str:
            ss = s.split(',')
            if len(ss) != self.n:
                raise ValueError('You must supply exactly %d comma separated values'%self.n)
            try:
                return [float(val) for val in ss]
            except ValueError:
                raise ValueError('Could not convert all entries to floats')
        else:
            assert type(s) in (list,tuple)
            if len(s) != self.n:
                raise ValueError('You must supply exactly %d values'%self.n)
            return [float(val) for val in s]

class validate_nseq_int:
    def __init__(self, n):
        self.n = n
    def __call__(self, s):
        'return a seq of n ints or raise'
        if type(s) is str:
            ss = s.split(',')
            if len(ss) != self.n:
                raise ValueError('You must supply exactly %d comma separated values'%self.n)
            try:
                return [int(val) for val in ss]
            except ValueError:
                raise ValueError('Could not convert all entries to ints')
        else:
            assert type(s) in (list,tuple)
            if len(s) != self.n:
                raise ValueError('You must supply exactly %d values'%self.n)
            return [int(val) for val in s]



def validate_color(s):
    'return a valid color arg'
    if s.lower() == 'none': return 'None'
    if len(s)==1 and s.isalpha(): return s
    if s.find(',')>=0: # looks like an rgb
        # get rid of grouping symbols
        s = ''.join([ c for c in s if c.isdigit() or c=='.' or c==','])
        vals = s.split(',')
        if len(vals)!=3:
            raise ValueError('Color tuples must be length 3')

        try: return [float(val) for val in vals]
        except ValueError:
            raise ValueError('Could not convert all entries "%s" to floats'%s)

    if s.replace('.', '').isdigit(): # looks like scalar (grayscale)
        return s

    if len(s)==6 and s.isalnum(): # looks like hex
        return '#' + s

    if s.isalpha():
        #assuming a color name, hold on
        return s

    raise ValueError('"s" does not look like color arg')

def validate_stringlist(s):
    'return a list'
    if type(s) is str:
        return [ v.strip() for v in s.split(',') ]
    else:
        assert type(s) in [list,tuple]
        return [ str(v) for v in s ]

validate_orientation = ValidateInStrings('orientation',[
    'landscape', 'portrait',
    ])

def validate_latex_preamble(s):
    'return a list'
    preamble_list = validate_stringlist(s)
    if not preamble_list == ['']:
        verbose.report("""
*****************************************************************
You have the following UNSUPPORTED LaTeX preamble customizations:
%s
Please do not ask for support with these customizations active.
*****************************************************************
"""% '\n'.join(preamble_list), 'helpful')
    return preamble_list



def validate_aspect(s):
    if s in ('auto', 'equal'):
        return s
    try:
        return float(s)
    except ValueError:
        raise ValueError('not a valid aspect specification')

def validate_fontsize(s):
    if type(s) is str:
        s = s.lower()
    if s in ['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large',
             'xx-large', 'smaller', 'larger']:
        return s
    try:
        return float(s)
    except ValueError:
        raise ValueError('not a valid font size')

validate_verbose = ValidateInStrings('verbose',[
    'silent', 'helpful', 'debug', 'debug-annoying',
    ])

validate_cairo_format = ValidateInStrings('cairo_format',
                            ['png', 'ps', 'pdf', 'svg'],
                            ignorecase=True)

validate_ps_papersize = ValidateInStrings('ps_papersize',[
    'auto', 'letter', 'legal', 'ledger',
    'a0', 'a1', 'a2','a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'a10',
    'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'b10',
    ], ignorecase=True)

def validate_ps_distiller(s):
    if type(s) is str:
        s = s.lower()

    if s in ('none',None):
        return None
    elif s in ('false', False):
        return False
    elif s in ('ghostscript', 'xpdf'):
        return s
    else:
        raise ValueError('matplotlibrc ps.usedistiller must either be none, ghostscript or xpdf')

validate_joinstyle = ValidateInStrings('joinstyle',['miter', 'round', 'bevel'], ignorecase=True)

validate_capstyle = ValidateInStrings('capstyle',['butt', 'round', 'projecting'], ignorecase=True)

validate_negative_linestyle = ValidateInStrings('negative_linestyle',['solid', 'dashed'], ignorecase=True)

def validate_negative_linestyle_legacy(s):
    try:
        res = validate_negative_linestyle(s)
        return res
    except ValueError:
        dashes = validate_nseq_float(2)(s)
        warnings.warn("Deprecated negative_linestyle specification; use 'solid' or 'dashed'")
        return (0, dashes)  # (offset, (solid, blank))

class ValidateInterval:
    """
    Value must be in interval
    """
    def __init__(self, vmin, vmax, closedmin=True, closedmax=True):
        self.vmin = vmin
        self.vmax = vmax
        self.cmin = closedmin
        self.cmax = closedmax

    def __call__(self, s):
        try: s = float(s)
        except: raise RuntimeError('Value must be a float; found "%s"'%s)

        if self.cmin and s<self.vmin:
            raise RuntimeError('Value must be >= %f; found "%f"'%(self.vmin, s))
        elif not self.cmin and s<=self.vmin:
            raise RuntimeError('Value must be > %f; found "%f"'%(self.vmin, s))

        if self.cmax and s>self.vmax:
            raise RuntimeError('Value must be <= %f; found "%f"'%(self.vmax, s))
        elif not self.cmax and s>=self.vmax:
            raise RuntimeError('Value must be < %f; found "%f"'%(self.vmax, s))
        return s



# a map from key -> value, converter
defaultParams = {
    'backend'           : ['WXAgg', validate_backend],
    'numerix'           : ['numpy', validate_numerix],
    'maskedarray'       : [False, validate_bool],
    'toolbar'           : ['toolbar2', validate_toolbar],
    'datapath'          : [None, validate_path_exists],   # handled by _get_data_path_cached
    'units'             : [False, validate_bool],
    'interactive'       : [False, validate_bool],
    'timezone'          : ['UTC', str],

    # the verbosity setting
    'verbose.level'     : ['silent', validate_verbose],
    'verbose.fileo'     : ['sys.stdout', str],

    # line props
    'lines.linewidth'       : [1.0, validate_float],     # line width in points
    'lines.linestyle'       : ['-', str],                # solid line
    'lines.color'           : ['b', validate_color],     # blue
    'lines.marker'          : ['None', str],     # black
    'lines.markeredgewidth' : [0.5, validate_float],
    'lines.markersize'      : [6, validate_float],       # markersize, in points
    'lines.antialiased'     : [True, validate_bool],     # antialised (no jaggies)
    'lines.dash_joinstyle'  : ['miter', validate_joinstyle],
    'lines.solid_joinstyle' : ['miter', validate_joinstyle],
    'lines.dash_capstyle'   : ['butt', validate_capstyle],
    'lines.solid_capstyle'  : ['projecting', validate_capstyle],

    # patch props
    'patch.linewidth'   : [1.0, validate_float], # line width in points
    'patch.edgecolor'   : ['k', validate_color], # black
    'patch.facecolor'   : ['b', validate_color], # blue
    'patch.antialiased' : [True, validate_bool], # antialised (no jaggies)


    # font props
    'font.family'       : ['serif', str],            # used by text object
    'font.style'        : ['normal', str],           #
    'font.variant'      : ['normal', str],           #
    'font.stretch'      : ['normal', str],           #
    'font.weight'       : ['normal', str],           #
    'font.size'         : [12.0, validate_float], #
    'font.serif'        : [['Bitstream Vera Serif','New Century Schoolbook',
                           'Century Schoolbook L','Utopia','ITC Bookman',
                           'Bookman','Nimbus Roman No9 L','Times New Roman',
                           'Times','Palatino','Charter','serif'],
                           validate_stringlist],
    'font.sans-serif'   : [['Bitstream Vera Sans','Lucida Grande','Verdana',
                           'Geneva','Lucid','Arial','Helvetica','Avant Garde',
                           'sans-serif'], validate_stringlist],
    'font.cursive'      : [['Apple Chancery','Textile','Zapf Chancery',
                           'Sand','cursive'], validate_stringlist],
    'font.fantasy'      : [['Comic Sans MS','Chicago','Charcoal','Impact'
                           'Western','fantasy'], validate_stringlist],
    'font.monospace'    : [['Bitstream Vera Sans Mono','Andale Mono'
                           'Nimbus Mono L','Courier New','Courier','Fixed'
                           'Terminal','monospace'], validate_stringlist],

    # text props
    'text.color'          : ['k', validate_color],     # black
    'text.usetex'         : [False, validate_bool],
    'text.latex.unicode'  : [False, validate_bool],
    'text.latex.preamble' : [[''], validate_latex_preamble],
    'text.dvipnghack'     : [False, validate_bool],
    'text.fontstyle'      : ['normal', str],
    'text.fontangle'      : ['normal', str],
    'text.fontvariant'    : ['normal', str],
    'text.fontweight'     : ['normal', str],
    'text.fontsize'       : ['medium', validate_fontsize],


    'image.aspect'        : ['equal', validate_aspect],  # equal, auto, a number
    'image.interpolation' : ['bilinear', str],
    'image.cmap'          : ['jet', str],        # one of gray, jet, etc
    'image.lut'           : [256, validate_int],  # lookup table
    'image.origin'        : ['upper', str],  # lookup table

    'contour.negative_linestyle' : ['dashed', validate_negative_linestyle_legacy],

    # axes props
    'axes.axisbelow'        : [False, validate_bool],
    'axes.hold'             : [True, validate_bool],
    'axes.facecolor'        : ['w', validate_color],    # background color; white
    'axes.edgecolor'        : ['k', validate_color],    # edge color; black
    'axes.linewidth'        : [1.0, validate_float],    # edge linewidth
    'axes.titlesize'        : [14, validate_fontsize], # fontsize of the axes title
    'axes.grid'             : [False, validate_bool],   # display grid or not
    'axes.labelsize'        : [12, validate_fontsize], # fontsize of the x any y labels
    'axes.labelcolor'       : ['k', validate_color],    # color of axis label
    'axes.formatter.limits' : [[-7, 7], validate_nseq_int(2)],
                               # use scientific notation if log10
                               # of the axis range is smaller than the
                               # first or larger than the second

    'polaraxes.grid'        : [True, validate_bool],   # display polar grid or not

    #legend properties
    'legend.isaxes'      : [True,validate_bool],
    'legend.numpoints'   : [2, validate_int],      # the number of points in the legend line
    'legend.fontsize'    : [14, validate_fontsize],
    'legend.pad'         : [0.2, validate_float], # the fractional whitespace inside the legend border
    'legend.markerscale' : [1.0, validate_float], # the relative size of legend markers vs. original

    # the following dimensions are in axes coords
    'legend.labelsep'      : [0.010, validate_float], # the vertical space between the legend entries
    'legend.handlelen'     : [0.05, validate_float], # the length of the legend lines
    'legend.handletextsep' : [0.02, validate_float], # the space between the legend line and legend text
    'legend.axespad'       : [0.02, validate_float], # the border between the axes and legend edge
    'legend.shadow'        : [False, validate_bool],


    # tick properties
    'xtick.major.size' : [4, validate_float],      # major xtick size in points
    'xtick.minor.size' : [2, validate_float],      # minor xtick size in points
    'xtick.major.pad'  : [4, validate_float],      # distance to label in points
    'xtick.minor.pad'  : [4, validate_float],      # distance to label in points
    'xtick.color'      : ['k', validate_color],    # color of the xtick labels
    'xtick.labelsize'  : [12, validate_fontsize], # fontsize of the xtick labels
    'xtick.direction'  : ['in', str],            # direction of xticks

    'ytick.major.size' : [4, validate_float],      # major ytick size in points
    'ytick.minor.size' : [2, validate_float],      # minor ytick size in points
    'ytick.major.pad'  : [4, validate_float],      # distance to label in points
    'ytick.minor.pad'  : [4, validate_float],      # distance to label in points
    'ytick.color'      : ['k', validate_color],    # color of the ytick labels
    'ytick.labelsize'  : [12, validate_fontsize], # fontsize of the ytick labels
    'ytick.direction'  : ['in', str],            # direction of yticks

    'grid.color'       : ['k', validate_color],       # grid color
    'grid.linestyle'   : [':', str],       # dotted
    'grid.linewidth'   : [0.5, validate_float],     # in points


    # figure props
    # figure size in inches: width by height
    'figure.figsize'    : [ [8.0,6.0], validate_nseq_float(2)],
    'figure.dpi'        : [ 80, validate_float],   # DPI
    'figure.facecolor'  : [ '0.75', validate_color], # facecolor; scalar gray
    'figure.edgecolor'  : [ 'w', validate_color],  # edgecolor; white

    'figure.subplot.left'   : [0.125, ValidateInterval(0, 1, closedmin=False, closedmax=False)],
    'figure.subplot.right'  : [0.9, ValidateInterval(0, 1, closedmin=False, closedmax=False)],
    'figure.subplot.bottom' : [0.1, ValidateInterval(0, 1, closedmin=False, closedmax=False)],
    'figure.subplot.top'    : [0.9, ValidateInterval(0, 1, closedmin=False, closedmax=False)],
    'figure.subplot.wspace' : [0.2, ValidateInterval(0, 1, closedmin=False, closedmax=True)],
    'figure.subplot.hspace' : [0.2, ValidateInterval(0, 1, closedmin=False, closedmax=True)],


    'savefig.dpi'         : [100, validate_float],   # DPI
    'savefig.facecolor'   : ['w', validate_color],  # facecolor; white
    'savefig.edgecolor'   : ['w', validate_color],  # edgecolor; white
    'savefig.orientation' : ['portrait', validate_orientation],  # edgecolor; white

    'cairo.format'       : ['png', validate_cairo_format],
    'tk.window_focus'    : [False, validate_bool],  # Maintain shell focus for TkAgg
    'tk.pythoninspect'   : [False, validate_bool],  # Set PYTHONINSPECT
    'ps.papersize'       : ['letter', validate_ps_papersize], # Set the papersize/type
    'ps.useafm'          : [False, validate_bool],  # Set PYTHONINSPECT
    'ps.usedistiller'    : [False, validate_ps_distiller], # use ghostscript or xpdf to distill ps output
    'ps.distiller.res'   : [6000, validate_int],     # dpi
    'ps.fonttype'        : [3, validate_psfonttype], # 3 or 42
    'pdf.compression'    : [6, validate_int],        # compression level from 0 to 9; 0 to disable
    'pdf.inheritcolor'   : [False, validate_bool],   # ignore any color-setting commands from the frontend
    'pdf.use14corefonts' : [False, validate_bool],  # use only the 14 PDF core fonts
                                                    # embedded in every PDF viewing application
    'svg.image_inline'  : [True, validate_bool],    # write raster image data directly into the svg file
    'svg.image_noscale' : [False, validate_bool],  # suppress scaling of raster data embedded in SVG
    'plugins.directory' : ['.matplotlib_plugins', str], # where plugin directory is locate

    # mathtext settings
    'mathtext.mathtext2'  : [False, validate_bool], # Needed to enable Unicode
    # fonts used by mathtext. These ship with matplotlib
    'mathtext.rm'         : ['cmr10.ttf', str],  # Roman (normal)
    'mathtext.it'         : ['cmmi10.ttf', str], # Italic
    'mathtext.tt'         : ['cmtt10.ttf', str], # Typewriter (monospaced)
    'mathtext.mit'        : ['cmmi10.ttf', str], # Math italic
    'mathtext.cal'        : ['cmsy10.ttf', str], # Caligraphic
    'mathtext.nonascii'   : ['cmex10.ttf', str], # All other nonascii fonts

}

if __name__ == '__main__':
    rc = defaultParams
    rc['datapath'][0] = '/'
    for key in rc:
        if not rc[key][1](rc[key][0]) == rc[key][0]:
            print "%s: %s != %s"%(key, rc[key][1](rc[key][0]), rc[key][0])
