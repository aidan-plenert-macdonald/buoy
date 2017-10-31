import numpy as np
import pandas as pd
import re, requests, datetime, io

class CDIPBuoy:
    def __init__(self, station):
        self.station = station

    def _get(self, code, start_datetime, end_datetime):
        url = "http://cdip.ucsd.edu/data_access/ndar.cdip?{station}+{code}".format(code=code, station=self.station)
        if start_datetime:
            url += "+" + start_datetime.strftime('%Y%m%d')
            if end_datetime:
                url += "-" + end_datetime.strftime('%Y%m%d')
        return re.sub('\<\/?pre\>', '', requests.get(url).text)

    def st(self, start_datetime=None, end_datetime=None):
        """
        30 min decomp of swell including the below columns for each datetime increment

         freq   Band      energy   Dmean     a1       b1       a2       b2    Check
          Hz    width     m*m/Hz    deg                                       factor
         0.0250  0.0050     0.0003   221   -0.1792  -0.1533  -0.3378   0.3161   2.55
         0.0300  0.0050     0.0006   229   -0.1814  -0.2084   0.0993  -0.1183   2.55

        More info http://cdip.ucsd.edu/?nav=documents&sub=index&xitem=description&xdoc=sp_format
        Just note that for ndar, sp got renamed to st
        """
        txt = self._get('st', start_datetime, end_datetime)
        parts = re.findall('(\d{14})\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s*((?:[\d\-\.]{,10}[\s]+)+)', txt)
        columns = ['frequency', 'bandwidth', 'energy', 'Dmean', 'a1', 'b1', 'a2', 'b2', 'checkfactor']
        df = pd.DataFrame(columns=['datetime'] + columns)
        for dt, data in parts:
            sio = io.StringIO()
            sio.write(data)
            sio.seek(0)
            tmp_df = pd.read_csv(sio, sep='\s+', header=None, names=columns)
            tmp_df['datetime'] = datetime.datetime.strptime(dt, '%Y%m%d%H%M%S')
            df = df.append(tmp_df)
        
        return df

    def sm(self, start_datetime=None, end_datetime=None):
        """
        I believe these are the central moments of the swell energy function

        Returns:
            pd.DataFrame(columns=['datetime', 'm0', 'm1', 'm2',
                                  'm3', 'm4', 'm5'])
        """
        sio = io.StringIO()
        sio.write(self._get('sm', start_datetime, end_datetime))
        sio.seek(0)
        return pd.read_csv(sio, sep='\s+', header=None, parse_dates=[0],
                           names=['datetime', 'm0', 'm1',
                                  'm2', 'm3', 'm4', 'm5'])

    def Hs(self, start_datetime=None, end_datetime=None):
        """
        Compute Significant Wave Height
        See http://www.ndbc.noaa.gov/wavemeas.pdf
        and "The sampling variability of estimates of spectra of wind-generated gravity waves" by Dolan and Pierson
        """
        st = self.st(start_datetime, end_datetime)
        st['dE'] = st['energy']*st['bandwidth']
        st['E^2'] = st['energy']**2
        group_st = st.groupby(['datetime'])
        TDF = 2 * group_st['energy'].sum()**2 / group_st['E^2'].sum()

        df = (4*group_st['dE'].sum()**0.5).to_frame(name='Hs')
        df['Hs_low']  = 10**(-TDF**(-0.5)) * df['Hs']
        df['Hs_high'] = 10**(TDF**(-0.5))  * df['Hs']
        return df

if __name__ == '__main__':
    b = CDIPBuoy('100')
    height = b.Hs(datetime.datetime.now() - datetime.timedelta(days=20),
                  datetime.datetime.now())
    print(height)
