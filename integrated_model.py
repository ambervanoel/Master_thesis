'''


'''
from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import operator
import numpy as np
import os
import pandas as pd

from ema_workbench import (ema_logging, RealParameter, TimeSeriesOutcome, Constant,
                           ScalarOutcome, perform_experiments, save_results, IntegerParameter)
from ema_workbench.em_framework.model import Replicator, FileModel
from ema_workbench.connectors import pyNetLogo


def calculate_energy_demand(t, energy_demand_init, energy_demand_growth_f):
    return energy_demand_init + (energy_demand_init * energy_demand_growth_f) * (t)

def calculate_share_green(t, c, a, u, green_share_init):
    return green_share_init + 0.5 * c * (np.tanh(1+a*(t-u)) - np.tanh(1-a*u))

def calculate_share_other_grey_sources(t, other_grey_share_init, other_grey_share_growth_f):
    return other_grey_share_init + (other_grey_share_init * other_grey_share_growth_f) * (t)


def calculate_coal_demand_HLH(t,
                              energy_demand_init, energy_demand_growth_f, 
                              c, a, u, green_share_init,
                              other_grey_share_init, other_grey_share_growth_f):
    energy_demand = calculate_energy_demand(t, energy_demand_init, energy_demand_growth_f)
    share_green = calculate_share_green(t, c, a, u, green_share_init)
    share_other_grey_sources = calculate_share_other_grey_sources(t, other_grey_share_init, other_grey_share_growth_f)    
    
    return (1 - share_other_grey_sources) * (energy_demand - (share_green * energy_demand))

def run_market_share_added_value(new_infra_projects,
                                 port_dues,
                                 financial_properties,
                                 type_of_project,
                                 run_times):

    def calculate_added_value(t_year):
        if t_year < starting_year:

            return 0
        else:
            return added_value_market_share       # if t > starting year, added value of project is added to MS_AV

    number_of_new_projects = len(new_infra_projects.columns) # define number of new projects

    MS_AV_list = []
    temp_MS_AV_list = []

    # New infra projects
    if type_of_project == "Infrastructure":
        MS_AV_list = []
        starting_year = new_infra_projects.get_value('Construction           year',1)
        added_value_market_share = new_infra_projects.get_value('Expected added value to market share',1)
        if added_value_market_share != added_value_market_share:
            MS_AV_list = run_times * [0]
        else:
            for t_year in range(0, run_times):
                MS_AV_list.append(calculate_added_value(t_year+2017))  

    # Commercial actions - port dues
    if type_of_project == "Commercial action - port dues":     
        starting_year = port_dues.get_value('Coal', 'Starting year')
        added_value_market_share = port_dues.get_value('Coal', 'Expected added value to market share')    
        if added_value_market_share != added_value_market_share:
            MS_AV_list = run_times * [0]
        else:
            for t_year in range(0, run_times):
                MS_AV_list.append(calculate_added_value(t_year+2017))      

    # Commercial actions - land renting
    if type_of_project == "Commercial action - land renting": 
        starting_year = financial_properties.get_value('Land renting', 'Starting year')
        added_value_market_share = financial_properties.get_value('Land renting', 'Expected added value to market share')  
        if added_value_market_share != added_value_market_share:
            MS_AV_list = run_times * [0]
        else:
            for t_year in range(0, run_times):
                MS_AV_list.append(calculate_added_value(t_year+2017))        

    # Commercial actions - Indexation - Land renting
    if type_of_project == "Indexation - land renting": 
        starting_year = financial_properties.get_value('Indexation - Land renting', 'Starting year')
        added_value_market_share = financial_properties.get_value('Indexation - Land renting', 'Expected added value to market share')  
        if added_value_market_share != added_value_market_share:
            MS_AV_list = run_times * [0]
        else:
            for t_year in range(0, run_times):
                MS_AV_list.append(calculate_added_value(t_year+2017))   

    # Commercial actions - Indexation - Port dues
    if type_of_project == "Indexation - land renting": 
        starting_year = financial_properties.get_value('Indexation - Port dues', 'Starting year')
        added_value_market_share = financial_properties.get_value('Indexation - Port dues', 'Expected added value to market share')  
        if added_value_market_share != added_value_market_share:
            MS_AV_list = run_times * [0]
        else:
            for t_year in range(0, run_times): #ranget aangepast
                MS_AV_list.append(calculate_added_value(t_year+2017))     

    # Current values (MS AV = 0)
    if type_of_project == "Current values":
        MS_AV_list = run_times * [0]
        
    market_share_added_value = MS_AV_list

    market_share_added_value = np.array(market_share_added_value)     # convert list to array, otherwise error with Netlogo coupling

    return market_share_added_value

