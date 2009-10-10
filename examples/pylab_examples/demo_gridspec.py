import matplotlib.pyplot as plt

def make_ticklabels_invisible(fig):
    for ax in fig.axes:
        for tl in ax.get_xticklabels() + ax.get_yticklabels():
            tl.set_visible(False)

# demo 1 : subplot2grid

plt.figure(1)
ax1 = plt.subplot2grid((3,3), (0,0), colspan=3)
ax2 = plt.subplot2grid((3,3), (1,0), colspan=2)
ax3 = plt.subplot2grid((3,3), (1, 2), rowspan=2)
ax4 = plt.subplot2grid((3,3), (2, 0))
ax5 = plt.subplot2grid((3,3), (2, 1))

plt.suptitle("subplot2grid")
make_ticklabels_invisible(plt.gcf())

# demo 2 : gridspec with python indexing

plt.figure(2)

from matplotlib.axes import GridSpec

gs = GridSpec(3, 3)
ax1 = plt.subplot(gs[0, :])
# identical to ax1 = plt.subplot(gs.new_subplotspec((0,0), colspan=3))
ax2 = plt.subplot(gs[1,:-1])
ax3 = plt.subplot(gs[1:, -1])
ax4 = plt.subplot(gs[-1,0])
ax5 = plt.subplot(gs[-1,-2])

plt.suptitle("GridSpec")
make_ticklabels_invisible(plt.gcf())

# demo 3 : gridspec with subplotpars set.

f = plt.figure(3)

plt.suptitle("GirdSpec w/ different subplotpars")

gs1 = GridSpec(3, 3)
ax1 = f.add_subplot(gs1[:-1, :])
ax2 = f.add_subplot(gs1[-1, :-1])
ax2 = f.add_subplot(gs1[-1, -1])
gs1.update(left=0.05, right=0.48, wspace=0.05)

gs2 = GridSpec(3, 3)
ax1 = f.add_subplot(gs2[:, :-1])
ax2 = f.add_subplot(gs2[:-1, -1])
ax2 = f.add_subplot(gs2[-1, -1])
gs2.update(left=0.55, right=0.98, hspace=0.05)

make_ticklabels_invisible(plt.gcf())

plt.show()
