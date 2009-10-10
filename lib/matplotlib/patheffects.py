from matplotlib.backend_bases import RendererBase
import matplotlib.transforms as transforms



class PathEffets(object):
    """
    """

    class _Base(object):
        """
        :class:`BBoxTransmuterBase` and its derivatives are used to make a
        fancy box around a given rectangle. The :meth:`__call__` method
        returns the :class:`~matplotlib.path.Path` of the fancy box. This
        class is not an artist and actual drawing of the fancy box is done
        by the :class:`FancyBboxPatch` class.
        """

        # The derived classes are required to be able to be initialized
        # w/o arguments, i.e., all its argument (except self) must have
        # the default values.

        def __init__(self):
            """
            initializtion.
            """
            super(PathEffets._Base, self).__init__()


        def draw_path(self, renderer, gc, tpath, affine, rgbFace):
            """
            Do not modify the input! Use copy instead.
            """
            renderer.draw_path(gc, tpath, affine, rgbFace)

        def draw_tex(self, renderer, gc, x, y, s, prop, angle, ismath='TeX!'):
            self._draw_text_as_path(renderer, gc, x, y, s, prop, angle, ismath="TeX")

        def draw_text(self, renderer, gc, x, y, s, prop, angle, ismath=False):
            self._draw_text_as_path(renderer, gc, x, y, s, prop, angle, ismath)

        def _draw_text_as_path(self, renderer, gc, x, y, s, prop, angle, ismath):

            path, transform = RendererBase._get_text_path_transform(renderer,
                                                                    x, y, s,
                                                                    prop, angle,
                                                                    ismath)
            color = gc.get_rgb()[:3]

            gc.set_linewidth(0.0)
            self.draw_path(renderer, gc, path, transform, rgbFace=color)


        def __call__(self, gc, path, transform):
            pass
        

    class Normal(_Base):
        pass


#     def draw_path_collection(self, renderer,
#                              gc, master_transform, paths, all_transforms,
#                              offsets, offsetTrans, facecolors, edgecolors,
#                              linewidths, linestyles, antialiaseds, urls):
#         path_ids = []
#         for path, transform in renderer._iter_collection_raw_paths(
#             master_transform, paths, all_transforms):
#             path_ids.append((path, transform))

#         for xo, yo, path_id, gc0, rgbFace in renderer._iter_collection(
#             gc, path_ids, offsets, offsetTrans, facecolors, edgecolors,
#             linewidths, linestyles, antialiaseds, urls):
#             path, transform = path_id
#             transform = transforms.Affine2D(transform.get_matrix()).translate(xo, yo)
#             self.draw_path(renderer, gc0, path, transform, rgbFace)


        

       
    class Stroke(_Base):

        def __init__(self, width, color):
            """
            initializtion.
            """
            super(PathEffets.Stroke, self).__init__()
            self._width = width
            self._color = color

        def draw_path(self, renderer, gc, tpath, affine, rgbFace):
            """
            """
            # Do not modify the input! Use copy instead.

            gc0 = renderer.new_gc()
            gc0.copy_properties(gc)
            gc0.set_linewidth(self._width)
            gc0.set_foreground(self._color)

            renderer.draw_path(gc0, tpath, affine, None)


    class withStroke(Stroke):

        def draw_path(self, renderer, gc, tpath, affine, rgbFace):

            PathEffets.Stroke.draw_path(self, renderer, gc, tpath, affine, rgbFace)
            renderer.draw_path(gc, tpath, affine, rgbFace)



if __name__ == '__main__':
    clf()
    imshow([[1,2],[2,3]])
    #eff = PathEffets.Thicken()
    txt = annotate("test", (1., 1.), (0., 0),
                   arrowprops=dict(arrowstyle="->", connectionstyle="angle3", lw=2),
                   size=12, ha="center")
    txt.set_path_effects([PathEffets.withStroke(width=3, color="w")])
    #txt.arrow_patch.set_path_effects([PathEffets.withStroke(width=3, color="w")])
    txt.arrow_patch.set_path_effects([PathEffets.Stroke(width=5, color="w"),
                                      PathEffets.Normal()])
