import netCDF4, calendar, urllib, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from datetime import datetime as dt

class CDIPBouy:
    def __init__(self, station, deploy='rt'):
        if not isinstance(deploy, str):
            deplot = '%02d' % deploy
        prefix = 'realtime/' if deploy == 'rt' else 'archive/' + str(station) + 'p1/'
        self.data_url = (
            'http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/' + prefix + '/' + 
            str(station) + 'p1_' + str(deploy) + '.nc'
        )
        self.station, self.deploy = station, deploy
        self.nc = netCDF4.Dataset(self.data_url)

    def name(self):
        return ''.join(self.nc.variables['metaStationName'][:])

    def displacement(self):
        disp = {'x':np.array(self.nc.variables['xyzXDisplacement']),
                'y':np.array(self.nc.variables['xyzYDisplacement']),
                'z':np.array(self.nc.variables['xyzZDisplacement'])}
        disp['t'] = (1000*self.nc.variables['xyzStartTime'][0] + 
                     1000*np.arange(disp['x'].size) / 
                     self.nc.variables['xyzSampleRate']).astype('datetime64[ms]')
        return disp

    def wave_time(self):
        return np.array(self.nc.variables['waveTime'])

    def nearest_time(self, t):
        wt = self.wave_time()
        idx = np.abs(wt - t).argmin()
        return wt[idx]

    def spectrum2D(self, t):
        t = self.nearest_time(t)
        url = (
            'http://cdip.ucsd.edu/data_access/MEM_2dspectra.cdip?sp' +
            str(self.station) + '01' + 
            dt.utcfromtimestamp(int(t)).strftime('%Y%m%d%H%M')
        )
        data = map(float, re.findall('\d\.\d+', urllib.urlopen(url).read()))
        
        energy = np.array(data).reshape(64, 72)
        energy = np.append(energy, energy[:, :1], axis=1)
        freq   = np.array(self.nc.variables['waveFrequency'])
        angle  = np.pi*np.arange(2.5, 367.5, 5)/180
        return energy, freq, angle

class DirectionalSpectrumAnimation:
    def __init__(self, bouy, start_time):
        self.bouy, self.wave_time = bouy, bouy.wave_time()
        self.idx = np.abs(start_time - self.wave_time).argmin()

    def animate(self, i):
        T = int(self.wave_time[self.idx+i])
        energy, freq, angle = self.bouy.spectrum2D(T)
        Emin, Emax = np.amin(energy), np.amax(energy)
        levels = np.arange(Emin + (Emax - Emin)*0.01, Emax, 0.0001)
        
        cntr = self.ax.contourf(angle, freq[:35], energy[:35, :], levels)
        plt.title(self.bouy.name() + " @ " + 
                  dt.utcfromtimestamp(T).strftime("%m/%d/%Y %H:%M"))        
        return self.ax,

    def plot(self, i=0):
        T = int(self.wave_time[self.idx+i])
        energy, freq, angle = self.bouy.spectrum2D(T)
        Emin, Emax = np.amin(energy), np.amax(energy)
        levels = np.arange(Emin + (Emax - Emin)*0.01, Emax, 0.0001)
        
        fig = plt.figure()

        self.ax = plt.subplot(111, polar=True)
        self.ax.set_theta_direction(-1)
        self.ax.set_theta_zero_location("N")
        ylabels = ([20,10,6.7,5,4])
        self.ax.set_yticklabels(ylabels)

        cntr = self.ax.contourf(angle, freq[:35], energy[:35, :], levels)
        plt.thetagrids(np.arange(0, 360, 30), labels=None, frac=1.07)
        plt.title(self.bouy.name() + " @ " + 
                  dt.utcfromtimestamp(T).strftime("%m/%d/%Y %H:%M"))
        
        cbar = fig.colorbar(cntr)
        cbar.set_label('Energy Density (m*m/Hz/deg)', rotation=270)
        
        return fig, self.ax

    def show(self):
        plt.show()        
        
b = CDIPBouy('100')

ds = DirectionalSpectrumAnimation(b, calendar.timegm(dt.utcnow().timetuple()) - 3600*24*7)
fig, ax = ds.plot()

anim = animation.FuncAnimation(fig, ds.animate, frames=10, interval=20, blit=False)

ds.show()