def calculate_market_share_base(t, market_share_init, market_share_base_growth_f):
    return market_share_init + (market_share_init * market_share_base_growth_f)  * (t) 

def calculate_market_share_added_value(new_infra_projects, port_dues, 
                                       financial_properties, type_of_project, run_times):
    market_share_added_value = run_market_share_added_value(new_infra_projects, port_dues, financial_properties, type_of_project, run_times)
    return market_share_added_value


def calculate_market_share_Rdam(t, new_infra_projects, port_dues, 
                                financial_properties, market_share_init, 
                                market_share_base_growth_f,
                                type_of_project, run_times):
    market_share_base = calculate_market_share_base(t, market_share_init, market_share_base_growth_f)
    market_share_added_value = calculate_market_share_added_value(new_infra_projects, port_dues, financial_properties, type_of_project, run_times)
    return market_share_base + market_share_added_value

def calculate_coal_throughput_Rdam(t,energy_demand_init, energy_demand_growth_f,
                                   c, a, u, green_share_init, 
                                   other_grey_share_init, other_grey_share_growth_f,
                                   market_share_init, market_share_base_growth_f, 
                                   type_of_project, run_times, financial_properties,
                                   new_infra_projects, port_dues):
    coal_demand_HLH = calculate_coal_demand_HLH(t,
                                                energy_demand_init, energy_demand_growth_f, 
                                                c, a, u, green_share_init,
                                                other_grey_share_init, other_grey_share_growth_f)
    market_share_Rdam = calculate_market_share_Rdam(t, new_infra_projects, port_dues, 
                                                    financial_properties, market_share_init, 
                                                    market_share_base_growth_f,
                                                    type_of_project, run_times)
    return coal_demand_HLH * market_share_Rdam 


