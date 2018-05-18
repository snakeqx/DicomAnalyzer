import math
import logging


class SOMATOM_go:
    def __init__(self, f=535, m=27.8, n=21.3, 
                 centralbeam=435.25, nmax=768, 
                 modchan=32, name="Now"):
        self.CompleteFlag = False
        if nmax == 1:
            logging.error("Divided by zero. Initial quited incompletely")
            return
        try:
            self.Name = name
            self.F = f
            self.M = m
            self.N = n
            self.ChannelPerModule = modchan
            self.CentralBeam = centralbeam
            self.Nmax = nmax
            self.DeltaBeta = (self.M+self.N)/(self.Nmax-1)
            self.CompleteFlag = True
        except Exception as e:
            logging.error(str(e))
            self.CompleteFlag = False

    def calculate_distance(self, chan):
        if self.CompleteFlag is False:
            logging.error("Initial not completed. Process return -1")
            return -1
        result = math.sin(
            (chan-self.CentralBeam)*self.DeltaBeta*math.pi/180
            )*self.F
        return math.floor(abs(result))

    def calculate_channel(self, distance):
        if self.CompleteFlag is False:
            logging.error("Initial not completed. Process return (-1, -1)")
            return -1, -1
        asi1 = math.asin(-1*distance/self.F)
        asi2 = math.asin(distance/self.F)
        channel1 = math.ceil(
            180*asi1/self.DeltaBeta/math.pi+self.CentralBeam
        )
        if channel1 > self.Nmax:
            channel1 = None
        channel2 = math.ceil(
            180*asi2/self.DeltaBeta/math.pi+self.CentralBeam
        )
        if channel2 > self.Nmax:
            channel2 = None
        return channel1, channel2 


if __name__ == "__main__":
    go = SOMATOM_go(nmax=1)
    print(go.CompleteFlag)
    print(go.calculate_channel(250))
    print(go.calculate_distance(34))
