import matplotlib.pyplot as plt

import logging
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.ERROR)

from matplotlib.offsetbox import VPacker, TextArea, AnchoredOffsetbox
from matplotlib.font_manager import FontProperties


from matplotlib.patches import Rectangle
import matplotlib.transforms as mtrans


from matplotlib.blocking_input import BlockingInput


class BlockingKeyInput(BlockingInput):
    """
    Class that creates a callable object to retrieve a single mouse or
    keyboard click
    """
    def __init__(self, fig, key_list = ["q"]):
        BlockingInput.__init__(self, fig=fig, eventslist=('button_press_event','key_press_event') )
        self.key_list = key_list

    def on_event(self, event):
        """
        Event handler that will be passed to the current figure to
        retrieve events.
        """
        # Check if we have enough events already
        if event.name == "key_press_event" and event.key in self.key_list:
            self.fig.canvas.stop_event_loop()

    def __call__(self, timeout=0):
        """
        Blocking call to retrieve a single mouse or key click
        Returns True if key click, False if mouse, or None if timeout
        """
        BlockingInput.__call__(self,n=1,timeout=timeout)

        return None


class MessageArea(AnchoredOffsetbox):
    def __init__(self, bbox, loc):
        #self.figure = figure
        self._empty = True
        #self.figure = None
        self._empty_message = self._new_message("")
        self.children = [self._empty_message]
        self.box = VPacker(pad=3, sep=3, children=self.children)
        self.prop=FontProperties(size=8)

        #if bbox is None:
        #    bbox = figure.bbox
        self.bbox = bbox

        AnchoredOffsetbox.__init__(self, loc=loc, child=self.box,
                                   prop=self.prop,
                                   pad=0.,
                                   bbox_to_anchor=self.bbox)

        self.patch.set_fc("y")
        #self._empty_message.set_figure(figure)
        #self.anchored_box.set_figure(figure)
        #figure.artists.append(self.anchored_box)

    def _new_message(self, s, **kwargs):

        if "size" not in kwargs:
            kwargs["size"]=8

        at = TextArea(s,
                      #textprops=dict(size=8),
                      textprops=kwargs
                      )
        return at

    def _check_empty(self):
        if self._empty:
            self.children.remove(self._empty_message)
            self._empty = False

    def add_message(self, s, **kwargs):
        self._check_empty()


        s = self._new_message(s, **kwargs)
        #s.set_figure(self.figure)
        self.children.append(s)

        return s


    def clear_message(self):
        for _ in range(len(self.children)):
            c = self.children.pop()
            #self.figure.artists.remove(c)

        self.children.append(self._empty_message)
        self._empty = True


    #def __del__(self):
    #    self.figure.artists.remove(self.anchored_box)


import matplotlib.widgets as widgets
class WidgetLock(widgets.LockDraw):
    def __call__(self, o):
        logging.debug("wideget_lock locked by (%s)"% o)
        widgets.LockDraw.__call__(self, o)
        if hasattr(self, "cb_lock"):
            self.cb_lock()

    def release(self, o):
        logging.debug("wideget_lock release by (%s)"% o)
        widgets.LockDraw.release(self, o)
        if hasattr(self, "cb_release"):
            self.cb_release()


class BaseInteractor(object):
    """
    """

    def __init__(self, figure, bbox):

        self.figure = figure
        self.canvas = figure.canvas

        self.bbox = bbox

        self._current_object = None

        self._click_callbacks = {}
        #self._animated_list = set()
        self.widget_list = []
        
        self._animation_handler_on = False

        self._animation_on = False


    #def check_animated_artist(self, o):
    #    return False

    def check_animated_artist(self, o):
        return isinstance(o, DraggableWidget)

    def get_widget_list(self):
        return self.widget_list

    def _install_widgets(self):
        pass

    def _uninstall_widgets(self):
        pass


    def install_widgets(self):
        self._install_widgets()

    def uninstall_widgets(self):
        self._uninstall_widgets()

    @staticmethod
    def _check_inside(ob, event):
        if hasattr(ob, "_contains") and callable(ob._contains):
            return ob._contains(event)[0]
        else:
            renderer = ob.figure._cachedRenderer
            x, y = event.x, event.y
            bbox = ob.get_window_extent(renderer)
            return bbox.contains(x, y)

    def get_object_under_point(self, event):

        if self.get_animation_handler_on():
            for l in self.get_widget_list():
                #if self._check_inside(l, event):
                if l.contains(event):
                    return l
