from thredds import CDIPBuoy
import numpy as np

# Torrey Pines
b = CDIPBuoy('100', 'd09')
freq, spec = b.spectrum(b.wave_time()[-1])

mean = np.average(freq, weights=spec)
var  = np.average((freq - mean)**2, weights=spec)

print "Mean Freq: ", mean, " +- ", var**0.5, " Hz"
print "Mean Period: ", 1.0/mean, " sec"
print "Std Estmated Lull: ", 2*mean/var



