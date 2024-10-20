from utils.local.stack_files import stack_files

if __name__ == '__main__':
    filesPath  = "./data/Raw-GPS-data-Kandy-Buses/MAIN/TEMP/AC_SF_CAL/15T/"
    savePath = './data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/'
    fileName = "merged_segments_15T.csv"

    print(stack_files(filesPath,savePath,fileName,"segment"))
