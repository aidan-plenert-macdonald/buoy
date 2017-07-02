import netCDF4, calendar, urllib, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from datetime import datetime as dt
import h5py

class CDIPBuoy:
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

    def nearest_time(self, t, strict_direction=0):
        wt = self.wave_time()
        if strict_direction == 0:
            idx = np.abs(wt - t).argmin()
        else:
            idx = (strict_direction*(wt - t) + np.inf*(strict_direction*(wt - t) < 0)).argmin()
        return wt[idx], idx

    def spectrum2D(self, t, strict_direction=0):
        t, _ = self.nearest_time(t, strict_direction)
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

    def spectrum(self, t, strict_direction=0):
        t, idx = self.nearest_time(t, strict_direction)
        return (np.array(self.nc.variables['waveFrequency']),
                np.array(self.nc.variables['waveEnergyDensity'][idx]))
    
    def to_hdf5_buoy(self, f, grp_name):
        f.create_group(grp_name)
        wave_time = f.create_dataset('wave_time', data=self.wave_time())
        energy    = f.create_dataset('energy', (wave_time.shape[0], 64, 73), dtype=np.float32)
        freq      = f.create_dataset('freq',   (wave_time.shape[0], 64),     dtype=np.float32)
        
        for i, wt in enumerate(wave_time):
            e, frq, a = self.spectrum2D(wt)
            energy[i], freq[i] = e, frq.flatten()
        return HDF5Buoy(f, grp_name)
        

class HDF5Buoy:
    def __init__(self, f, station):
        self.station = station
        self.energy, self.freq, self.wtime = f[station]['energy'], f[station]['freq'], f[station]['wave_time']

    def wave_time(self):
        return self.wtime

    def spectrum2D(self, t, strict_direction=0):
        _, idx = self.nearest_time(t, strict_direction)
        return self.energy[idx], self.freq[idx], np.pi*np.arange(2.5, 367.5, 5)/180

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

def align_buoys(master, supplemental):
    min_time = max([min(master.wave_time())] + [b.wave_time() for b in supplemental])
    max_time = min([max(master.wave_time()[:-1])] + [b.wave_time() for b in supplemental])
    for i, wt in enumerate(master.wave_time()):
        if wt > min_time and wt < max_time:
            X = np.array([master.spectrum(wt, strict_direction=-1)[0].flatten()] + 
                         [b.spectrum(wt, strict_direction=-1)[0].flatten() for b in supplemental]).flatten()
            y = master.spectrum(master.wave_time()[i+1], strict_direction=-1)
            yield X, y
            

