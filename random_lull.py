from thredds import CDIPBuoy
import numpy as np
from scipy.interpolate import splrep, splev
import matplotlib.pyplot as plt

SPLINE = 1e-4

# Torrey Pines
b = CDIPBuoy('100', 'd09')
freq, spec = b.spectrum(b.wave_time()[-1])
tck = splrep(freq, spec)
freq = np.arange(np.min(freq), np.max(freq), SPLINE)
spec = splev(freq, tck)

prob = spec/np.sum(spec)

f_sample = np.random.choice(freq, size=10000, p=prob)
t_sample = 1.0/f_sample
F_sample = 

figure, axs = plt.subplots(3, 1)
axs = axs.ravel()

axs[0].hist(f_sample, bins=1000)
axs[1].hist(T_sample, bins=1000)


plt.show()



