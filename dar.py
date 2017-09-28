import numpy as np
import pandas as pd
import re, requests, datetime, io

class CDIPBuoy:
    def __init__(self, station, minutes=[25, 55]):
        self.station = station
        self.minutes = minutes

    def align_time(self, dt):
        # We need to shift time for some reason and round to  minutes
        if dt.minute >= self.minutes[0] and dt.minute < self.minutes[1]:
            return dt.replace(minute=self.minutes[0])
        elif dt.minute < self.minutes[0]:
            return dt.replace(minute=self.minutes[1]) - datetime.timedelta(hours=1)
        else:
            return dt.replace(minute=self.minutes[1])                                     

    def pm(self, datetime_utc=None):
        if datetime_utc:
            datetime_utc = self.align_time(datetime_utc)
            dt = datetime_utc + datetime.timedelta(hours=1, minutes=30)
        url = (
            "http://cdip.ucsd.edu/data_access/justdar.cdip?100+sp" +
            (("+" + dt.strftime("%Y%m%d%H%M")) if datetime_utc else "")
        )
        txt = re.sub('\<\/?pre\>', '', requests.get(url).text).split('\n')
        meta = {k:v.strip() for k, v in 
                re.findall(r"((?:[A-Z][\w\d\(\)]+[ ]?)+)\: +((?:[\w\d\.\,\/]+[ ]?)+)", 
                           '\n'.join(txt[:7]))}
        sio = io.StringIO()
        sio.write('\n'.join([txt[8]] + txt[10:]))
        sio.seek(0)
        df = pd.read_csv(sio, sep='\s+')
        return df, meta

    def compute_Hs(self, datetime_utc=None):
        """
        Compute Significant Wave Height
        See http://www.ndbc.noaa.gov/wavemeas.pdf
        and "The sampling variability of estimates of spectra of wind-generated gravity waves" by Dolan and Pierson
        """
        df, _ = self.pm(datetime_utc)
        Hs = 4 * np.sum(df['energy']*df['Band'])**0.5
        # I don't know why df['Band'] isn't in the below,
        # but thats what the equ said and I didn't want to read more.
        TDF = 2 * np.sum(df['energy'])**2 / np.sum(df['energy']**2)
        low, high = 10**(-TDF**(-0.5)) * Hs, 10**(TDF**(-0.5)) * Hs
        return Hs, (low, high)
        

if __name__ == '__main__':
    b = CDIPBuoy('100')
    print(b.compute_Hs())
    
    t = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
    for i in range(100):
        df, meta = b.pm(t)
        assert abs(float(meta['Hs(m)']) - b.compute_Hs(t)[0]) < 0.2
        t -= datetime.timedelta(minutes=30)
