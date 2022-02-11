import pandas as pd


class CostModel:
    def create_route_prof(self, data, full_sked):
        #inputs
        airport_cots = data['airport_cost']
        route_cost = data['route_cost']
        aircraft_fix_cost = data['aircraft_fix_cost']

        route_prof = full_sked.copy()
        route_prof = full_sked[full_sked['al'].isin(data['sked'].al)]
        route_prof = route_prof.merge(airport_cots.add_suffix('_from'), left_on=['actype','from'], right_on=['actype_from','ap_from'], how='left')
        route_prof = route_prof.merge(airport_cots.add_suffix('_to'), left_on=['actype','to'], right_on=['actype_to','ap_to'],how='left')
        route_prof = route_prof.merge(route_cost,how='left')
        route_prof = route_prof.merge(aircraft_fix_cost,how='left')

        route_prof[["route_cost","airp_cost_from","airp_cost_to","airc_fix_cost"]]=route_prof[["route_cost","airp_cost_from","airp_cost_to","airc_fix_cost"]].fillna(0)

        route_prof['CM1'] = route_prof['pror_rev']- route_prof['route_cost']-(route_prof['airp_cost_from']+route_prof['airp_cost_to'])/2
        tot_BH = route_prof['BH'].sum()
        route_prof['CM2'] = route_prof['CM1']-route_prof['airc_fix_cost']*(route_prof['BH']/tot_BH)
        route_prof['netw_CM1']=route_prof['CM1']-route_prof['pror_rev']+route_prof['netw_rev']
        route_prof['netw_CM2']=route_prof['CM2']-route_prof['pror_rev']+route_prof['netw_rev']
        
        return route_prof

def __init__(self):
        print ("in init")
    