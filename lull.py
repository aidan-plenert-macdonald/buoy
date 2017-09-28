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
group_freq = (freq**2 - mean**2)/(2*mean)
group_spec = spec*mean/freq

plt.plot(freq, spec, 'r')
plt.plot(group_freq, group_spec, 'b')
plt.legend(['Freq Spec', 'Group Freq Spec'])
plt.show()
exit()

period = 1.0/freq
period_spec = spec*period**2
group_period = 1.0/group_freq
group_period_spec = group_spec*group_period**2

plt.plot(period, period_spec, 'r')
plt.plot(group_period, group_period_spec, 'b')
plt.legend(['Period Spec', 'Group Period Spec'])
plt.show()

