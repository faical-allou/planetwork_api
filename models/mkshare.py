import pandas as pd
import os, os.path

class mkshareModel:
    def read_files(self):
        data = {}
        directory = './temp'
        for _filename in os.listdir(directory):
            print(_filename)
            df_data = pd.read_csv(directory+'/'+_filename)
            data[_filename] = df_data
            print(data)
        return data

def __init__(self):
        print ("in init")
    