"""
This module supports embedded TeX expressions in matplotlib via dvipng
and dvips for the raster and postscript backends.  The tex and
dvipng/dvips information is cached in ~/.matplotlib/tex.cache for reuse between
sessions

Requirements:

* latex
* \*Agg backends: dvipng
* PS backend: latex w/ psfrag, dvips, and Ghostscript 8.51
  (older versions do not work properly)

Backends:

* \*Agg
* PS
* PDF

For raster output, you can get RGBA numpy arrays from TeX expressions
as follows::

  texmanager = TexManager()
  s = '\\TeX\\ is Number $\\displaystyle\\sum_{n=1}^\\infty\\frac{-e^{i\pi}}{2^n}$!'
  Z = self.texmanager.get_rgba(s, size=12, dpi=80, rgb=(1,0,0))

To enable tex rendering of all text in your matplotlib figure, set
text.usetex in your matplotlibrc file (http://matplotlib.sf.net/matplotlibrc)
or include these two lines in your script::

  from matplotlib import rc
  rc('text', usetex=True)

"""

import copy, glob, os, shutil, sys, warnings
from subprocess import Popen, PIPE, STDOUT

try:
    from hashlib import md5
except ImportError:
    from md5 import md5 #Deprecated in 2.5

import atexit
import tempfile
import StringIO

import distutils.version
import numpy as np
import matplotlib as mpl
from matplotlib import rcParams
from matplotlib._png import read_png_from_buffer, read_png
import matplotlib.dviread as dviread
import re

import weakref

DEBUG = False

if sys.platform.startswith('win'): cmd_split = '&'
else: cmd_split = ';'


def dvipng_hack_alpha():
    p = Popen('dvipng -version', shell=True, stdin=PIPE, stdout=PIPE,
        stderr=STDOUT, close_fds=(sys.platform!='win32'))
    stdin, stdout = p.stdin, p.stdout
    for line in stdout:
        if line.startswith('dvipng '):
            version = line.split()[-1]
            mpl.verbose.report('Found dvipng version %s'% version,
                'helpful')
            version = distutils.version.LooseVersion(version)
            return version < distutils.version.LooseVersion('1.6')
    raise RuntimeError('Could not obtain dvipng version')



def _clear_temp_dir(tmpdirname):
    "clear temporary directory"
    shutil.rmtree(tmpdirname, ignore_errors=True)


class TexDBFile(object):

    class Proxy(object):
        def __init__(self, get_basefile, extname):
            self.get_basefile = get_basefile
            self.extname = extname

        def _get_name(self, tex_fontsize):
            basename = self.get_basefile(*tex_fontsize)
            return basename + "." + self.extname

        def exists(self, tex_fontsize):
            return os.path.exists(self._get_name(tex_fontsize))

        def retrieve(self, tex_fontsize, as_buffer=False):
            return open(self._get_name(tex_fontsize)).read()

        def retrieve_as_buffer(self, tex_fontsize):
            return buffer(open(self._get_name(tex_fontsize)).read())

        def retrieve_as_filelike(self, tex_fontsize):
            return open(self._get_name(tex_fontsize))

        def retrieve_as_file(self, tex_fontsize):
            return self._get_name(tex_fontsize)

        def store(self, tex_fontsize, s):
            open(self._get_name(tex_fontsize), "w").write(s)

        def store_file(self, tex_fontsize, fname):
            new_name = self._get_name(tex_fontsize)
            if new_name != fname:
                os.rename(fname, new_name)
            return new_name


    class ProxyTex(Proxy):
        def __init__(self, get_basefile):
            TexDBFile.Proxy.__init__(self, get_basefile, "tex")

        def store(self, tex_fontsize, s):
            texfile = self._get_name(tex_fontsize)
            fh = file(texfile, 'w')

            if rcParams['text.latex.unicode']:
                fh.write(s.encode('utf8'))
            else:
                try:
                    fh.write(s)
                except UnicodeEncodeError, err:
                    mpl.verbose.report("You are using unicode and latex, but have "
                                       "not enabled the matplotlib 'text.latex.unicode' "
                                       "rcParam.", 'helpful')
                    raise

            fh.close()


    def get_cache_directory(self):
        configdir = mpl.get_configdir()
        texcache = self.texcache

        if self._use_temp:
            if self._temp_root is None:
                texcache = tempfile.mkdtemp("", "", configdir)
            else:
                texcache = tempfile.mkdtemp("", "", self._temp_root)
                
            atexit.register(_clear_temp_dir, texcache)

        elif texcache is None:

            oldpath = mpl.get_home()
            if oldpath is None: oldpath = mpl.get_data_path()
            oldcache = os.path.join(oldpath, '.tex.cache')

            texcache = os.path.join(configdir, 'tex.cache')

            if os.path.exists(oldcache):
                print >> sys.stderr, """\
        WARNING: found a TeX cache dir in the deprecated location "%s".
          Moving it to the new default location "%s"."""%(oldcache, texcache)
                shutil.move(oldcache, texcache)

        if not os.path.exists(texcache):
            os.mkdir(texcache)

        return texcache


    def __init__(self, texmanager, texcache=None,
                 use_temp=False, temp_root=None):

        self.texcache = texcache
        self._use_temp = use_temp
        self._temp_root = temp_root
        self.texcache_dir = None
        self.texmanager = weakref.ref(texmanager)

        self.tex = self.ProxyTex(self.get_basefile)
        self.dvi = self.Proxy(self.get_basefile, "dvi")
        self.dvi_baseline = self.Proxy(self.get_basefile, "baseline")
        self.png = self.Proxy(self.get_basefile, "png")
        self.png_baseline = self.Proxy(self.get_basefile, "png_baseline")


    def get_basefile(self, tex, fontsize, dpi=None):
        """
        returns a filename based on a hash of the string, fontsize, and dpi
        """
        if self.texcache_dir is None:
            self.texcache_dir = self.get_cache_directory()

        s = ''.join([tex, self.texmanager().get_font_config(), '%f'%fontsize,
                     self.texmanager().get_custom_preamble(), str(dpi or '')])
        # make sure hash is consistent for all strings, regardless of encoding:
        bytes = unicode(s).encode('utf-8')
        return os.path.join(self.texcache_dir, md5(bytes).hexdigest())




