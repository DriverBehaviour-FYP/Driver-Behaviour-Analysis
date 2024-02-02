from utils.local.stack_files import stack_files

if __name__ == '__main__':
    filesPath  = "./data/Raw-GPS-data-Kandy-Buses/MAIN/TEMP/TR_FL/"
    savePath = './data/Raw-GPS-data-Kandy-Buses/MAIN/OUTPUTS/'
    fileName = "merged_trips_data.csv"

    print(stack_files(filesPath,savePath,fileName,"bus_trips"))
