import struct
import logging


class TableFile:
    def __init__(self, name):
        self.CurrentByteCount = 0
        self.IntSize = 4
        self.FloatSize = 4
        self.ByteSize = 1
        self.LongFloatSize = 8
        try:
            self.FP = open(name, 'rb')
        except Exception as e:
            logging.error(str(e))
            self.FP = False

    def ReadInt(self):
        if self.FP is not False:
            self.CurrentByteCount += self.IntSize
            return struct.unpack("i", self.FP.read(self.IntSize))[0]
        else:
            logging.error("File is not opened correctly.")

    def ReadFloat(self):
        if self.FP is not False:
            self.CurrentByteCount += self.FloatSize
            return struct.unpack("f", self.FP.read(self.FloatSize))[0]
        else:
            logging.error("File is not opened correctly.")

    def ReadLongFloat(self):
        if self.FP is not False:
            self.CurrentByteCount += self.LongFloatSize
            return struct.unpack("d", self.FP.read(self.LongFloatSize))[0]
        else:
            logging.error("File is not opened correctly.")

    def ReadByte(self):
        if self.FP is not False:
            self.CurrentByteCount += self.ByteSize
            return struct.unpack("B", self.FP.read(self.ByteSize))[0]
        else:
            logging.error("File is not opened correctly.")

    def Close(self):
        self.FP.close()


if __name__ == '__main__':
    print("Please don't use it individually.")