def run_netlogo(netlogo, data_areas, coal_throughput_Rdam, run_times, data_terminals_file_name_run):
    
    coal_throughput_Rdam_str = ' '.join(map(str, (coal_throughput_Rdam)))

    netlogo.command('setup_clear')
    netlogo.command('set data-terminals "' + data_terminals_file_name_run + '"')
    netlogo.command('set data-areas "' + data_areas + '"')
    netlogo.command('setup')
    netlogo.command('set TP_Coal_CD_model_NL [' + coal_throughput_Rdam_str + ']')

    number_of_areas = int(netlogo.report('count areas')) # because starting at who=0
    number_of_terminals = int(netlogo.report('count terminals'))

    area_capacity= []
    area_capacity_unused = []
    area_TP = []
    area_occupancy = []
    area_denied_infra_cap = []
    area_denied_cap_percentage = []

    terminal_capacity= []
    terminal_capacity_unused = []
    terminal_TP = []
    terminal_occupancy = []
    terminal_capacity_expanded = []
    terminal_capacity_initial = []
    terminal_denied_infra_cap = []
    terminal_surface = []

    TP_without_terminal = []
    total_TP_rdam = []
    total_surface_terminals = []


    for i in range(0, number_of_areas):
        area_capacity.append([])
        area_capacity_unused.append([])
        area_TP.append([])
        area_occupancy.append([])
        area_denied_infra_cap.append([])
        area_denied_cap_percentage.append([])

    for i in range(0, number_of_terminals):
        terminal_capacity.append([])
        terminal_capacity_unused.append([])
        terminal_TP.append([])
        terminal_occupancy.append([])
        terminal_capacity_expanded.append([])
        terminal_capacity_initial.append([])    
        terminal_denied_infra_cap.append([])  
        terminal_surface.append([])

    netlogo.repeat_command('go', run_times)
    for i in range(0, number_of_areas):
        area_capacity[i] = netlogo.report('first [area-cap-current-list] of areas with [area-id = '+str(i)+']')
        area_capacity_unused[i] = netlogo.report('first [area-cap-unused-list] of areas with [area-id = '+str(i)+']')
        area_TP[i] = netlogo.report('first [area-TP-final-list] of areas with [area-id = '+str(i)+']')
        area_occupancy[i] = netlogo.report('first [area-occupancy-list] of areas with [area-id = '+str(i)+']')
        area_denied_infra_cap[i] = netlogo.report('first [area-infra-check-denied-cap-final-list] of areas with [area-id = '+str(i)+']')
        area_denied_cap_percentage[i] = netlogo.report('first [area-percentage-denied-cap-list] of areas with [area-id = '+str(i)+']')


    for i in range(0, number_of_terminals): 
        terminal_capacity[i] = netlogo.report('first [terminal-cap-current-list] of terminals with [terminal-id = '+str(i)+']')
        terminal_capacity_unused[i] = netlogo.report('first [terminal-cap-unused-list] of terminals with [terminal-id = '+str(i)+']')
        terminal_TP[i] = netlogo.report('first [terminal-TP-final-list] of terminals with [terminal-id = '+str(i)+']')
        terminal_occupancy[i] = netlogo.report('first [terminal-occupancy-list] of terminals with [terminal-id = '+str(i)+']')
        terminal_capacity_expanded[i] = netlogo.report('first [terminal-cap-expanded-list] of terminals with [terminal-id = '+str(i)+']')
        terminal_capacity_initial[i] = netlogo.report('first [terminal-cap-initial-list] of terminals with [terminal-id = '+str(i)+']')
        terminal_denied_infra_cap[i] = netlogo.report('first [terminal-infra-check-denied-cap-final-list] of terminals with [terminal-id = '+str(i)+']')
        terminal_surface[i] = netlogo.report('first [terminal-surface-list] of terminals with [terminal-id = '+str(i)+']')

    TP_without_terminal = netlogo.report('TP-without-terminal-list')
    total_TP_rdam = netlogo.report('total-TP-rdam-list')
    total_surface_terminals = netlogo.report('total-surface-terminals-list')

    outcomes = {}
    outcomes['area_capacity'] = area_capacity
    outcomes['area_capacity_unused'] = area_capacity_unused
    outcomes['area_TP'] = area_TP
    outcomes['area_occupancy'] = area_occupancy
    outcomes['area_denied_infra_cap'] = area_denied_infra_cap
    outcomes['area_denied_cap_percentage'] = area_denied_cap_percentage
    outcomes['terminal_capacity'] = terminal_capacity 
    outcomes['terminal_capacity_unused'] = terminal_capacity_unused
    outcomes['terminal_TP'] = terminal_TP
    outcomes['terminal_occupancy'] = terminal_occupancy
    outcomes['terminal_capacity_expanded'] = terminal_capacity_expanded
    outcomes['terminal_capacity_initial'] = terminal_capacity_initial
    outcomes['terminal_denied_infra_cap'] = terminal_denied_infra_cap
    outcomes['terminal_surface'] = terminal_surface
    outcomes['TP_without_terminal'] = TP_without_terminal
    outcomes['total_TP_rdam'] = total_TP_rdam
    outcomes['total_surface_terminals'] = total_surface_terminals

    
    return outcomes

def calculate_business_case(port_dues_coal, land_renting_price, terminal_TP, terminal_surface):
    terminal_TP_bc = []
    for i in range(0,len(terminal_TP)):
        s = pd.Series(terminal_TP[i])
        terminal_TP_bc.append((s * port_dues_coal).tolist())
        
    terminal_surface_bc = []
    for i in range(0,len(terminal_surface)):
        s = pd.Series(terminal_surface[i])
        terminal_surface_bc.append((s * land_renting_price).tolist())    
        
    business_case_terminal = []
    for i in range(0,len(terminal_TP)):
        business_case_terminal.append(list(map(operator.add,terminal_TP_bc[i],terminal_surface_bc[i])))

    return business_case_terminal 

def calculate_business_value_pora(port_dues_coal, land_renting_price, total_TP_rdam, total_surface_terminals):
    s = pd.Series(total_TP_rdam)
    income_port_dues_coal = (s * port_dues_coal).tolist()

    s = pd.Series(total_surface_terminals)
    income_rent_terminals = (s * land_renting_price).tolist()

    business_value_PoRA = list(map(operator.add,income_port_dues_coal,income_rent_terminals ))
    
    return business_value_PoRA

def calculate_yearly_costs_infra_project(new_infra_projects, run_times):
        yearly_costs_infra_project = new_infra_projects.get_value('Yearly costs',1)
        starting_year = new_infra_projects.get_value('Construction           year',1)
        yearly_costs_infra_project_list = []
        for t in range(0, run_times):
            if t < starting_year:
                yearly_costs_infra_project_list.append(0)
            else:
                yearly_costs_infra_project_list.append(yearly_costs_infra_project)
        return yearly_costs_infra_project_list