#         for l in self._click_callbacks:
#             if hasattr(l, "_contains") and l._contains:
#                 if l._contains(event):
#                     return l
#             else:
#                 if self._check_inside(l, event):
#                     return l

        return None



    def set_animation_handler_on(self, status):
        self._animation_handler_on = status

    def get_animation_handler_on(self):
        return self._animation_handler_on

    def select_object_as_current(self, l):
        logging.debug("selecting current object = (%s)"% l)
        self.deselect_current_object()
        self._current_object = l

    def get_current_object(self):
        return self._current_object

    def deselect_current_object(self):
        if self._current_object:
            logging.debug("object deselected")
            self._current_object = None



    def begin_animation(self):
        if not self.get_animation_handler_on():
            return
        logging.debug("begin animation")
        self._animation_on = True
        self.begin_animated()
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.bbox)
        self.draw_animated()
        self.canvas.blit(self.bbox)


    def end_animation(self):
        self._animation_on = False
        self.end_animated()

    def begin_animated(self):
        pass

    def end_animated(self):
        pass

    def update_animated(self, event):
        pass

    def draw_animated(self):
        pass


    def draw_callback(self, event):
        pass


    def key_press_callback(self, event):
        pass


    def button_press_callback(self, event):
        'whenever a mouse button is pressed'

        if self._current_object:
            if self._current_object in self._click_callbacks:
                cb = self._click_callbacks[self._current_object]
                logging.debug("calling (%s) with event (%s)" % (cb, event))
                cb(event)

            if self.check_animated_artist(self._current_object):
                logging.debug("calling begin_animation")
                self.begin_animation()
            else:
                logging.debug("calling begin_animation")
                self._current_object.button_pressed()
            #if self.check_animated_artist(self._current_object):
            #    logging.debug("calling begin_animation")
            #    self.begin_animation()


    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if self._current_object:
            #if self._current_object in self._animated_list:
            if self.check_animated_artist(self._current_object):
                #self.begin_animation()
                self.end_animation()



    def motion_notify_callback(self, event):
        'on mouse movement'

        if event.button == 1:

            if self._current_object is None:
                return

            if self._animation_on:
                self.update_animated(event)
                self.canvas.restore_region(self.background)
                self.draw_animated()
                self.canvas.blit(self.ax.bbox)

        else:

            _current_object = self.get_object_under_point(event)
            if _current_object is self._current_object:
                return

            if _current_object:
                self.select_object_as_current(_current_object)
            else:
                self.deselect_current_object()

            self.canvas.draw()


    def disconnect(self):
        [self.canvas.mpl_disconnect(c) for c in self._connected_callbacks]




