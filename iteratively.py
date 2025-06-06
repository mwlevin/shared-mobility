import contextlib
from src import Node
from src import Link
from src import Path
from src import Zone
from src import Bush
from src import Params
from src import PASList
from src import PAS
from src import Network
import Optimization

import math
import time
from src import Heap
from gurobipy import Model, GRB, quicksum
import sys
import numpy as np
import matplotlib.pyplot as plt
import ModeChoice

def update_plots(all_runs_data):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    iterations = list(range(1, len(all_runs_data) + 1))
    
    tstt_values = [run_data['tstt_values'] for run_data in all_runs_data]
    sptt_values = [run_data['sptt_values'] for run_data in all_runs_data]
    tfftt_values = [run_data['tfftt_values'] for run_data in all_runs_data]
    gap_values = [run_data['gap_values'] for run_data in all_runs_data]
    aec_values = [run_data['aec_values'] for run_data in all_runs_data]

    ax1.plot(iterations, tstt_values, label='TSTT', marker='o')
    ax1.plot(iterations, sptt_values, label='SPTT', marker='x')
    ax1.plot(iterations, tfftt_values, label='TFFTT', marker='s')
    
    ax1.set_xlabel('Iteration of algorithm')
    ax1.set_ylabel('Time (min)')
    #ax1.set_title('TSTT, SPTT, and TFFTT over Iterations')
    ax1.legend()
    
    ax3 = ax2.twinx()
    ax2.plot(iterations, gap_values, label='Gap', marker='o', color='tab:blue')
    ax3.plot(iterations, aec_values, label='AEC', marker='x', color='tab:orange')
    
    ax2.set_xlabel('Iteration of algorithm')
    ax2.set_ylabel('Gap', color='tab:blue')
    ax3.set_ylabel('AEC', color='tab:orange')
    #ax2.set_title('Gap and AEC over Iterations')
    ax2.legend(loc='upper left')
    ax3.legend(loc='upper right')
    
    plt.tight_layout()
    plt.show()

def plot_differences(all_runs_data):
    if len(all_runs_data) < 2:
        print("Not enough runs to calculate differences.")
        return
    
    first_run = all_runs_data[0]
    last_run = all_runs_data[-1]

    # Ensure the runs have the same length by taking the minimum length
    min_length = min(len(first_run['tstt_values']), len(last_run['tstt_values']))

    differences_tstt = [last_run['tstt_values'][i] - first_run['tstt_values'][i] for i in range(min_length)]
    differences_sptt = [last_run['sptt_values'][i] - first_run['sptt_values'][i] for i in range(min_length)]
    differences_tfftt = [last_run['tfftt_values'][i] - first_run['tfftt_values'][i] for i in range(min_length)]

    iterations = range(min_length)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, differences_tstt, label='Difference in TSTT', marker='o')
    ax.plot(iterations, differences_sptt, label='Difference in SPTT', marker='x')
    ax.plot(iterations, differences_tfftt, label='Difference in TFFTT', marker='s')

    ax.set_xlabel('Iteration')
    ax.set_ylabel('Difference')
    ax.set_title('Differences between First and Last Run TSTT, SPTT, and TFFTT')
    ax.legend()

    plt.tight_layout()
    plt.show()


def plot_individual_runs(all_runs_data):
    num_runs = len(all_runs_data)
    fig, axes = plt.subplots(num_runs, 1, figsize=(10, 2 * num_runs))

    for run_index, run_data in enumerate(all_runs_data):
        ax = axes[run_index] if num_runs > 1 else axes
        ax.plot(run_data['iterations'], run_data['tstt_values'], label=f'TSTT Run {run_index+1}', marker='o')
        ax.plot(run_data['iterations'], run_data['sptt_values'], label=f'SPTT Run {run_index+1}', marker='x')
        ax.plot(run_data['iterations'], run_data['tfftt_values'], label=f'TFFTT Run {run_index+1}', marker='s')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Value')
        ax.set_title(f'TSTT, SPTT, and TFFTT for Run {run_index+1}')
        ax.legend()

    plt.tight_layout()
    plt.show()