# run the model ecosystem for the assessment of the land issue project, with the new terminal included in the data
def run_ecosystem(netlogo,
                  data_areas,
                  port_dues,
                  port_dues_coal,
                  land_renting_price,
                  financial_properties,
                  energy_demand_init,
                  energy_demand_growth_f,
                  c,
                  a, 
                  u,
                  green_share_init, 
                  other_grey_share_init, 
                  other_grey_share_growth_f, 
                  market_share_init,
                  market_share_base_growth_f, 
                  type_of_project,
                  run_times, 
                  data_terminals_file_name_run,
                  new_infra_projects):

    t = np.arange(0, run_times, 1)

    run_times = run_times
    market_share_Rdam = calculate_market_share_Rdam(t, new_infra_projects, port_dues, 
                                                    financial_properties, market_share_init, 
                                                    market_share_base_growth_f, type_of_project, run_times)

    coal_throughput_Rdam = calculate_coal_throughput_Rdam(t,energy_demand_init, energy_demand_growth_f,
                                                          c, a, u, green_share_init, 
                                                          other_grey_share_init, other_grey_share_growth_f,
                                                          market_share_init, market_share_base_growth_f, 
                                                          type_of_project, run_times, financial_properties,
                                                          new_infra_projects, port_dues)

    data_result = run_netlogo(netlogo, data_areas, coal_throughput_Rdam, run_times, data_terminals_file_name_run)

    terminal_TP = data_result['terminal_TP']
    terminal_surface = data_result['terminal_surface']
    total_TP_rdam = data_result['total_TP_rdam']
    total_surface_terminals = data_result['total_surface_terminals']

    business_case_terminal = calculate_business_case(port_dues_coal, land_renting_price, terminal_TP, terminal_surface)
    business_value_pora = calculate_business_value_pora(port_dues_coal, land_renting_price, total_TP_rdam, total_surface_terminals)

    return (business_case_terminal, business_value_pora, data_result,
            coal_throughput_Rdam, market_share_Rdam)

