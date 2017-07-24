import thredds
from datetime import datetime

timezone = +7
epoch = datetime.utcfromtimestamp(0)

# (datetime, buoy, descrip)
breaks = { 
    'blacks': [
        (datetime(2017, 7, 12, 9+timezone), '100', "5-7ft peeling and clean"),
        (datetime(2017, 7, 20, 8+timezone), '100', "5-7ft peeling and clean. A little fast."),
        ],
    
}

def convert((t, bb, dsp)):
    buoy = thredds.CDIPBuoy(bb)
    anim = thredds.DirectionalSpectrumAnimation(buoy, (t-epoch).total_seconds())
    return (t, buoy, anim, dsp)

for b in breaks:
    breaks[b] = map(convert, breaks[b])

breaks['blacks'][1][2].plot(0)
breaks['blacks'][1][2].show()
