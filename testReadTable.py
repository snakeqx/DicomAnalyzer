import logging
from readtable.readtable import TableData

import numpy as np

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(filename)s[line:%(lineno)d]" +
                           "%(levelname)s %(message)s",
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=r'./log.log',
                    filemode='w')
# define a stream that will show log level > ERROR on screen also
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


if __name__ == '__main__':
    data = TableData(r"./exampleData/CCR_A_130")
    if data.isFileAnalyzeComplete is True:
        print(data.UnknownData)
        print(data.HeaderDict)
        d = data.sort_center()
        np.savetxt("foo.csv", d, delimiter=",")
        e = data.simplize_table(module_sep=1, slice_sep=1)
        np.savetxt("fuse.csv", e, delimiter=",")
    else:
        print("Error!")