def run_assess_project(netlogo, 
                       data_areas,
                       port_dues, 
                       port_dues_coal,
                       land_renting_price,
                       data_terminals_file_name_current,
                       data_terminals_file_name_project,
                       new_infra_projects,
                       financial_properties,
                       discount_rate,
                       energy_demand_init, 
                       energy_demand_growth_f, 
                       c,
                       a,
                       u,
                       green_share_init,
                       other_grey_share_init,
                       other_grey_share_growth_f,
                       market_share_init,
                       market_share_base_growth_f,      
                       run_times,
                       project_to_assess
                       ):
    
    
    business_case_terminal_current, business_value_pora_current, data_result_current, coal_throughput_Rdam_current, market_share_Rdam_current = \
    run_ecosystem(netlogo,
                  data_areas,
                  port_dues,
                  port_dues_coal,
                  land_renting_price,
                  financial_properties,
                  energy_demand_init,
                  energy_demand_growth_f,
                  c,
                  a, 
                  u,
                  green_share_init, 
                  other_grey_share_init, 
                  other_grey_share_growth_f, 
                  market_share_init,
                  market_share_base_growth_f, 
                  'Current values',
                  run_times, 
                  data_terminals_file_name_current,
                  new_infra_projects)
    
    business_case_terminal_project, business_value_pora_project, data_result_project, coal_throughput_Rdam_project, market_share_Rdam_project = \
    run_ecosystem(netlogo,
                  data_areas,
                  port_dues,
                  port_dues_coal,
                  land_renting_price,
                  financial_properties,
                  energy_demand_init,
                  energy_demand_growth_f,
                  c,
                  a, 
                  u,
                  green_share_init, 
                  other_grey_share_init, 
                  other_grey_share_growth_f, 
                  market_share_init,
                  market_share_base_growth_f, 
                  project_to_assess,
                  run_times, 
                  data_terminals_file_name_project,
                  new_infra_projects)
    
    
    area_capacity_current = data_result_current['area_capacity']
    area_capacity_unused_current = data_result_current['area_capacity_unused']
    area_TP_current = data_result_current['area_TP']
    area_occupancy_current = data_result_current['area_occupancy']
    area_denied_infra_cap_current = data_result_current['area_denied_infra_cap']
    area_denied_cap_percentage_current = data_result_current['area_denied_cap_percentage']
    terminal_capacity_current = data_result_current['terminal_capacity']
    terminal_capacity_unused_current = data_result_current['terminal_capacity_unused']
    terminal_TP_current = data_result_current['terminal_TP']
    terminal_occupancy_current = data_result_current['terminal_occupancy']
    terminal_capacity_expanded_current = data_result_current['terminal_capacity_expanded']
    terminal_capacity_initial_current = data_result_current['terminal_capacity_initial']
    terminal_denied_infra_cap_current = data_result_current['terminal_denied_infra_cap']
    terminal_surface_current = data_result_current['terminal_surface']
    TP_without_terminal_current = data_result_current['TP_without_terminal']
    total_TP_rdam_current = data_result_current['total_TP_rdam']
    total_surface_terminals_current = data_result_current['total_surface_terminals']    
    

    area_capacity_project = data_result_project['area_capacity']
    area_capacity_unused_project = data_result_project['area_capacity_unused']
    area_TP_project = data_result_project['area_TP']
    area_occupancy_project = data_result_project['area_occupancy']
    area_denied_infra_cap_project = data_result_project['area_denied_infra_cap']
    area_denied_cap_percentage_project = data_result_project['area_denied_cap_percentage']
    terminal_capacity_project = data_result_project['terminal_capacity']
    terminal_capacity_unused_project = data_result_project['terminal_capacity_unused']
    terminal_TP_project = data_result_project['terminal_TP']
    terminal_occupancy_project = data_result_project['terminal_occupancy']
    terminal_capacity_expanded_project = data_result_project['terminal_capacity_expanded']
    terminal_capacity_initial_project = data_result_project['terminal_capacity_initial']
    terminal_denied_infra_cap_project = data_result_project['terminal_denied_infra_cap']
    terminal_surface_project = data_result_project['terminal_surface']
    TP_without_terminal_project = data_result_project['TP_without_terminal']
    total_TP_rdam_project = data_result_project['total_TP_rdam']
    total_surface_terminals_project = data_result_project['total_surface_terminals']  

    construction_costs_infra_project = new_infra_projects.get_value('Construction costs',1)
    yearly_costs_infra_project = calculate_yearly_costs_infra_project(new_infra_projects, run_times)

    
    total_added_income_project = list(map(operator.sub, business_value_pora_project, business_value_pora_current ))
    net_income_infra_project = list(map(operator.sub, total_added_income_project, yearly_costs_infra_project))

    NPV_list = []
    for t in range(0,run_times):
        NPV_list.append((net_income_infra_project[t] / (1 + discount_rate) ** t )) 
    NPV = sum(NPV_list) - construction_costs_infra_project

    return area_capacity_current, area_capacity_unused_current, area_TP_current, area_occupancy_current,\
    area_denied_infra_cap_current, area_denied_cap_percentage_current, terminal_capacity_current, terminal_capacity_unused_current,\
    terminal_TP_current, terminal_occupancy_current, terminal_capacity_expanded_current,terminal_capacity_initial_current, \
    terminal_denied_infra_cap_current,terminal_surface_current, TP_without_terminal_current, total_TP_rdam_current,\
    total_surface_terminals_current, business_case_terminal_current, business_value_pora_current, area_capacity_project,\
    area_capacity_unused_project, area_TP_project, area_occupancy_project, area_denied_infra_cap_project,\
    area_denied_cap_percentage_project, terminal_capacity_project, terminal_capacity_unused_project, terminal_TP_project,\
    terminal_occupancy_project, terminal_capacity_expanded_project, terminal_capacity_initial_project, \
    terminal_denied_infra_cap_project, terminal_surface_project, TP_without_terminal_project, total_TP_rdam_project, \
    total_surface_terminals_project, business_case_terminal_project, business_value_pora_project, coal_throughput_Rdam_project, \
    market_share_Rdam_project, coal_throughput_Rdam_current, market_share_Rdam_current, NPV,
    


