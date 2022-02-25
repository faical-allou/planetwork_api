import pandas as pd
import os, os.path
from math import radians, degrees, sin, cos, asin, acos, sqrt
import datetime
import random

class MkshareModel:

    def read_data(self, input_directory, param_directory, analysisName):
        data = {}
        param = {}
        for _filename in os.listdir(input_directory):
            if _filename[0] == '.' or len(_filename.split('-')) != 2:
                continue

            filetype = _filename.split('-')[1]
            if _filename.split('-')[0] == analysisName:
                df_data = pd.read_csv(input_directory+'/'+_filename,  header = None)
                column_dict = { 
                        'sked': ['from', 'to', 'al','fln', 'actype', 'depday','dep','arrday','arr'],
                        'comp': ['from', 'to', 'al', 'fln','actype', 'depday','dep','arrday','arr'],
                        'demand': ['orig', 'dest', 'unit','unit_vol', 'rev'],
                        'demand_curve': ['orig', 'dest', 'ttt_1','ttt_2', 'ttt_3','ttt_4'],          
                        'route_cost': ['from','to', 'actype', 'route_cost'],
                        'airport_cost': ['ap', 'actype', 'airp_cost'],
                        'aircraft_fix_cost': ['actype', 'airc_fix_cost'],
                        'config': ['actype', 'unit_cap', 'vol_cap'],
                        'network' : ['stops_allowed'],
                        'connections': ['hub', 'minct', 'maxct'],
                        'preferences' : ['from', 'to', 'stop_penalty'],
                }
                if filetype in column_dict:
                    df_data.columns = column_dict[filetype]
                    data[filetype] = df_data
                
            for _filename in os.listdir(param_directory):
                if _filename[0] == '.':
                    continue
                filetype = _filename
                df_data = pd.read_csv(param_directory+'/'+_filename,  header = None)
                column_dict = { 
                        'airports': ["country_code","region_name","iata","icao","airport","latitude","longitude"]
                }
                if filetype in column_dict:
                    df_data.columns = column_dict[filetype]
                    param[_filename] = df_data
        return data, param

    def gcd(self, lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        return 6371 * (
            acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2))
        )

    def create_itin(self, data, param, max_stop):
        #inputs
        your_sked = data['sked']
        comp_sked = data['comp']
        data_config = data['config']

        data_connect = data['connections']
        data_pref = data['preferences']
        data_pref['od'] = data_pref["from"]+data_pref["to"]
        param_airport = param['airports']
        param_airport['latitude']= param_airport['latitude'].astype(float)
        param_airport['longitude']= param_airport['longitude'].astype(float)


        your_sked = your_sked.merge(data_config, on='actype')
        comp_sked = comp_sked.merge(data_config, on='actype')


        full_sked = pd.concat([your_sked,comp_sked])
        full_sked["dep"] = pd.to_datetime(full_sked["dep"]) + full_sked["depday"]*datetime.timedelta(days=1)
        full_sked["arr"] = pd.to_datetime(full_sked["arr"]) + full_sked["arrday"]*datetime.timedelta(days=1)
        full_sked["id"] = full_sked['al'] + full_sked['fln'].astype('str')+"/"+full_sked['depday'].astype('str')
        full_sked = full_sked.merge(param_airport[['iata','latitude','longitude']].add_suffix('_from'),left_on=['from'], right_on=['iata_from'] )
        full_sked = full_sked.merge(param_airport[['iata','latitude','longitude']].add_suffix('_to'),left_on=['to'], right_on=['iata_to'])

        full_sked["BH"] = (full_sked["arr"]-full_sked["dep"])

        full_sked["unit_load"] = 0
        full_sked["vol_load"] = 0
        full_sked["netw_rev"] = 0
        full_sked["pror_rev"]=0

        full_sked["dist"] = full_sked.apply(lambda x: self.gcd(x['longitude_from'], x['latitude_from'],x['longitude_to'], x['latitude_to']), axis=1)

        data_connect['minct'] = pd.to_timedelta(data_connect['minct'])
        data_connect['maxct'] = pd.to_timedelta(data_connect['maxct'])

        df_connect = full_sked.add_suffix('_1').reset_index(drop=True)
        df_connect['nbstops'] = 0

        list_itin = {}
        list_itin[0] = df_connect.copy()
        list_itin[0]['unit_demand']= 0
        list_itin[0]['vol_demand']= 0
        list_itin[0]['rev']= 0
        list_itin[0]['tot_dist']=list_itin[0]['dist_1']

        #build itineraries
        for i in range (1,max_stop+1):
            cnx_p = data_connect.copy()
            itins = list_itin[i-1].merge(full_sked.add_suffix('_'+str(i+1)), how= "cross")
            
            
            itins['cnx_time_'+str(i)] = itins['dep_'+str(i+1)] - itins['arr_'+str(i)]
            
            cnx_p.columns = ['to_'+str(i), 'minct_'+str(i), 'maxct_'+str(i)]
            
            #filter connections
            itins.drop(itins[itins['to_'+str(i)] != itins['from_'+str(i+1)]].index, inplace=True)
            itins.drop(itins[itins['from_'+str(i)] == itins['to_'+str(i+1)]].index, inplace=True)
            itins.drop(itins[itins['from_'+str(1)] == itins['to_'+str(i+1)]].index, inplace=True)
            
            itins = itins.merge(cnx_p, on = ['to_'+str(i)])
            
            itins.drop(itins[itins['cnx_time_'+str(i)] < itins['minct_'+str(i)]].index, inplace=True)
            itins.drop(itins[itins['cnx_time_'+str(i)] > itins['maxct_'+str(i)]].index, inplace=True)
            
            
            itins['nbstops'] = i
            itins['tot_dist'] += itins['dist_'+str(i+1)]
            list_itin[i] = itins


        #add attributes
        for i in range(0,max_stop+1):
            list_itin[i]["travel_time"] = list_itin[i]["arr_"+str(i+1)]-list_itin[i]["dep_1"]
            list_itin[i]["od"] = list_itin[i]["from_1"]+list_itin[i]["to_"+str(i+1)]
            list_itin[i]["index"] = list_itin[i].index
            list_itin[i]['itin_id'] = list_itin[i]["nbstops"].astype(str)+"-"+list_itin[i]["index"].astype(str)
            list_itin[i] = list_itin[i].merge(data_pref, on="od")

            #calculate score
            list_itin[i]["score"] = list_itin[i]["travel_time"].dt.seconds+list_itin[i]["nbstops"]*list_itin[i]["stop_penalty"]*3600
        return full_sked, list_itin

    def build_options(self, list_itin, max_stop, data_pref):
        od_itin = {}
        list_itin_summary = pd.DataFrame(columns=["itin_id","index", "od","travel_time", "nbstops","score"])

        for i in range(0,max_stop+1):
            list_itin_summary= pd.concat([list_itin_summary,list_itin[i][["itin_id","index", "od","travel_time", "nbstops","score"]]]) 
        #organize data by OD
        for od in data_pref.od.unique():    
            od_itin[od] = list_itin_summary[list_itin_summary['od']==od].copy()
        return list_itin_summary, od_itin

    def create_demand_set(self, data, time_period):
        #variables
        timep = time_period

        #define user arrivals
        demand_rand = {}
        demand_curve = data['demand_curve']
        demand = data['demand']
        demand['od'] = demand['orig']+demand['dest']
        demand_by_ttt = pd.merge(demand, demand_curve, on=["orig","dest"])

        for i in range(1,1+timep):
            demand_by_ttt['d_ttt_'+str(i)]=(demand_by_ttt['ttt_'+str(i)]*demand_by_ttt['unit']).astype('int')

        #shuffle pax

        for i in range(1,1+timep):
            randm = []
            for indx, row in demand_by_ttt.iterrows():
                for k in range(1,row['d_ttt_'+str(i)]):
                    randm.append(row['orig']+row['dest'])
            random.shuffle(randm)
            demand_rand[i] = randm
        return demand_rand

    def allocate_traffic(self, max_stop, timep, demand, data_pref, full_sked, list_itin, list_itin_summary, od_itin, demand_rand ):
        spill = dict.fromkeys(demand['od'].unique(),0)

        avail_list_itin = {}
        for key in list_itin:   
            avail_list_itin[key] = list_itin[key].copy()

        avail_od_itin = {}
        for key in od_itin:
            avail_od_itin[key] = od_itin[key].copy()

        avail_list_itin_summary = list_itin_summary.copy()

        for _i in range(1, 1+timep):
            list_pax = demand_rand[_i]


            #choose an itin randomly among available ones
            for od_select in list_pax:
                if len(avail_od_itin[od_select])>0 :
                    choice = random.choices(list(avail_od_itin[od_select]["itin_id"]), weights = list(avail_od_itin[od_select]["score"]), k=1)
                    stop_index = choice[0].split('-')
                    choice_stops = int(stop_index[0])
                    choice_index = int(stop_index[1])  
                    itin_selected = avail_list_itin[choice_stops]['index']==choice_index
                    
                    #add pax and revenue to itinerary 
                    itin_selected_orig_list = (list_itin[choice_stops]['index']==choice_index)
                    list_itin[choice_stops].loc[itin_selected_orig_list,'unit_demand'] += 1
                    list_itin[choice_stops].loc[itin_selected_orig_list,'vol_demand'] += demand.loc[demand['od']==od_select,'unit_vol'].values[0]
                    list_itin[choice_stops].loc[itin_selected_orig_list,'rev'] += demand.loc[demand['od']==od_select,'rev'].values[0]
                    
                    
                    #add pax to flights
                    for i in range(0, choice_stops+1):
                        if len(avail_list_itin[choice_stops].loc[itin_selected,'id_'+str(i+1)])== 0:
                            break
                        flights_chosen = avail_list_itin[choice_stops].loc[itin_selected,'id_'+str(i+1)].values[0]
                        full_sked.loc[full_sked['id']==flights_chosen,'unit_load' ] += 1
                        full_sked.loc[full_sked['id']==flights_chosen,'vol_load' ] += demand.loc[demand['od']==od_select,'unit_vol'].values[0]
                        full_sked.loc[full_sked['id']==flights_chosen,'netw_rev' ] += demand.loc[demand['od']==od_select,'rev'].values[0]
                        full_sked.loc[full_sked['id']==flights_chosen,'pror_rev' ] += demand.loc[demand['od']==od_select,'rev'].values[0]*(
                            list_itin[choice_stops].loc[itin_selected_orig_list,'dist_'+str(i+1)].values[0]/list_itin[choice_stops].loc[itin_selected_orig_list,'tot_dist'].values[0]
                        )

                    #remove closed flights
                    for i in range(0, choice_stops+1):
                        if (full_sked.loc[full_sked['id']==flights_chosen,'unit_load'].values[0] == full_sked.loc[full_sked['id']==flights_chosen,'unit_cap'].values[0] or
                            full_sked.loc[full_sked['id']==flights_chosen,'vol_load'].values[0] >= full_sked.loc[full_sked['id']==flights_chosen,'vol_cap'].values[0]  ) :
                            for j in range(0, max_stop+1):
                                for k in range(0,j+1):
                                    avail_list_itin[j].drop(avail_list_itin[j][avail_list_itin[j]['id_'+str(k+1)] == flights_chosen].index, inplace=True)
                            avail_list_itin_summary, avail_od_itin = self.build_options(avail_list_itin, max_stop, data_pref)
                            
                else:
                    #log spill
                    spill[od_select] += 1 
        spill_df = pd.DataFrame.from_dict(spill, orient='index').reset_index()

        return spill_df, full_sked, list_itin, avail_list_itin

def __init__(self):
        print ("in init")
    