class FigureInteractor(BaseInteractor):
    """
    """

    def __init__(self, fig, axes_interactors=None):

        self.figure = fig
        canvas = self.figure.canvas
        self.canvas = canvas

        BaseInteractor.__init__(self, fig, fig.bbox)

        c1 = canvas.mpl_connect('draw_event', self.draw_callback)
        c2 = canvas.mpl_connect('button_press_event', self.button_press_callback)
        c3 = canvas.mpl_connect('key_press_event', self.key_press_callback)
        c4 = canvas.mpl_connect('button_release_event', self.button_release_callback)
        c5 = canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)

        self._connected_callbacks = [c1, c2, c3, c4, c5]


        if axes_interactors is None:
            axes_interactors = []

        self._axes_interactors = dict([(ai.ax, ai) for ai in axes_interactors])
        self._current_axes = None


    def _release_toolbar_lock(self, event=None):
        tb = self.canvas.toolbar
        if tb._active == "ZOOM":
            tb.zoom()
        elif tb._active == "PAN":
            tb.pan()

        # TODO need to set animation_handler_on
        self.update_widget_lock_status(False)


    def _install_widgets(self):

        #ma = self.message_area = MessageArea(self.figure, loc=4)
        ma = self.message_area = MessageArea(self.figure.bbox, loc=4)
        self.figure.artists.append(ma)
        m1 = ma.add_message("Drag annotes to ajust its position.")
        m1.set_figure(self.figure)
        #btn = ButtonWidget(m1, self._release_toolbar_lock)
        #self.widget_list.append(btn)
        #self._click_callbacks[m1] = self._release_toolbar_lock


        ma = self.message_keys = MessageArea(self.figure.bbox, loc=3)
        self.figure.artists.append(ma)
        m2 = ma.add_message("q: quit")
        m2.set_figure(self.figure)


        wl = self.canvas.widgetlock
        wl.__class__ = WidgetLock
        wl.cb_lock = lambda : self.update_widget_lock_status(True)
        wl.cb_release = lambda : self.update_widget_lock_status(False)

    def install_widgets(self):
        self._install_widgets()

        for ai in self._axes_interactors.values():
            ai.install_widgets()

    def _uninstall_widgets(self):

        self.figure.artists.remove(self.message_keys)
        self.figure.artists.remove(self.message_area)
        #del self.message_area
        #del self.message_keys
        #self.message_area = None
        wl = self.canvas.widgetlock
        del wl.cb_lock
        del wl.cb_release
        wl.__class__ = widgets.LockDraw

    def uninstall_widgets(self):
        self._uninstall_widgets()

        for ai in self._axes_interactors.values():
            ai.uninstall_widgets()


    def check_widget_lock(self):
        if self.canvas.widgetlock.available(self):
            if self.do_event_handling == False:
                self.update_widget_lock_status(False)
            self.do_event_handling = True
            return True
        else:
            if self.do_event_handling == True:
                self.update_widget_lock_status(True)
            self.do_event_handling = False
            return False

    def set_animation_handler_on(self, status):
        for ai in self._axes_interactors.values():
            ai.set_animation_handler_on(status)

        BaseInteractor.set_animation_handler_on(self, status)


    def update_widget_lock_status(self, status):
        m1 = self.message_area.children[0]
        if status:
            m1.set_text("Widet is locked.")
            m1._text.set_backgroundcolor("r")
            self.canvas.draw()
            self.set_animation_handler_on(False)

        else:
            m1.set_text("Drag annotes around to ajust its position")
            m1._text.set_backgroundcolor("none")
            self.canvas.draw()
            self.set_animation_handler_on(True)



    def run(self):
        self.install_widgets()

        _interactive = plt.isinteractive()

        self._release_toolbar_lock()

        if _interactive:
            try:
                w = BlockingKeyInput(self.figure)
                w()
                #aa.disconnect()
            finally:
                #ax.get_figure().canvas.widgetlock.release(aa)
                self.disconnect()

                self.uninstall_widgets()
                plt.interactive(_interactive)
                plt.draw()



    def begin_animated(self):
        pass

    def end_animated(self):
        pass

    def update_animated(self, event):
        pass

    def draw_animated(self):
        pass

    def key_press_callback(self, event):
        if self._current_axes is not None:
            ai = self._axes_interactors[self._current_axes]
            logging.debug("forwarding key_press to (%s)" %(ai))
            ai.key_press_callback(event)
            return

        BaseInteractor.button_press_callback(self, event)


    def button_press_callback(self, event):
        'whenever a mouse button is pressed'

        if self._current_axes is not None:
            ai = self._axes_interactors[self._current_axes]
            logging.debug("forwarding button_press to (%s)" %(ai))
            ai.button_press_callback(event)
            return

        BaseInteractor.button_press_callback(self, event)


    def button_release_callback(self, event):
        'whenever a mouse button is released'

        if self._current_axes is not None:
            ai = self._axes_interactors[self._current_axes]
            logging.debug("forwarding button_release to (%s)" %(ai))
            ai.button_release_callback(event)
            return

        BaseInteractor.button_press_callback(self, event)


    def motion_notify_callback(self, event):
        'on mouse movement'

        if self._current_axes is not None:
            self._axes_interactors[self._current_axes].motion_notify_callback(event)
            # return  immediately if it is dragging.
            if event.button == 1:
                return

        ax = event.inaxes
        if ax is None and self._current_axes is not None:
            logging.debug("deselecting axes (%s)" % (ax,))
            self._current_axes = None
        else:
            if ax is not self._current_axes and ax in self._axes_interactors:
                logging.debug("selecting axes (%s)" % (ax,))
                self._current_axes = event.inaxes
                #self._current_object = None


        BaseInteractor.motion_notify_callback(self, event)


    def disconnect(self):
        [self.canvas.mpl_disconnect(c) for c in self._connected_callbacks]