class IntegratedModel(Replicator, FileModel):
    
    def __init__(self, name, wd=None):
        super(IntegratedModel, self).__init__(name, wd=wd, 
                                          model_file='Satisficing 0409.nlogo')
        
        self.netlogo_model = 'Satisficing.nlogo'
        self.data_terminals_fn = 'DataTerminals - analysis.csv'
        self.data_areas = 'DataAreas.csv'
        self.data_terminals_current_fn = 'DataTerminals - current.csv'
        self.data_new_projects = 'Port_characteristics.xlsm'
        
        self.read_excel_file()
        
    def read_excel_file(self):
        excel_file = os.path.join(self.working_directory, self.data_new_projects)
        
        commercial_port_properties = pd.read_excel(excel_file,
                                   sheetname='New project - commercial', 
                                   parse_cols='B:I', header=None)
        
        port_dues = commercial_port_properties.drop(commercial_port_properties.columns[[ 2, 4, 7]], axis=1)
        port_dues = port_dues.drop(port_dues.index[[0,1,2,3,13,14,15,16,17,18, 19, 20]])

        list_columns = port_dues[0].tolist()
        port_dues.index = list_columns
        self.port_dues = port_dues.drop(port_dues .columns[[ 0]], axis=1)
        self.port_dues.columns = ['current values', 'analysis values','Expected added value to market share', 'Starting year']
        self.port_dues_coal = self.port_dues.get_value('Coal', 'analysis values')
        
        #FINANCIAL PROPERTIES
        financial_properties = commercial_port_properties.drop(commercial_port_properties.columns[[ 2, 4, 7]], axis=1)
        financial_properties = financial_properties.drop(financial_properties.index[[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,18]])
        
        list_columns = financial_properties[0].tolist()
        financial_properties.index = list_columns
        self.financial_properties = financial_properties.drop(financial_properties.columns[[0]], axis=1)
        self.financial_properties.columns = ['current values', 'analysis values', 'Expected added value to market share' , 'Starting year']

        self.land_renting_price = self.financial_properties.get_value('Land renting','analysis values')
        self.discount_rate = self.financial_properties.get_value('Discount rate','analysis values')
        self.indexation_land_renting = self.financial_properties.get_value('Indexation - Land renting','analysis values')
        self.indexation_port_dues = self.financial_properties.get_value('Indexation - Port dues','analysis values')
        
        new_infra_projects = pd.read_excel(excel_file, sheetname='New project - infrastructure', parse_cols='D:J', header=None)
        new_infra_projects = new_infra_projects.drop(new_infra_projects.columns[[ 1, 2, 4, 5]], axis=1)
        self.new_infra_projects = new_infra_projects.drop(new_infra_projects.index[[0,1,2,3,4,5]])
        self.new_infra_projects.index = ['name', 'Area', 'Type', 'Extra capacity', 'Expected added value to market share', 'Construction           year', 'Construction costs', 'Yearly costs']
        self.new_infra_projects.columns = [1,2,3]

    def model_init(self, policy):
        super(IntegratedModel, self).model_init(policy)
        
        # import Netlogo model
        self.netlogo = pyNetLogo.NetLogoLink()
        self.netlogo.load_model(os.path.join(self.working_directory, self.netlogo_model))
        self.netlogo.NL_VERSION='6.0'

    def run_experiment(self, experiment):

        model_output = run_assess_project(self.netlogo, 
                                          self.data_areas,
                                          self.port_dues,
                                          self.port_dues_coal, 
                                          self.land_renting_price, 
                                          self.data_terminals_current_fn, 
                                          self.data_terminals_fn, 
                                          self.new_infra_projects,
                                          self.financial_properties,
                                          self.discount_rate, **experiment)
        
        results  = {}
        for i, variable in enumerate(self.output_variables):
            try:
                value = model_output[variable]
            except KeyError:
                ema_logging.warning(variable +' not found in model output')
                value  = None
            except TypeError:
                value = model_output[i]
            results[variable] = value
        return results

def mean_over_replications(data):
		return np.mean(data, axis=0)
    
