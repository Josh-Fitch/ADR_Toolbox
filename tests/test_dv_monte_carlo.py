""" Test and plot dV Monte Carlo """
import math
import random
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import scienceplots # pylint: disable=unused-import
plt.style.use('science')
plt.rcParams.update({'font.size': 14})

def checkpoint(h, k, x, y, a, b):
    """Check if a point is within ellipse"""
    # checking the equation of
    # ellipse with the given point
    p = ((math.pow((x - h), 2) / math.pow(a, 2)) +
         (math.pow((y - k), 2) / math.pow(b, 2)))
    # P is distance from point to origin relative to ellipse size
    return p

a_0_mean = 800
a_0_std_dev = 8
a_f_mean = 850
a_f_std_dev = 2

inc_0_mean = 65
inc_0_std_dev = 0.25
inc_f_mean = 67
inc_f_std_dev = 0.5

a_mean_list = [a_0_mean, a_f_mean]
a_unc_list = [a_0_std_dev, a_f_std_dev]
inc_mean_list = [inc_0_mean, inc_f_mean]
inc_unc_list = [inc_0_std_dev, inc_f_std_dev]

fig = plt.figure()
ax = plt.axes()
error_ellipse_0 = Ellipse((inc_0_mean, a_0_mean), 2 * inc_0_std_dev, 2 * a_0_std_dev)
error_ellipse_0.set_color("red")
error_ellipse_0.set_alpha(0.2)
error_ellipse_f = Ellipse((inc_f_mean, a_f_mean), 2 * inc_f_std_dev, 2 * a_f_std_dev)
error_ellipse_f.set_color("green")
error_ellipse_f.set_alpha(0.2)
ax.add_patch(error_ellipse_0)
ax.add_patch(error_ellipse_f)
ax.scatter(inc_mean_list, a_mean_list, s=100, c="black", label="Mean Orbital Elements")

for i in range(8):
    a_list = []
    inc_list = []
    while True:
        a_0 = random.uniform(a_0_mean - a_0_std_dev, a_0_mean + a_0_std_dev)
        inc_0 = random.uniform(inc_0_mean - inc_0_std_dev, inc_0_mean + inc_0_std_dev)
        if checkpoint(inc_0_mean, a_0_mean, inc_0, a_0, inc_0_std_dev, a_0_std_dev) <= 1:
            a_list.append(a_0)
            inc_list.append(inc_0)
            break
    while True:
        a_f = random.uniform(a_f_mean - a_f_std_dev, a_f_mean + a_f_std_dev)
        inc_f = random.uniform(inc_f_mean - inc_f_std_dev, inc_f_mean + inc_f_std_dev)
        if checkpoint(inc_f_mean, a_f_mean, inc_f, a_f, inc_f_std_dev, a_f_std_dev) <= 1:
            a_list.append(a_f)
            inc_list.append(inc_f)
            break
    ax.plot(inc_list, a_list, label=f"Run {i}")
#plt.title("Monte Carlo of Altitude-Inclination Transfers under Uncertainty")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.legend()
plt.grid()
plt.show()