class AxesInteractor(BaseInteractor):
    """
    """

    def __init__(self, ax):

        self.ax = ax

        BaseInteractor.__init__(self, ax.figure, ax.bbox)

        self.widget_list = []
        self.group_list = []

        self._current_group = None


    def add_group(self, grp):
        """
        tie multiple animation widgets as a group. so that they can
        updated together.
        """

        self.group_list.append(grp)
        self.widget_list.extend(grp.widget_list)



    def _install_widgets(self):
        logging.debug("ttt")
        ma = self.message_area = MessageArea(self.ax.bbox, loc=2)
        self.ax.add_artist(ma)
        m1 = ma.add_message("test")
        self.ax.add_artist(m1)


    def _uninstall_widgets(self):
        for c in self.message_area.children:
            c.remove()
        self.message_area.remove()

        for w in self.widget_list:
            w.remove()

#     def check_animated_artist(self, o):
#         if o in self.widget_list:
#             return True
#         return False

    def get_widget_list(self):
        #return [w._artist for w in self.widget_list]
        return self.widget_list




    def select_group(self, obj):
        for grp in self.group_list:
            if grp.has_widget(obj):
                logging.debug("group selected (%s)"% grp)
                grp.set_current(obj)
                self._current_group = grp
                return grp

    def deselect_group(self):
        if self._current_group:
            logging.debug("group deselected (%s)"% self._current_group)
            self._current_group = None

    def select_object_as_current(self, l):
        BaseInteractor.select_object_as_current(self, l)
        if self._current_object:
            grp = self.select_group(self._current_object)
            if grp:
                grp.set_highlighted(True)
            else:
                self._current_object.set_highlighted(True)

    def deselect_current_object(self):
        if self._current_object:
            self._current_object.set_highlighted(False)
        self.deselect_group()
        BaseInteractor.deselect_current_object(self)


    def begin_animated(self):
        if self._current_group:
            self._current_group.begin_animated()
        else:
            self._current_object.begin_animated()

    def end_animated(self):
        if self._current_group:
            self._current_group.end_animated()
        else:
            self._current_object.end_animated()

    def update_animated(self, event):
        if self._current_group:
            self._current_group.update_animated(event)
        else:
            self._current_object.update_animated(event)

    def draw_animated(self):
        if self._current_group:
            self._current_group.draw_animated()
        else:
            self._current_object.draw_animated()


    def key_press_callback(self, event):
        'whenever a mouse button is pressed'

        if event.key == "a":
            w = VLineWidget(self.ax, event.xdata)
            #l = self.ax.axvline(event.xdata)
            self.widget_list.append(w)
            #self.vlines_list.append(l)
            self.select_object_as_current(w)
            self.canvas.draw()
        elif event.key == "d":
            co =self.get_current_object()
            if co:
                self.widget_list.remove(co)
                del co
                self.deselect_current_object()
                self.canvas.draw()


class AxesWidget(object):
    def __init__(self, ax):
        self.ax = ax
        self.set_highlighted(False)
        super(AxesWidget, self).__init__()
        
    def __del__(self):
        if self._artist is not None:
            self._artist.remove()

    def remove(self):
        pass

    #self._artist.remove()

    def set_highlighted(self, b):
        if b:
            self._artist.set_alpha(1.)
        else:
            self._artist.set_alpha(.5)

    def contains(self, event):
        self._cached_xdata = event.xdata
        self._cached_ydata = event.ydata

        ob = self._artist
        if hasattr(ob, "_contains") and callable(ob._contains):
            return ob._contains(event)[0]
        else:
            renderer = ob.get_figure()._cachedRenderer
            x, y = event.x, event.y
            bbox = ob.get_window_extent(renderer)
            return bbox.contains(x, y)


class DraggableWidget(AxesWidget):
    """
    A single widget
    """
    def __init__(self, ax):
        AxesWidget.__init__(self, ax)
        self._ref_xdata = None

    def begin_animated(self):
        self._artist.set_animated(True)

    def end_animated(self):
        self._artist.set_animated(False)


    def update_animated(self, event):
        pass

    def draw_animated(self):
        self._connected_widgets
        pass