if __name__ == '__main__':
    ema_logging.LOG_FORMAT = '[%(name)s/%(levelname)s/%(processName)s] %(message)s'
    ema_logging.log_to_stderr(ema_logging.INFO)
    
    def mean_over_replications(data):
        return np.mean(data, axis=0)
    
    model = IntegratedModel('Model_ecosystem', wd='./model')
    model.replications = 2


    #specify uncertainties
	model.uncertainties = [RealParameter("energy_demand_growth_f",-0.006, 0.013),
                            RealParameter("a",0,0.2),
                            RealParameter("market_share_base_growth_f", -0.02, 0.02),
                            IntegerParameter("u", 0,39),
                            RealParameter("c",0.03,0.733),
                            RealParameter("other_grey_share_growth_f", -0.015,0.015)
                          ]
                        	
                      	
   
    #specify outcomes 
    model.outcomes = [TimeSeriesOutcome('area_capacity_current', function=mean_over_replications),    
                    TimeSeriesOutcome('area_capacity_unused_current', function=mean_over_replications),           
                    TimeSeriesOutcome('area_TP_current', function=mean_over_replications),                       
                    TimeSeriesOutcome('area_occupancy_current', function=mean_over_replications),                
                    TimeSeriesOutcome('area_denied_infra_cap_current', function=mean_over_replications),          
                    TimeSeriesOutcome('area_denied_cap_percentage_current', function=mean_over_replications),     
                    TimeSeriesOutcome('terminal_capacity_current', function=mean_over_replications),              
                    TimeSeriesOutcome('terminal_capacity_unused_current', function=mean_over_replications),       
                    TimeSeriesOutcome('terminal_TP_current', function=mean_over_replications),                    
                    TimeSeriesOutcome('terminal_occupancy_current', function = mean_over_replications),             
                    TimeSeriesOutcome('terminal_capacity_expanded_current', function=mean_over_replications),     
                    TimeSeriesOutcome('terminal_capacity_initial_current', function=mean_over_replications),      
                    TimeSeriesOutcome('terminal_denied_infra_cap_current', function=mean_over_replications),      
                    TimeSeriesOutcome('terminal_surface_current', function=mean_over_replications),               
                    TimeSeriesOutcome('TP_without_terminal_current', function=mean_over_replications),            
                    TimeSeriesOutcome('total_TP_rdam_current', function=mean_over_replications),                  
                    TimeSeriesOutcome('total_surface_terminals_current', function=mean_over_replications),          
                    TimeSeriesOutcome('business_case_terminal_current', function=mean_over_replications),         
                    TimeSeriesOutcome('business_value_pora_current', function=mean_over_replications),            
                    TimeSeriesOutcome('area_capacity_project', function=mean_over_replications),                  
                    TimeSeriesOutcome('area_capacity_unused_project', function=mean_over_replications),           
                    TimeSeriesOutcome('area_TP_project', function=mean_over_replications),                        
                    TimeSeriesOutcome('area_occupancy_project', function=mean_over_replications),                 
                    TimeSeriesOutcome('area_denied_infra_cap_project', function=mean_over_replications),          
                    TimeSeriesOutcome('area_denied_cap_percentage_project', function=mean_over_replications),     
                    TimeSeriesOutcome('terminal_capacity_project', function=mean_over_replications),              
                    TimeSeriesOutcome('terminal_capacity_unused_project', function=mean_over_replications),       
                    TimeSeriesOutcome('terminal_TP_project', function=mean_over_replications),                    
                    TimeSeriesOutcome('terminal_occupancy_project', function=mean_over_replications),             
                    TimeSeriesOutcome('terminal_capacity_expanded_project', function=mean_over_replications),     
                    TimeSeriesOutcome('terminal_capacity_initial_project', function=mean_over_replications),      
                    TimeSeriesOutcome('terminal_denied_infra_cap_project', function=mean_over_replications),      
                    TimeSeriesOutcome('terminal_surface_project', function=mean_over_replications),               
                    TimeSeriesOutcome('TP_without_terminal_project', function=mean_over_replications),            
                    TimeSeriesOutcome('total_TP_rdam_project', function=mean_over_replications),                  
                    TimeSeriesOutcome('total_surface_terminals_project', function=mean_over_replications),  
                    TimeSeriesOutcome('business_case_terminal_project', function=mean_over_replications),
                    TimeSeriesOutcome('business_value_pora_project', function=mean_over_replications),               
                    TimeSeriesOutcome('coal_throughput_Rdam_project', function=mean_over_replications),
                    TimeSeriesOutcome('market_share_Rdam_project', function=mean_over_replications),
                    TimeSeriesOutcome('coal_throughput_Rdam_current', function=mean_over_replications),
                    TimeSeriesOutcome('market_share_Rdam_current', function=mean_over_replications),
                    ScalarOutcome('NPV', function=mean_over_replications)]



    model.constants = [Constant('run_times', 40),
                      Constant('project_to_assess','Current values'),
                      Constant('energy_demand_init', 30000000),
                      Constant('other_grey_share_init', 0.3),
                      Constant('green_share_init', 0.13),
                      Constant('market_share_init',0.15)]
                     

       