def plot_vmt(all_runs_data):
    iterations = list(range(1, len(all_runs_data) + 1))
    vmt_values = [run_data['vmt_values'] for run_data in all_runs_data]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, vmt_values, label='VMT', marker='o')

    ax.set_xlabel('Iteration of algorithm')
    ax.set_ylabel('VMT')
    #ax.set_title('VMT over Iterations')
    ax.legend()

    plt.tight_layout()
    plt.show()

def plot_mode_percentages(all_mode_percentages):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    num_runs = len(all_mode_percentages)
    runs = range(1, num_runs + 1)
    mode_names = all_mode_percentages[0].keys()

    for mode in mode_names:
        percentages = [run[mode] for run in all_mode_percentages]
        #print(percentages)
        ax.plot(runs, percentages, label=mode, marker='o')

    ax.set_xlabel('Iteration of algorithm')
    ax.set_ylabel('Percentage of users choosing mode m')
    #ax.set_title('Mode Choice Percentages over Runs')
    ax.legend()

    plt.tight_layout()
    plt.show()


def plot_uber_demand_and_f_rs(uber_demand_values, f_rs_values):
    iterations = range(1, len(uber_demand_values) + 1)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, uber_demand_values, label='Total Uber Demand', marker='o')
    ax.plot(iterations, f_rs_values, label='Total f_rs', marker='x')
    
    ax.set_xlabel('Iteration of algorithm')
    ax.set_ylabel('Number of demand and trips')
    #ax.set_title('Total Uber Demand and Total f_rs over Iterations')
    ax.legend()
    
    plt.tight_layout()
    plt.show()

def plot_congestion(all_runs_data):
    iterations = list(range(1, len(all_runs_data) + 1))
    congestion_values = [((run_data['tstt_values'][-1] - run_data['tfftt_values'][-1])/run_data['tfftt_values'][-1])*100 for run_data in all_runs_data]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, congestion_values, label='Congestion percentage', marker='o')

    ax.set_xlabel('Iteration of algorirthm')
    ax.set_ylabel('Congestion percentage')
    #ax.set_title('Congestion over Iterations')
    ax.legend()

    plt.tight_layout()
    plt.show()

def plot_frs_vs_drs(uber_demand_values, f_rs_values):
    iterations = range(1, len(uber_demand_values) + 1)
    differences = [f_rs - d_rs for f_rs, d_rs in zip(f_rs_values, uber_demand_values)]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(iterations, differences, label='Rebalncing trips', marker='o')
    
    ax.set_xlabel('Iteration of algorithm')
    ax.set_ylabel('Number of rebalancing trips')
    #ax.set_title('Difference between f_rs and d_rs for Uber over Iterations')
    ax.legend()
    
    plt.tight_layout()
    plt.show()


########################################################
pas_instance = PAS.PAS()
start_time = time.time()
all_runs_data = []
all_mode_percentages = []
uber_demand_values = []
f_rs_values = []

network = Network.Network("Minneapolis", 0.5, 500, 60, 1, 600, "data/Minneapolis/trips.txt", "data/Minneapolis/trips.txt", "data/Minneapolis/trips.txt", "data/Minneapolis/trips.txt")

y1 = {(i, j): 1 for (i, j) in network.links2}
l0 = {(i, j): 0 for (i, j) in network.links2}
x0 = {(i, j): 0 for (i, j) in network.links2}
lbd = {(i, j): 1 for (i, j) in network.links2}

network.write_free_flow_travel_times_to_file()

mode_choice_solver = ModeChoice.ModeChoice(network, "free_flow_travel_times.txt", initial_run=True)
uber_demand_dict = mode_choice_solver.solve_mode_choice()
#all_mode_percentages.append(mode_choice_solver.mode_percentages[-1])
#uber_demand_values.append(mode_choice_solver.mode_total_demand["Uber/Lyft"])
#f_rs_values.append(mode_choice_solver.calculate_total_f_rs())