import sqlite3

class TexDBSqlite(object):

    class Proxy(object):
        def __init__(self, cur, extname, texdb_file=None):
            if texdb_file:
                self.texdb_file = weakref.ref(texdb_file)
            else:
                self.texdb_file = None

            self.cur = cur
            self.extname = extname

            MAKE_TABLE = 'CREATE TABLE IF NOT EXISTS %s (texstring TEXT UNIQUE NOT NULL, data BLOB)' % (extname,)

            cur.execute(MAKE_TABLE)

            cur.commit()


            self.GET_ITEM = 'SELECT data FROM %s WHERE (texstring = ?)' % (extname)
            self.ADD_ITEM = 'REPLACE INTO %s (texstring, data) VALUES (?,?)' % (extname)

        def _get_hash(self, s):
            return unicode(s).encode('utf-8')
            #bytes = unicode(s).encode('utf-8')
            #return md5(bytes).hexdigest()

        def _tex_fontsize(self, tex_fontsize):
            l = len(tex_fontsize)
            if l==2:
                return tex_fontsize[0], tex_fontsize[1], 0.
            elif l==3:
                if tex_fontsize[2] is None:
                    return tex_fontsize[0], tex_fontsize[1], 0.
                else:
                    return tex_fontsize
            else:
                raise Exception("")


        def exists(self, tex_fontsize):
            cur = self.cur

            hh = self._get_hash(tex_fontsize)

            return cur.execute(self.GET_ITEM, (hh,)).fetchone() is not None


        def retrieve(self, tex_fontsize):
            r = self.retrieve_as_buffer(tex_fontsize)
            return str(r)


        def retrieve_as_buffer(self, tex_fontsize):
            cur = self.cur

            hh = self._get_hash(tex_fontsize)
            item = cur.execute(self.GET_ITEM, (hh,)).fetchone()
            return item[0]

        def retrieve_as_filelike(self, tex_fontsize):
            return StringIO.StringIO(self.retrieve(tex_fontsize))


        def retrieve_as_file(self, tex_fontsize):
            if not self.texdb_file().exists(tex_fontsize):
                s = self.retrieve(tex_fontsize)
                self.texdb_file().store(tex_fontsize, s)

            return self.texdb_file().retrieve_as_file(tex_fontsize)


        def store(self, tex_fontsize, s):
            cur = self.cur
            hh = self._get_hash(tex_fontsize)
            data = sqlite3.Binary(s)
            cur.execute(self.ADD_ITEM, (hh, data))
            cur.commit()


        def store_file(self, tex_fontsize, fname):
            data = open(fname).read()
            self.store(tex_fontsize, data)

            return fname



    def __init__(self, texmanager):

        configdir = mpl.get_configdir()
        self.texdb_name = os.path.join(configdir, 'tex.db')
        texdb_cache_dir_root = os.path.join(configdir, 'tex.db.cache')

        if not os.path.exists(texdb_cache_dir_root):
            os.mkdir(texdb_cache_dir_root)

        texdb_file = TexDBFile(texmanager, use_temp=True,
                               temp_root=texdb_cache_dir_root)
        self.texdb_file = texdb_file

        self.cur = sqlite3.connect(self.texdb_name)
        #con.text_factory = str

        self.tex = self.Proxy(self.cur, "tex", texdb_file.tex)
        self.dvi = self.Proxy(self.cur, "dvi", texdb_file.dvi)
        self.dvi_baseline = self.Proxy(self.cur, "dvi_baseline", texdb_file.dvi_baseline)
        self.png = self.Proxy(self.cur, "png", texdb_file.png)
        self.png_baseline = self.Proxy(self.cur, "png_baseline", texdb_file.png_baseline)






