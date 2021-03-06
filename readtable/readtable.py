import logging
import numpy as np
from readtable.readfile import TableFile


class TableData:
    TableTypeDict = {
        2: "Air Calibration",
        7: "Channel Correction",
        8: "Water Scaling",
        -1: "Unkown"
    }

    DMSTypeDict = {
        # channels : (DMS name, channel per module)
        768: ("P07A/B", 32),
        840: ("P07C", 20),
        -1:  ("Unkown", 16)
    }

    def __init__(self, name):
        self.isFileAnalyzeComplete = False
        self.File = TableFile(name)
        if self.File.FP is False:
            logging.error("Read File error!")
            return
        try:
            self.__read_pub_header()
            self.__read_pri_header()
            self.__init_data()
            self.__read_data()
            self.File.close()
        except Exception as e:
            logging.error(str(e))
            logging.error("File not correctly initilized. " +
                          "Make sure upload the corect table file!")
            return
        self.isFileAnalyzeComplete = True
        self.__init_header_dict()

    def __read_pub_header(self):
        self.TableVersion = self.File.readint()
        self.TableContentState = self.File.readint()
        if self.TableContentState in self.TableTypeDict:
            self.TableType = self.TableTypeDict[self.TableContentState]
        else:
            self.TableType = self.TableTypeDict[-1]
        self.TableLenth = self.File.readint()
        self.PrivateHdrOffset = self.File.readint()
        self.DataOffset = self.File.readint()
        self.DataLength = self.File.readint()
        self.LastUpdateTime = self.File.readint()
        # TODO
        # self.PubLastUpdateTimeStr =
        # datestr(datenum(LastUpdateTime/60/60/24)+
        # datenum('01-Jan-1970 8:00:00'));
        self.TableContentVersion = self.File.readint()
        self.DataType = self.File.readint()
        self.DataArrangement = self.File.readint()

    def __read_pri_header(self):
        if self.File.CurrentByteCount != self.PrivateHdrOffset:
            logging.error("Private header start position wrong!")
            return
        self.Channels = self.File.readint()
        if self.Channels in self.DMSTypeDict:
            self.DMSType = self.DMSTypeDict[self.Channels]
        else:
            self.DMSType = self.DMSTypeDict[-1]
        self.Slices = self.File.readint()
        self.PhiFfs = self.File.readint()
        self.ZFfs = self.File.readint()
        self.Integrators = self.File.readint()
        self.Segments = self.File.readint()
        self.SliceWidthDet = self.File.readint()
        self.AirTypes = self.File.readint()
        # TODO
        # Not Right type!!!
        self.ScaledDose = self.File.readfloat()
        logging.warning("Known Bug, the scaled dose is not correct!")

    def __init_data(self):
        offset = self.DataOffset-self.File.CurrentByteCount
        self.UnknownData = []
        for _ in range(0, offset):
            self.UnknownData.append(self.File.readbyte())

        self.Rows = self.Channels
        self.Cols = self.Segments * self.ZFfs * \
            self.ZFfs * self.Integrators * \
            self.Slices
        self.Data = np.zeros([self.Rows, self.Cols])

    def __read_data(self):
        if self.File.CurrentByteCount != self.DataOffset:
            logging.error("Data start position wrong!")
            return
        for i in range(0, self.Cols):
            for j in range(0, self.Rows):
                self.Data[j, i] = self.File.readfloat()

    def __init_header_dict(self):
        if self.isFileAnalyzeComplete is False:
            logging.error("Input file is not initialized!")
            return
        self.HeaderDict = {
            "DMSType": self.DMSType,
            "TableVersion": self.TableVersion,
            "TableContentState": self.TableContentState,
            "TableType": self.TableType,
            "TableLength": self.TableLenth,
            "PrivateHdrOffset": self.PrivateHdrOffset,
            "DataOffset": self.DataOffset,
            "DataLength": self.DataLength,
            "LastUpdateTime": self.LastUpdateTime,
            "TableContentVersion": self.TableContentVersion,
            "DataType": self.DataType,
            "DataArrangement": self.DataArrangement,
            "Channels": self.Channels,
            "Slices": self.Slices,
            "PhiFfs": self.PhiFfs,
            "ZFfs": self.ZFfs,
            "Integrators": self.Integrators,
            "Segments": self.Segments,
            "SliceWidthDet": self.SliceWidthDet,
            "AirTypes": self.AirTypes,
            "ScaledDose": self.ScaledDose
        }

    def getdata(self,
                segment=1, zffs=1,
                phiffs=1, integrator=1):
        if self.isFileAnalyzeComplete is False:
            logging.error("Data not initialized!")
            return False

        if segment > self.Segments or zffs > self.ZFfs or \
           phiffs > self.PhiFfs or integrator > self.Integrators:
            logging.error("Index out of boundary during fetch data")
            return False

        segment -= 1
        zffs -= 1
        phiffs -= 1
        integrator -= 1

        seg_offset = self.ZFfs * self.PhiFfs * self.Integrators * self.Slices
        z_offset = self.PhiFfs * self.Integrators * self.Slices
        phi_offset = self.Integrators * self.Slices
        int_offset = self.Slices
        start_col = (seg_offset * segment +
                     z_offset * zffs +
                     phi_offset * phiffs +
                     int_offset * integrator)
        end_col = start_col + self.Slices
        return self.Data[:, start_col:end_col]

    def fusedata(self):
        if self.isFileAnalyzeComplete is False:
            logging.error("Data not initialized!")
            return False
        # Start calculating
        data = np.zeros([self.Channels, self.Slices])
        logging.info("Raw data initilized, shape is: %s" %
                     (str(data.shape)))
        count = 0
        for seg in range(1, self.Segments+1):
            for zff in range(1, self.ZFfs+1):
                for pff in range(1, self.PhiFfs+1):
                    for inte in range(1, self.Integrators+1):
                        data += self.getdata(segment=seg, zffs=zff,
                                             phiffs=pff, integrator=inte)
                        count += 1
        return data/count

    def simplize_table(self, module_sep=2, slice_sep=2):
        # get fused data
        logging.info("Simplizing Data: module sep: %d; slices fuse: %d" %
                     (module_sep, slice_sep))
        data = self.fusedata()
        # 计算每份通道和层厚里由多少数据整合
        mod = int(self.DMSTypeDict[self.Channels][1]/module_sep)
        sli = int(self.Slices / slice_sep)
        # 计算层厚数据
        fuse_slice = np.zeros([int(self.Channels), slice_sep])
        temp = 0
        for i in range(0, self.Channels):
            fus_count = 0
            for j in range(0, self.Slices):
                if j % sli == (sli - 1) and j != 0:
                    temp += data[i, j]
                    fuse_slice[i, fus_count] = temp / sli
                    fus_count += 1
                    temp = 0
                else:
                    temp += data[i, j]
        logging.info("Simplize slices Done. Shape is: %s" %
                     (str(fuse_slice.shape),))
        # 计算通道数据
        simple = np.zeros([int(self.Channels / mod), slice_sep])
        temp = 0
        for j in range(0, fuse_slice.shape[1]):
            sim_count = 0
            for i in range(0, fuse_slice.shape[0]):
                if i % mod == (mod - 1) and i != 0:
                    temp += fuse_slice[i, j]
                    simple[sim_count, j] = temp / mod
                    sim_count += 1
                    temp = 0
                else:
                    temp += fuse_slice[i, j]
        logging.info("Simplize Channel Done. Shape is: %s" %
                     (str(simple.shape),))
        return simple

    def sort_channel(self, fus_slice=1):
        logging.info("sort channel start!")
        mod_chan = self.DMSTypeDict[self.Channels][1]
        data = self.simplize_table(module_sep=mod_chan, slice_sep=fus_slice)

        result = np.zeros([int(self.Channels/mod_chan) * 2, data.shape[1]])
        for j in range(0, data.shape[1]):
            count = 0
            for i in range(0, data.shape[0]):
                if i % mod_chan == 0 or i % mod_chan == (mod_chan-1):
                    result[count, j] = data[i, j]
                    count += 1

        channel = np.zeros([int(result.shape[0]/2)-1, result.shape[1]])
        for j in range(0, result.shape[1]):
            count = 0
            for i in range(0, result.shape[0]):
                if i % 2 == 0 and i != 0:
                    channel[count, j] = result[i, j] - result[i-1, j]
                    count += 1
        logging.info("sort channel done!")
        return channel

    def sort_nearest_neighbor(self, fus_slice=1):
        logging.info("sort nearest neighbor start!")
        data = self.simplize_table(module_sep=1, slice_sep=fus_slice)
        mod_chan = self.DMSTypeDict[self.Channels][1]
        mod = int(self.Channels/mod_chan)
        result = np.zeros([mod - 1,
                           data.shape[1]])
        for j in range(0, data.shape[1]):
            count = 0
            for i in range(0, data.shape[0]):
                if i != 0:
                    result[count, j] = data[i, j] - data[i - 1, j]
                    count += 1
        logging.info("sort nearest neighbor done!")
        return result

    def sort_center(self, fus_slice=1):
        logging.info("sort center start!")
        mod_chan = self.DMSTypeDict[self.Channels][1]
        mod = int(self.Channels/mod_chan)
        if mod % 2 != 0:
            logging.error("Module Qty is not odd!")
            return False
        data = self.simplize_table(module_sep=1,
                                   slice_sep=fus_slice)
        # P07A/B
        if self.DMSType == self.DMSTypeDict[768]:
            partial_fan = 14 - 1
            middle = (partial_fan, partial_fan)
        # P07C
        elif self.DMSType == self.DMSTypeDict[840]:
            non_partial_fan = 23 - 1
            middle = (non_partial_fan, non_partial_fan + 1)
        # Unkown
        else:
            logging.warning("Unkown DMS type, suppose not partial fan DMS")
            middle = (int(mod/2), int(mod/2+1))

        result = np.zeros([mod, data.shape[1]])
        for j in range(0, data.shape[1]):
            for i in range(0, data.shape[0]):
                # left part
                if i < middle[1]:
                    result[i, j] = data[i, j] - data[middle[0], j]
                # right part
                else:
                    result[i, j] = data[i, j] - data[middle[1], j]
        logging.info("sort center done!")
        return result

    def sort_mirror(self, fus_slice=1):
        logging.info("sort mirror start!")
        mod_chan = self.DMSTypeDict[self.Channels][1]
        mod = int(self.Channels/mod_chan)
        if mod % 2 != 0:
            logging.error("Module Qty is not odd!")
            return False
        data = self.simplize_table(module_sep=1,
                                   slice_sep=fus_slice)
        # P07A/B
        if self.DMSType == self.DMSTypeDict[768]:
            logging.info("Partial Fan!")
            partial_fan = 14 - 1
            middle = (partial_fan, partial_fan)
            result_half_len = min(middle[0], mod-middle[1])
            result = np.zeros([result_half_len * 2 - 1, data.shape[1]])
            is_partial_fan = True
        # P07C
        elif self.DMSType == self.DMSTypeDict[840]:
            logging.info("Non-partial Fan!")
            non_partial_fan = 23 - 1
            middle = (non_partial_fan, non_partial_fan + 1)
            result_half_len = min(middle[0], mod-middle[1])
            result = np.zeros([result_half_len * 2, data.shape[1]])
            is_partial_fan = False
        # Unkown
        else:
            logging.warning("Unkown DMS type, suppose not partial fan DMS")
            middle = (int(mod/2), int(mod/2+1))
            result_half_len = int(mod/2)
            result = np.zeros([result_half_len * 2, data.shape[1]])
            is_partial_fan = False

        # mirror calculating
        if is_partial_fan is True:
            for j in range(0, data.shape[1]):
                for i in range(0, result_half_len):
                    # left part
                    result[result_half_len - i - 1, j] = data[middle[0] - i, j] - data[middle[1] + i, j]
                    # right part
                    if result[result_half_len - i - 1, j] != 0:
                        result[result_half_len + i - 1, j] = result[result_half_len - i - 1, j]

        if is_partial_fan is False:
            for j in range(0, data.shape[1]):
                for i in range(0, result_half_len):
                    # left part
                    result[result_half_len - i - 1, j] = data[middle[0] - i - 1, j] - data[middle[1] + i - 1, j]
                    # right part
                    result[result_half_len + i, j] = result[result_half_len - i - 1, j]

        # TODO
        # the result len is not total module, should add 0 to fill

        logging.info("sort mirror done!")
        return result


if __name__ == '__main__':
    print("Please don't use it individually.")