class VLineWidget(DraggableWidget):

    def __init__(self, ax, position):

        self._artist = ax.axvline(position)
        DraggableWidget.__init__(self, ax)


    def update_animated(self, event):
        if event.inaxes is not self.ax: return
        self._artist.set_xdata(event.xdata)

    def draw_animated(self):
        self.ax.draw_artist(self._artist)


    def get_position(self):
        return self._artist.get_xdata()


class ButtonWidget(object):

    def __init__(self, artist, callback):

        self._artist = artist
        self.set_highlighted(False)
        self._callback = callback

    def _contains(self, event):
        r, _ = self._artist.contains(event)
        return r

    def contains(self, event):
        r, _ = self._artist.contains(event)
        return r

    def set_highlighted(self, b):
        if b:
            self._artist.set_alpha(1.)
        else:
            self._artist.set_alpha(.5)

    def button_pressed(self):
        print "clicked"
        self._callback()

    def remove(self):
        pass


from mpl_toolkits.axes_grid.inset_locator import BboxPatch

class HiButtonWidget(ButtonWidget):

    def __init__(self, artist, callback):

        self.bbox_patch = BboxPatch(artist.axes.bbox, fc="none", lw=3)
        self.bbox_patch.set_visible(False)
        ButtonWidget.__init__(self, artist, callback)
        artist.axes.add_artist(self.bbox_patch)


    def _contains(self, event):
        r, _ = self._artist.contains(event)
        return r

    def contains(self, event):
        r, _ = self._artist.contains(event)
        return r

    def set_highlighted(self, b):
        if b:
            self.bbox_patch.bbox = self._artist.get_window_extent()
            self.bbox_patch.set_visible(True)
        else:
            self.bbox_patch.set_visible(False)

    def button_pressed(self):
        self._callback()

    def remove(self):
        self.bbox_patch.remove()


class WidgetGroup(object):
    """ a collection of widget that will be animated together"""
    def __init__(self, widget_list):
        self.widget_list = widget_list
        self._current_widget = None

    def has_widget(self, w):
        return w in self.widget_list

    def set_current(self, w):
        self._current_widget = w

    def set_highlighted(self, b):
        self._current_widget.set_highlighted(b)

    def begin_animated(self):
        for w in self.widget_list:
            w.begin_animated()

    def end_animated(self):
        for w in self.widget_list:
            w.end_animated()


    def update_animated(self, event):
        self._current_widget.update_animated(event)

    def draw_animated(self):
        for w in self.widget_list:
            w.draw_animated()

    def get_current_widget(self):
        return self._current_widget


class VSpanWidgetGroup(WidgetGroup):
    def __init__(self, ax, x0, x1):

        self.l1 = VLineWidget(ax, x0)
        self.l2 = VLineWidget(ax, x1)
        self.patch = VSpanrectWidget(ax, x0, x1)

        WidgetGroup.__init__(self, [self.l1, self.l2, self.patch])

    def update_animated(self, event):
        w = self.get_current_widget()
        if (w is self.l1) or (w is self.l2):
            w.update_animated(event)

            x0 = self.l1._artist.get_xdata()
            x1 = self.l2._artist.get_xdata()

            if x0.shape:
                x0 = x0[0]
            if x1.shape:
                x1 = x1[0]

            if x1 > x1:
                x0, x1 = x1, x0

            a = self.patch._artist
            a.set_x(float(x0))
            a.set_width(float(x1-x0))

        elif w is self.patch:
            w.update_animated(event)

            a = w._artist
            x0 = a.get_x()
            x1 = x0 + a.get_width()

            self.l1._artist.set_xdata(x0)
            self.l2._artist.set_xdata(x1)




