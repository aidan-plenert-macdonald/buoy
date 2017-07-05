from thredds import CDIPBuoy
import numpy as np
from scipy.interpolate import splrep, splev
import matplotlib.pyplot as plt

SCALE = 1.0e2
SPLINE = 1e-4

# Torrey Pines
b = CDIPBuoy('100', 'd09')
freq, spec = b.spectrum(b.wave_time()[-1])
tck = splrep(freq, spec)

freq = np.arange(np.min(freq), np.max(freq), SPLINE)
spec = splev(freq, tck)

mean = np.average(freq, weights=spec**SCALE)
var  = np.average((freq - mean)**2, weights=spec**SCALE)*SCALE
swell0 = np.max(spec)*np.exp(-(freq - mean)**2/(2*var))

# Variance in the lull is
#  E[ (w^2 - w0^2)^2 ]/w0^2
# This can be computed using var and mean
lull_mean = np.average(mean/(freq**2 - mean**2), weights=swell0)
lull_var  = np.average((mean/(freq**2 - mean**2) - lull_mean)**2, weights=swell0)


print "Mean Period: ", 1.0/mean, " sec"
print "Group Period: ", lull_mean, " +- ", lull_var**0.5, " sec"

plt.plot(freq, spec)
plt.plot(freq, swell0, 'r')
plt.show()


