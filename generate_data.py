# Data generator for fox hunting simulation

import csv
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats

class ReceptionReport:
    def __init__(self,time,location,rssi,bearing,tx_identity):
        """A reception report, consisting of time (seconds), location (numpy array), rssi (Watts), and bearing (bearing)"""
        self.time=time
        self.location=np.array(location) # Note: creates a copy!
        self.rssi=rssi
        self.bearing=bearing
        self.tx_identity=tx_identity

    def __repr__(self):
        return "{0},{1},{2},{3},{4}".format(self.time,
                                            ','.join(map(str,self.location)),
                                            self.tx_identity,
                                            self.rssi,
                                            self.bearing)

# Transmitter characteristics
class Transmitter:
    def __init__(self,location,power,identity):
        """A transmitter with a location (given by a 3-slot numpy array) and power level (in Watts)"""
        self.location=location
        self.power=power
        self.identity=identity

    def reception(self,rx_time,rx_location,rx_noise_level=None,rx_antenna_beamwidth=None):
        """Produce a reception report for the transmitter from a rx_location (3-slot numpy array) given rx_noise_level (Watts) and rx_antenna_beamwidth (degrees)"""
        dist=np.linalg.norm(rx_location-self.location)
        
        if rx_noise_level is not None:
            rssi_gen=scipy.stats.rice(np.sqrt(self.power / (2.0*np.pi*rx_noise_level*dist**2)),scale=np.sqrt(rx_noise_level/2.0))
            rssi=rssi_gen.rvs(1)**2.0
            #rssi += np.random.randn(1)*rx_noise_level
        else:
            rssi=self.power/(4*np.pi*dist**2)

        bearing = np.arctan2(self.location[0]-rx_location[0],self.location[1]-rx_location[1])
        if rx_antenna_beamwidth is not None:
            bearing = np.random.vonmises(bearing,
                                         1/(rx_antenna_beamwidth*np.pi/180)**2)[0]
        return ReceptionReport(rx_time,rx_location,float(rssi),bearing*180/np.pi,self.identity)

class Receiver:
    def __init__(self,rx_noise_level=None,rx_antenna_beamwidth=None,name=None):
        self.rx_noise_level=rx_noise_level
        self.rx_antenna_beamwidth=rx_antenna_beamwidth
        self.name=None
        self.reception_reports=[]

    def add_reception(self,time,location,transmitter):
        self.reception_reports.append(transmitter.reception(time,
                                                            location, 
                                                            self.rx_noise_level,
                                                            self.rx_antenna_beamwidth))

    def plot_bearings(self):
        plt.plot([r.bearing for r in self.reception_reports])

    def plot_rssis(self):
        plt.plot([r.rssi for r in self.reception_reports])

    def plot_locations(self):
        plt.plot([r.location[0] for r in self.reception_reports],
                 [r.location[1] for r in self.reception_reports])

    def write_csv(self,filename):
        with open(filename,'wt') as fp:
            for r in self.reception_reports:
                fp.write(repr(r)+'\n')

    def read_csv(self,filename):
        with open(filename,'rt') as fp:
            for row in csv.reader(fp):
                self.reception_reports.append(ReceptionReport(time=float(row[0]),
                                                              location=np.array([float(row[1]),float(row[2])]),
                                                              tx_identity=row[3],
                                                              rssi=float(row[4]),
                                                              bearing=float(row[5])))
        
class TrackingReceiver(Receiver):
    def __init__(self,start_time,start_location,speed_factor,steps,transmitter,rx_noise_level=None,rx_antenna_beamwidth=None):
        Receiver.__init__(self,rx_noise_level,rx_antenna_beamwidth)

        time=start_time
        location=start_location
        
        for i in range(steps):
            self.add_reception(time,location,transmitter)
            location += speed_factor*np.array([np.sin(self.reception_reports[-1].bearing*np.pi/180),
                                               np.cos(self.reception_reports[-1].bearing*np.pi/180)])
            time += 1.0

if __name__ == 'main':
    tx=Transmitter(np.array([0.,0.]),1,'A')
    rx=TrackingReceiver(0.,np.array([1.,0.]),0.005,10,tx,rx_noise_level=0.01,rx_antenna_beamwidth=10)
    rx.name='1'
    #plt.figure()
    #rx.plot_rssis()
    #plt.figure()
    #rx.plot_bearings()
    #plt.figure()
    #rx.plot_locations()
    #plt.show()
    rx.write_csv('test.csv')
    
    rx2=Receiver()
    rx2.read_csv('test.csv')
    rx2.name='2'
    plt.figure()
    rx2.plot_rssis()
    plt.figure()
    rx2.plot_bearings()
    plt.figure()
    rx2.plot_locations()
    plt.show()
