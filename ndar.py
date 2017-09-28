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
        txt = self._get('st', start_datetime, end_datetime)
        parts = re.findall('(\d{14})\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s*((?:[\d\-\.]{,10}[\s]+)+)', txt)
        columns = ['frequency', 'bandwidth', 'Dmean', 'a1', 'b1', 'a2', 'b2', 'checkfactor']
        df = pd.DataFrame(columns=['datetime'] + columns)
        for dt, data in parts:
            sio = io.StringIO()
            sio.write(data)
            sio.seek(0)
            tmp_df = pd.read_csv(sio, sep='\s+', header=None, names=columns)
            tmp_df['datetime'] = datetime.datetime.strptime(dt, '%Y%m%d%H%M%S')
            df = df.append(tmp_df)
        
        return df


if __name__ == '__main__':
    b = CDIPBuoy('100')
    print(b.st(datetime.datetime.now() - datetime.timedelta(days=2),
               datetime.datetime.now()))