class TexManager(object):

    """
    Convert strings to dvi files using TeX, caching the results to a
    working dir
    """


    _dvipng_hack_alpha = dvipng_hack_alpha()

    # mappable cache of
    rgba_arrayd = {}
    grey_arrayd = {}
    postscriptd = {}
    pscnt = 0

    serif = ('cmr', '')
    sans_serif = ('cmss', '')
    monospace = ('cmtt', '')
    cursive = ('pzc', r'\usepackage{chancery}')
    font_family = 'serif'
    font_families = ('serif', 'sans-serif', 'cursive', 'monospace')

    font_info = {'new century schoolbook': ('pnc',
                                            r'\renewcommand{\rmdefault}{pnc}'),
                'bookman': ('pbk', r'\renewcommand{\rmdefault}{pbk}'),
                'times': ('ptm', r'\usepackage{mathptmx}'),
                'palatino': ('ppl', r'\usepackage{mathpazo}'),
                'zapf chancery': ('pzc', r'\usepackage{chancery}'),
                'cursive': ('pzc', r'\usepackage{chancery}'),
                'charter': ('pch', r'\usepackage{charter}'),
                'serif': ('cmr', ''),
                'sans-serif': ('cmss', ''),
                'helvetica': ('phv', r'\usepackage{helvet}'),
                'avant garde': ('pag', r'\usepackage{avant}'),
                'courier': ('pcr', r'\usepackage{courier}'),
                'monospace': ('cmtt', ''),
                'computer modern roman': ('cmr', ''),
                'computer modern sans serif': ('cmss', ''),
                'computer modern typewriter': ('cmtt', '')}

    _rc_cache = None
    _rc_cache_keys = ('text.latex.preamble', )\
                     + tuple(['font.'+n for n in ('family', ) + font_families])

    def __init__(self):
        self._texdb = {}
        self.select_texdb("sqlite")
        #self.select_texdb("file")
        self._init_fontconfig()

    def _init_fontconfig(self):
        ff = rcParams['font.family'].lower()
        if ff in self.font_families:
            self.font_family = ff
        else:
            mpl.verbose.report('The %s font family is not compatible with LaTeX. serif will be used by default.' % ff, 'helpful')
            self.font_family = 'serif'

        fontconfig = [self.font_family]
        for font_family, font_family_attr in \
            [(ff, ff.replace('-', '_')) for ff in self.font_families]:
            for font in rcParams['font.'+font_family]:
                if font.lower() in self.font_info:
                    found_font = self.font_info[font.lower()]
                    setattr(self, font_family_attr,
                            self.font_info[font.lower()])
                    if DEBUG:
                        print 'family: %s, font: %s, info: %s'%(font_family,
                                    font, self.font_info[font.lower()])
                    break
                else:
                    if DEBUG: print '$s font is not compatible with usetex'
            else:
                mpl.verbose.report('No LaTeX-compatible font found for the %s font family in rcParams. Using default.' % ff, 'helpful')
                setattr(self, font_family_attr, self.font_info[font_family])
            fontconfig.append(getattr(self, font_family_attr)[0])
        self._fontconfig = ''.join(fontconfig)

        # The following packages and commands need to be included in the latex
        # file's preamble:
        cmd = [self.serif[1], self.sans_serif[1], self.monospace[1]]
        if self.font_family == 'cursive': cmd.append(self.cursive[1])
        while r'\usepackage{type1cm}' in cmd:
            cmd.remove(r'\usepackage{type1cm}')
        cmd = '\n'.join(cmd)
        self._font_preamble = '\n'.join([r'\usepackage{type1cm}', cmd,
                                         r'\usepackage{textcomp}'])


    def _get_texdb(self):
        return self._texdb_current

    texdb = property(_get_texdb)

    def select_texdb(self, s):
        if s in self._texdb:
            self._texdb_current = self._texdb[s]
            return

        if s == "file":
            texdb = TexDBFile(self)
            self._texdb["file"] = texdb
            self._texdb_current = self._texdb[s]
            return

        if s == "sqlite":
            texdb = TexDBSqlite(self) # , self._texdb["file"]
            self._texdb["sqlite"] = texdb
            self._texdb_current = self._texdb[s]
            return 

        raise RuntimeError("")

    def get_font_config(self):
        """Reinitializes self if relevant rcParams on have changed."""
        if self._rc_cache is None:
            self._rc_cache = dict([(k,None) for k in self._rc_cache_keys])
        changed = [par for par in self._rc_cache_keys if rcParams[par] != \
                   self._rc_cache[par]]
        if changed:
            if DEBUG: print 'DEBUG following keys changed:', changed
            for k in changed:
                if DEBUG:
                    print 'DEBUG %-20s: %-10s -> %-10s' % \
                            (k, self._rc_cache[k], rcParams[k])
                # deepcopy may not be necessary, but feels more future-proof
                self._rc_cache[k] = copy.deepcopy(rcParams[k])
            if DEBUG: print 'DEBUG RE-INIT\nold fontconfig:', self._fontconfig
            self._init_fontconfig()
        if DEBUG: print 'DEBUG fontconfig:', self._fontconfig
        return self._fontconfig

    def get_font_preamble(self):
        """
        returns a string containing font configuration for the tex preamble
        """
        return self._font_preamble

    def get_custom_preamble(self):
        """returns a string containing user additions to the tex preamble"""
        return '\n'.join(rcParams['text.latex.preamble'])

    def _get_shell_cmd(self, *args):
        """
        On windows, changing directories can be complicated by the presence of
        multiple drives. get_shell_cmd deals with this issue.
        """
        if sys.platform == 'win32':
            command = ['%s'% os.path.splitdrive(self.texcache)[0]]
        else:
            command = []
        command.extend(args)
        return ' && '.join(command)


    def _make_tex(self, tex, fontsize):
        """
        Generate a tex file to render the tex string at a specific font size

        returns the file name
        """
        custom_preamble = self.get_custom_preamble()
        fontcmd = {'sans-serif' : r'{\sffamily %s}',
                   'monospace'  : r'{\ttfamily %s}'}.get(self.font_family,
                                                         r'{\rmfamily %s}')
        tex = fontcmd % tex

        if rcParams['text.latex.unicode']:
            unicode_preamble = """\usepackage{ucs}
\usepackage[utf8x]{inputenc}"""
        else:
            unicode_preamble = ''

        s = r"""\documentclass{article}
%s
%s
%s
\usepackage[papersize={72in,72in}, body={70in,70in}, margin={1in,1in}]{geometry}
\pagestyle{empty}
\begin{document}
\fontsize{%f}{%f}%s
\end{document}
""" % (self._font_preamble, unicode_preamble, custom_preamble,
       fontsize, fontsize*1.25, tex)

        return s


    def make_tex(self, tex, fontsize):
        """
        Generate a tex file to render the tex string at a specific font size

        returns the file name
        """

        if DEBUG or not self.texdb.tex.exists((tex, fontsize)):

            s = self._make_tex(tex, fontsize)
            self.texdb.tex.store((tex, fontsize), s)

        texfile = self.texdb.tex.retrieve_as_file((tex, fontsize))

        return texfile


    _re_vbox = re.compile(r"MatplotlibBox:\(([\d.]+)pt\+([\d.]+)pt\)x([\d.]+)pt")
    _re_png_depth = re.compile(r"depth=([\d.]+)")
    _re_png_height = re.compile(r"height=([\d.]+)")

    def _make_tex_preview(self, tex, fontsize):
        """
        Generate a tex file to render the tex string at a specific
        font size.  It uses the preview.sty to determin the dimension
        (width, height, descent) of the output.

        returns the file name
        """
        #basefile = self.get_basefile(tex, fontsize)
        #texfile = '%s.tex'%basefile
        #fh = file(texfile, 'w')
        custom_preamble = self.get_custom_preamble()
        fontcmd = {'sans-serif' : r'{\sffamily %s}',
                   'monospace'  : r'{\ttfamily %s}'}.get(self.font_family,
                                                         r'{\rmfamily %s}')
        tex = fontcmd % tex

        if rcParams['text.latex.unicode']:
            unicode_preamble = """\usepackage{ucs}
\usepackage[utf8x]{inputenc}"""
        else:
            unicode_preamble = ''



        # newbox, setbox, immediate, etc. are used to find the box
        # extent of the rendered text.


        s = r"""\documentclass{article}
%s
%s
%s
\usepackage[active,showbox,tightpage]{preview}
\usepackage[papersize={72in,72in}, body={70in,70in}, margin={1in,1in}]{geometry}

%% we override the default showbox as it is treated as an error and makes
%% the exit status not zero
\def\showbox#1{\immediate\write16{MatplotlibBox:(\the\ht#1+\the\dp#1)x\the\wd#1}}

\begin{document}
\begin{preview}
{\fontsize{%f}{%f}%s}
\end{preview}
\end{document}
""" % (self._font_preamble, unicode_preamble, custom_preamble,
       fontsize, fontsize*1.25, tex)

        return s




    def make_tex_preview(self, tex, fontsize):
        """
        Generate a tex file to render the tex string at a specific
        font size.  It uses the preview.sty to determin the dimension
        (width, height, descent) of the output.

        returns the file name
        """

        if DEBUG or not self.texdb.tex.exists((tex, fontsize)):

            s = self._make_tex_preview(tex, fontsize)
            self.texdb.tex.store((tex, fontsize), s)

        texfile = self.texdb.tex.retrieve_as_file((tex, fontsize))

        return texfile


    def _make_dvi(self, tex, fontsize):
        """
        generates a dvi file containing latex's layout of tex string

        returns the file name
        """


        #basefile = self.get_basefile(tex, fontsize)
        #dvifile = '%s.dvi'% basefile

        #if DEBUG or not os.path.exists(dvifile):
        if DEBUG or not self.texdb.dvi.exists((tex, fontsize)):
            #texfile = self.texdb.retrieve_tex_as_file(tex, fontsize)
            texfile = self.make_tex(tex, fontsize)
            tmpdir = os.path.dirname(texfile)
            texname = os.path.basename(texfile)
            tex_root, tex_ext = os.path.splitext(texname)
            outfile = tex_root + '.output'
            command = self._get_shell_cmd('cd "%s"'% tmpdir,
                            'latex -interaction=nonstopmode %s > "%s"'\
                            %(tex_root, outfile))
            mpl.verbose.report(command, 'debug')
            exit_status = os.system(command)
            try:
                fh = file(os.path.join(tmpdir, outfile))
                report = fh.read()
                fh.close()
            except IOError:
                report = 'No latex error report available.'
            if exit_status:
                raise RuntimeError(('LaTeX was not able to process the following \
string:\n%s\nHere is the full report generated by LaTeX: \n\n'% repr(tex)) + report)
            else: mpl.verbose.report(report, 'debug')
            for fname in glob.glob(os.path.join(tmpdir, tex_root+'*')):
                if fname.endswith('dvi'):
                    self.texdb.dvi.store_file((tex, fontsize), fname)
                elif fname.endswith('tex'): pass
                else:
                    try:
                        os.remove(fname)
                    except OSError: pass


    def make_dvi(self, tex, fontsize):
        """
        generates a dvi file containing latex's layout of tex string

        returns the file name
        """


        if rcParams['text.latex.preview']:
            return self.make_dvi_preview(tex, fontsize)

        self._make_dvi(tex, fontsize)
        dvifile = self.texdb.dvi.retrieve_as_file((tex, fontsize))
        return dvifile


    def get_dvi(self, tex, fontsize):
        """
        generates a dvi file containing latex's layout of tex string

        returns the file name
        """


        if rcParams['text.latex.preview']:
            self._make_dvi_preview(tex, fontsize)
        else:
            self._make_dvi(tex, fontsize)

        dvifile = self.texdb.dvi.retrieve_as_filelike((tex, fontsize))
        return dvifile

    def _make_dvi_preview(self, tex, fontsize):
        """
        generates a dvi file containing latex's layout of tex
        string. It calls make_tex_preview() method and store the size
        information (width, height, descent) in a separte file.

        returns the file name
        """
        #basefile = self.texdv.get_basefile(tex, fontsize)
        #dvifile = '%s.dvi'% basefile
        #baselinefile = '%s.baseline'% basefile

        if DEBUG or not self.texdb.dvi.exists((tex, fontsize)) or \
               not self.texdb.dvi_baseline.exists((tex, fontsize)):
            texfile = self.make_tex_preview(tex, fontsize)
            tmpdir = os.path.dirname(texfile)
            texname = os.path.basename(texfile)
            tex_root, tex_ext = os.path.splitext(texname)
            outfile = tex_root + '.output'
            command = self._get_shell_cmd('cd "%s"'% tmpdir,
                            'latex -interaction=nonstopmode %s > "%s"'\
                            %(tex_root, outfile))
            mpl.verbose.report(command, 'debug')
            exit_status = os.system(command)
            try:
                fh = file(os.path.join(tmpdir,outfile))
                report = fh.read()
                fh.close()

            except IOError:
                print command
                report = 'No latex error report available.'
            if exit_status:
                raise RuntimeError(('LaTeX was not able to process the following \
string:\n%s\nHere is the full report generated by LaTeX: \n\n'% repr(tex)) + report)
            else: mpl.verbose.report(report, 'debug')

            # find the box extent information in the latex output
            # file and store them in ".baseline" file
            mm = TexManager._re_vbox.search(report)
            if mm is None:
                mpl.verbose.report(report, 'Failed to parse output')
                raise Exception("")
            self.texdb.dvi_baseline.store((tex, fontsize),
                                          " ".join(mm.groups()))
            #open(basefile+'.baseline',"w").write(" ".join(m.groups()))

            for fname in glob.glob(os.path.join(tmpdir, tex_root+'*')):
                if fname.endswith('dvi'):
                    self.texdb.dvi.store_file((tex, fontsize), fname)
                elif fname.endswith('tex'): pass
                elif fname.endswith('baseline'): pass
                else:
                    try:
                        #print "removing", fname
                        os.remove(fname)
                    except OSError: pass



    def make_dvi_preview(self, tex, fontsize):
        """
        generates a dvi file containing latex's layout of tex
        string. It calls make_tex_preview() method and store the size
        information (width, height, descent) in a separte file.

        returns the file name
        """

        self._make_dvi_preview(tex, fontsize)
        dvifile = self.texdb.dvi.retrieve_as_file((tex, fontsize))
        return dvifile


    def _make_png(self, tex, fontsize, dpi):
        """
        generates a png file containing latex's rendering of tex string

        returns the filename
        """
        #basefile = self.get_basefile(tex, fontsize, dpi)
        #pngfile = '%s.png'% basefile

        # see get_rgba for a discussion of the background
        #if DEBUG or not os.path.exists(pngfile):
        if DEBUG or not self.texdb.png.exists((tex, fontsize, dpi)):
            dvifile = self.make_dvi(tex, fontsize)
            tmpdir = os.path.dirname(dvifile)
            basefile = os.path.basename(dvifile)
            tex_root, tex_ext = os.path.splitext(basefile)

            pngfile = tex_root+'.png'
            outfile = tex_root+'.output'

            command = self._get_shell_cmd('cd "%s"' % tmpdir,
                        'dvipng -bg Transparent -D %s -T tight -o \
                        "%s" "%s" > "%s"'%(dpi, pngfile,
                        tex_root, outfile))
            mpl.verbose.report(command, 'debug')
            exit_status = os.system(command)
            try:
                fh = file(os.path.join(tmpdir, outfile))
                report = fh.read()
                fh.close()
            except IOError:
                report = 'No dvipng error report available.'
            if exit_status:
                raise RuntimeError('dvipng was not able to \
process the flowing file:\n%s\nHere is the full report generated by dvipng: \
\n\n'% dvifile + report)
            else: mpl.verbose.report(report, 'debug')

            self.texdb.png.store_file((tex, fontsize, dpi),
                                      os.path.join(tmpdir, pngfile))

            ## array
            #buf = self.texdb.png.retrieve((tex, fontsize, dpi),
            #                              as_buffer=True)
            #buf = self.texdb.png.retrieve_as_buffer((tex, fontsize, dpi))
            #arr = read_png_from_buffer(buf)
            #self.texdb.array.store((tex, fontsize, dpi), arr.dumps())
            
            try: os.remove(os.path.join(tmpdir, outfile))
            except OSError: pass


    def _make_png_preview(self, tex, fontsize, dpi):
        """
        generates a png file containing latex's rendering of tex string

        returns the filename
        """
        #basefile = self.get_basefile(tex, fontsize, dpi)
        #pngfile = '%s.png'% basefile

        # see get_rgba for a discussion of the background
        #if DEBUG or not os.path.exists(pngfile):
        if DEBUG or not self.texdb.png.exists((tex, fontsize, dpi)) or \
               not self.texdb.png_baseline.exists((tex, fontsize, dpi)):
            dvifile = self.make_dvi_preview(tex, fontsize)
            tmpdir = os.path.dirname(dvifile)
            basefile = os.path.basename(dvifile)
            tex_root, tex_ext = os.path.splitext(basefile)

            pngfile = tex_root+'.png'
            outfile = tex_root+'.output'

            command = self._get_shell_cmd('cd "%s"' % tmpdir,
                        'dvipng -bg Transparent -D %s -T tight --depth --height -o \
                        "%s" "%s" > "%s"'%(dpi, pngfile,
                        tex_root, outfile))
            mpl.verbose.report(command, 'debug')
            exit_status = os.system(command)
            try:
                fh = file(os.path.join(tmpdir, outfile))
                report = fh.read()
                fh.close()
            except IOError:
                report = 'No dvipng error report available.'
            if exit_status:
                raise RuntimeError('dvipng was not able to \
process the flowing file:\n%s\nHere is the full report generated by dvipng: \
\n\n'% dvifile + report)
            else: mpl.verbose.report(report, 'debug')

            try:
                height = int(self._re_png_height.search(report).groups()[0])
                depth = int(self._re_png_depth.search(report).groups()[0])
            except AttributeError:
                print report
                mpl.verbose.report(report, 'debug')
                raise

            self.texdb.png_baseline.store((tex, fontsize, dpi),
                                          "%d %d" % (height, depth))

            self.texdb.png.store_file((tex, fontsize, dpi),
                                      os.path.join(tmpdir, pngfile))

            try: os.remove(os.path.join(tmpdir, outfile))
            except OSError: pass


    def make_png(self, tex, fontsize, dpi):
        """
        generates a png file containing latex's rendering of tex string

        returns the filename
        """

        if rcParams['text.latex.preview']:
            self._make_png_preview(tex, fontsize, dpi)
            #return self.make_png_preview(tex, fontsize, dpi)
        else:
            self._make_png(tex, fontsize, dpi)
        pngfile = self.texdb.png.retrieve_as_file((tex, fontsize, dpi))
        return pngfile


    def get_png(self, tex, fontsize, dpi):
        """
        generates a png file containing latex's rendering of tex string

        returns the filename
        """

        if rcParams['text.latex.preview']:
            self._make_png_preview(tex, fontsize, dpi)
        else:
            self._make_png(tex, fontsize, dpi)

        buf = self.texdb.png.retrieve_as_buffer((tex, fontsize, dpi))
        return read_png_from_buffer(buf)


    def make_ps(self, tex, fontsize):
        """
        generates a postscript file containing latex's rendering of tex string

        returns the file name
        """
        basefile = self.get_basefile(tex, fontsize)
        psfile = '%s.epsf'% basefile

        if DEBUG or not os.path.exists(psfile):
            dvifile = self.make_dvi(tex, fontsize)
            outfile = basefile+'.output'
            command = self._get_shell_cmd('cd "%s"'% self.texcache,
                        'dvips -q -E -o "%s" "%s" > "%s"'\
                        %(os.path.split(psfile)[-1],
                          os.path.split(dvifile)[-1], outfile))
            mpl.verbose.report(command, 'debug')
            exit_status = os.system(command)
            fh = file(outfile)
            if exit_status:
                raise RuntimeError('dvipng was not able to \
process the flowing file:\n%s\nHere is the full report generated by dvipng: \
\n\n'% dvifile + fh.read())
            else: mpl.verbose.report(fh.read(), 'debug')
            fh.close()
            os.remove(outfile)

        return psfile

    def get_ps_bbox(self, tex, fontsize):
        """
        returns a list containing the postscript bounding box for latex's
        rendering of the tex string
        """
        psfile = self.make_ps(tex, fontsize)
        ps = file(psfile)
        for line in ps:
            if line.startswith('%%BoundingBox:'):
                return [int(val) for val in line.split()[1:]]
        raise RuntimeError('Could not parse %s'%psfile)

    def get_grey(self, tex, fontsize=None, dpi=None):
        """returns the alpha channel"""
        key = tex, self.get_font_config(), fontsize, dpi
        alpha = self.grey_arrayd.get(key)

        if alpha is None:
            #pngfile = self.make_png(tex, fontsize, dpi)
            #png_data = self.get_png(tex, fontsize, dpi)
            #X = read_png(os.path.join(self.texcache, pngfile))
            #X = read_png(pngfile)
            X = self.get_png(tex, fontsize, dpi)

            if rcParams['text.dvipnghack'] is not None:
                hack = rcParams['text.dvipnghack']
            else:
                hack = self._dvipng_hack_alpha

            if hack:
                # hack the alpha channel
                # dvipng assumed a constant background, whereas we want to
                # overlay these rasters with antialiasing over arbitrary
                # backgrounds that may have other figure elements under them.
                # When you set dvipng -bg Transparent, it actually makes the
                # alpha channel 1 and does the background compositing and
                # antialiasing itself and puts the blended data in the rgb
                # channels.  So what we do is extract the alpha information
                # from the red channel, which is a blend of the default dvipng
                # background (white) and foreground (black).  So the amount of
                # red (or green or blue for that matter since white and black
                # blend to a grayscale) is the alpha intensity.  Once we
                # extract the correct alpha information, we assign it to the
                # alpha channel properly and let the users pick their rgb.  In
                # this way, we can overlay tex strings on arbitrary
                # backgrounds with antialiasing
                #
                # red = alpha*red_foreground + (1-alpha)*red_background
                #
                # Since the foreground is black (0) and the background is
                # white (1) this reduces to red = 1-alpha or alpha = 1-red
                #alpha = npy.sqrt(1-X[:,:,0]) # should this be sqrt here?
                alpha = 1-X[:,:,0]
            else:
                alpha = X[:,:,-1]

            self.grey_arrayd[key] = alpha
        return alpha


    def get_rgba(self, tex, fontsize=None, dpi=None, rgb=(0,0,0)):
        """
        Returns latex's rendering of the tex string as an rgba array
        """
        if not fontsize: fontsize = rcParams['font.size']
        if not dpi: dpi = rcParams['savefig.dpi']
        r,g,b = rgb
        key = tex, self.get_font_config(), fontsize, dpi, tuple(rgb)
        Z = self.rgba_arrayd.get(key)

        if Z is None:
            alpha = self.get_grey(tex, fontsize, dpi)

            Z = np.zeros((alpha.shape[0], alpha.shape[1], 4), np.float)

            Z[:,:,0] = r
            Z[:,:,1] = g
            Z[:,:,2] = b
            Z[:,:,3] = alpha
            self.rgba_arrayd[key] = Z

        return Z


    def get_text_width_height_descent(self, tex, fontsize, renderer=None):
        """
        return width, heigth and descent of the text.
        """

        if renderer:
            dpi_fraction = renderer.points_to_pixels(1.)
        else:
            dpi_fraction = 1.

        if rcParams['text.latex.preview']:
            # use preview.sty
            if DEBUG or not self.texdb.dvi_baseline.exists((tex, fontsize)):
                dvifile = self.make_dvi_preview(tex, fontsize)

            #l = open(baselinefile).read().split()
            l = self.texdb.dvi_baseline.retrieve((tex, fontsize)).split()

            height, depth, width = [float(l1)*dpi_fraction for l1 in l]
            return width, height+depth, depth

        else:
            # use dviread. It sometimes returns a wrong descent.
            dvifile = self.make_dvi(tex, fontsize)
            dvi = dviread.Dvi(dvifile, 72*dpi_fraction)
            page = iter(dvi).next()
            dvi.close()
            # A total height (including the descent) needs to be returned.
            return page.width, page.height+page.descent, page.descent


    def get_png_correction_offset(self, tex, fontsize, dpi):
        """
        return width, heigth and descent of the text.
        """

        dpi_fraction = dpi / 72.

        if rcParams['text.latex.preview']:
            if DEBUG or not self.texdb.dvi_baseline.exists((tex, fontsize)):
                dvifile = self.make_dvi_preview(tex, fontsize)

            l = self.texdb.dvi_baseline.retrieve((tex, fontsize)).split()
            height, depth, width = [float(l1)*dpi_fraction for l1 in l]

            png_ = self.texdb.png_baseline.retrieve((tex, fontsize, dpi))
            png_height, png_depth = [float(l1) for l1 in png_.split()]

            return 0, png_depth - depth

        else:
            return 0, 0

if __name__ == "__main__":
    texmanager = TexManager()
    s = '\\TeX\\ is Number $\\displaystyle\\sum_{n=1}^\\infty\\frac{-e^{i\pi}}{2^n}$!'
    def aa():
        Z = texmanager.get_rgba(s, fontsize=12, dpi=80)


    def do_store():
        for i in range(100):
            s = "key%05d" % i
            d = "data%05d" % i
            Z = texmanager.texdb.tex.store((s, 12), d)

    def test():
        import time
        rrr = (rand(10000)*97).astype("i")
        ct = time.time()
        for i in rrr:
            s = "key%05d" % i
            Z = texmanager.texdb.tex.exists((s, 12))
        et = time.time() - ct
        print et

    def ttt():
        texmanager.select_texdb("sqlite")
        do_store()
        test()
        texmanager.select_texdb("file")
        do_store()
        test()
        