class VSpanrectWidget(DraggableWidget):

    def __init__(self, ax, x0, x1):

        self._artist = Rectangle((x0, 0), x1-x0, 1, alpha=0.1, ec="none")
        tr = mtrans.blended_transform_factory(ax.transData,
                                              ax.transAxes)
        self._artist.set_transform(tr)
        ax.add_patch(self._artist)

        DraggableWidget.__init__(self, ax)


    def begin_animated(self):
        self._artist.set_animated(True)
        self._ref_xdata = self._cached_xdata

    def update_animated(self, event):
        xx = event.xdata
        if xx is None:
            return

        if event.inaxes is not self.ax: return

        dx = xx - self._ref_xdata

        x0 = self._artist.get_x()
        self._artist.set_x(x0+dx)

        self._ref_xdata = xx

    def draw_animated(self):
        self.ax.draw_artist(self._artist)











class VLinesInteractor(AxesInteractor):
    """
    """
    def __init__(self, ax, vline_locations = []):

        AxesInteractor.__init__(self, ax)
        for p in vline_locations:
            self.add_vline(p)

#     def __del__(self):
#         for w in self.widget_list:
#             del w

    def add_vline(self, pos):
        w = VLineWidget(self.ax, pos)
        self.widget_list.append(w)
        return w

    def key_press_callback(self, event):
        'whenever a mouse button is pressed'

        if event.key == "a":
            w = self.add_vline(event.xdata)
            #l = self.ax.axvline(event.xdata)
            #self.vlines_list.append(l)
            self.select_object_as_current(w)
            self.canvas.draw()
        elif event.key == "d":
            co =self.get_current_object()
            if co:
                self.widget_list.remove(co)
                del co
                self.deselect_current_object()
                self.canvas.draw()
                print self.ax.lines
                
import numpy as np
from matplotlib.image import BboxImage
from matplotlib.transforms import Bbox, TransformedBbox

class VLinesInteractor3(AxesInteractor):
    """
    """

    def _init_colormaps(self):

        a = np.linspace(0, 1, 256).reshape(1,-1)
        a = np.vstack((a,a))

        maps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        ncol = 2
        nrow = len(maps)//ncol + 1

        xpad_fraction = 0.2
        dx = 1./(ncol + xpad_fraction*(ncol-1))

        ypad_fraction = 0.3
        dy = 1./(nrow + ypad_fraction*(nrow-1))


        for i,m in enumerate(maps):
            ix, iy = divmod(i, nrow)
            bbox0 = Bbox.from_bounds(ix*dx*(1+xpad_fraction),
                                     1.-iy*dy*(1+ypad_fraction)-dy,
                                     dx, dy)
            bbox = TransformedBbox(bbox0, self.ax.transAxes)

            bbox_image = BboxImage(bbox,
                                   cmap = plt.get_cmap(m),
                                   norm = None,
                                   origin=None,
                                   #**kwargs
                                   )

            bbox_image.set_data(a)
            self.ax.add_artist(bbox_image)

            def _f(m=m):
                print m

            btn = HiButtonWidget(bbox_image, _f)


            self.widget_list.append(btn)



    def __init__(self, ax):

        AxesInteractor.__init__(self, ax)

        self._init_colormaps()


        txt = ax.text(0.5, 0.5, "Test", size=30)
        def _f():
            print "123"
        btn = HiButtonWidget(txt, _f)


        self.widget_list.append(btn)
        #self._click_callbacks[btn] = _f


class VSpanInteractor(AxesInteractor):
    """
    """
    def __init__(self, ax, x0, x1):

        AxesInteractor.__init__(self, ax)

        grp = VSpanWidgetGroup(ax, x0, x1)

        self.add_group(grp)




if 0:
    plt.clf()
    fig = plt.gcf()

    ax1 = plt.subplot(121)
    ax1.plot([0, 1])
    ax2 = plt.subplot(122)
    ax2.plot([0, 1])

    ai1 = VLinesInteractor(ax1, [0.3, 0.5])
    #ai1 = VLinesInteractor3(ax1, 0.3, 0.5)
    ai2 = VSpanInteractor(ax2, 0.3, 0.5)

    fi = FigureInteractor(fig, [ai1, ai2])
    fi.run()


if __name__ == "__main__":
    fig = plt.gcf()
    fig.clf()

    ax1 = plt.subplot(111)
    #ax1.plot([0, 1])

    #ai1 = VLinesInteractor3(ax1)
    ai1 = VSpanInteractor(ax1, 0.3, 0.5)
    #ai1 = VLinesInteractor(ax1)

    fi = FigureInteractor(fig, [ai1])
    fi.run()