#network = Network.Network("SiouxFalls", 0.5, 500, 1e-0, 2, 600, "data/SiouxFalls/asymmetric_trips.txt", "shared_electric_vehicle_mode_choice_results.txt", "private_vehicle_mode_choice_results.txt", "uber_lyft_mode_choice_results.txt")
travel_times = Optimization.readTravelTimes('free_flow_travel_times.txt', network)
#demand_dict = network.create_demand_dict()
with open('resultdict.txt', 'w') as file, contextlib.redirect_stdout(file):
    print(uber_demand_dict)
Optimization.setup_and_solve_optimization(network, "Uber/Lyft", travel_times, uber_demand_dict)

network = Network.Network("Minneapolis", 0.5, 500, 60 , 1, 600, "trips_frs.txt", "shared_electric_vehicle_mode_choice_results.txt", "private_vehicle_mode_choice_results.txt", "uber_lyft_mode_choice_results.txt")

network.tapas('UE', l0, y1, x0)

# Initialize lists to store values for the first run
run_data = {
    'iterations': network.iterations,
    'tstt_values': network.tstt_values,
    'sptt_values': network.sptt_values,
    'gap_values': network.gap_values,
    'aec_values': network.aec_values,
    'tfftt_values': network.tfftt_values,
    'vmt_values': network.vmt_values
}
all_runs_data.append(run_data)

network.write_travel_times_to_file()

maximumIteration = 5
for run in range(maximumIteration):
    mode_choice_solver = ModeChoice.ModeChoice(network, "travel_times.txt", initial_run=False)
    uber_demand_dict = mode_choice_solver.solve_mode_choice()
    #mode_choice_solver.solve_mode_choice()
    all_mode_percentages.append(mode_choice_solver.mode_percentages[-1])

    #uber_demand_values.append(mode_choice_solver.calculate_total_uber_demand())
    uber_demand_values.append(mode_choice_solver.mode_total_demand["Uber/Lyft"])
    

    #network = Network.Network("SiouxFalls", 0.5, 500, 1e-0, 2, 600, "trips_frs.txt", "shared_electric_vehicle_mode_choice_results.txt", "private_vehicle_mode_choice_results.txt", "uber_lyft_mode_choice_results.txt")
    #demand_dict = network.create_demand_dict()
    #uber_demand_dict = mode_choice_solver.solve_mode_choice

    travel_times = Optimization.readTravelTimes('travel_times.txt', network)
    
    #Optimization.setup_and_solve_optimization(network, "Uber/Lyft", travel_times, uber_lyft_demand_dict)
    Optimization.setup_and_solve_optimization(network, "Uber/Lyft", travel_times, uber_demand_dict)
    f_rs_values.append(Optimization.setup_and_solve_optimization(network, "Uber/Lyft", travel_times, uber_demand_dict)
)


    network = Network.Network("Minneapolis", 0.5, 500, 60, 1, 600, "trips_frs.txt", "shared_electric_vehicle_mode_choice_results.txt", "private_vehicle_mode_choice_results.txt", "uber_lyft_mode_choice_results.txt")
    network.tapas('UE', l0, y1, x0)     
    network.write_travel_times_to_file() 
    
    run_data = {
        'iterations': network.iterations,
        'tstt_values': network.tstt_values,
        'sptt_values': network.sptt_values,
        'gap_values': network.gap_values,
        'aec_values': network.aec_values,
        'tfftt_values': network.tfftt_values,
        'vmt_values': network.vmt_values 
    }
    all_runs_data.append(run_data)

update_plots(all_runs_data)
#plot_differences(all_runs_data)
plot_individual_runs(all_runs_data)
plot_mode_percentages(all_mode_percentages)
plot_uber_demand_and_f_rs(uber_demand_values, f_rs_values)
plot_frs_vs_drs(uber_demand_values, f_rs_values)
plot_congestion(all_runs_data)
plot_vmt(all_runs_data)


    

