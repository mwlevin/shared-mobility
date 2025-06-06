import contextlib
from src import Node, Link, Path, Zone, Bush, Params, PASList, PAS, Network
import Optimization, OptimizationCG
import math, time
from src import Heap
from gurobipy import Model, GRB, quicksum
import sys
import numpy as np
import matplotlib.pyplot as plt
import ModeChoice
import iterativeclass

# # Define the scenarios with manually entered values
# scenarios = {
#     "Base Scenario": {"uber_price": 10, "ev_price": 16.4, "ev_ovtt": 0, "congestion": 15.0, "vmt": 1.326e7, "private_vehicle_percentage": 61, "rebalancing_trips": 50000, "tncs_percentage": 21},
#     "Scenario 1": {"uber_price": 50, "ev_price": 16.4, "ev_ovtt": 0, "congestion": 25.0, "vmt": 1.29e7, "private_vehicle_percentage": 68, "rebalancing_trips": 25000, "tncs_percentage": 9.82},
#     "Scenario 2": {"uber_price": 10, "ev_price": 2, "ev_ovtt": -7, "congestion": 10.0, "vmt": 1.33e7, "private_vehicle_percentage": 33, "rebalancing_trips": 35000, "tncs_percentage": 10}
# }

# # Initialize the results dictionaries for the bar charts
# tstt_results = {}
# congestion_results = {}
# vmt_results = {}
# private_vehicle_results = {}
# rebalancing_trips_results = {}
# tncs_results = {}

# # Run the simulations for each scenario
# for scenario_name, params in scenarios.items():
#     print(f"Running simulation for {scenario_name}")
#     simulation = iterativeclass.MobilitySimulation(params["uber_price"], params["ev_price"], params["ev_ovtt"])
#     tstt = simulation.network.tstt_values[-1]  # Get the TSTT value from the last iteration
#     congestion = params["congestion"]  # Use the manually entered congestion percentage
#     vmt = params["vmt"]  # Use the manually entered VMT value
#     private_vehicle_percentage = params["private_vehicle_percentage"]  # Use the manually entered private vehicle percentage
#     rebalancing_trips = params["rebalancing_trips"]  # Use the manually entered number of rebalancing trips
#     tncs_percentage = params["tncs_percentage"]  # Use the manually entered TNCs percentage
#     tstt_results[scenario_name] = tstt
#     congestion_results[scenario_name] = congestion
#     vmt_results[scenario_name] = vmt
#     private_vehicle_results[scenario_name] = private_vehicle_percentage
#     rebalancing_trips_results[scenario_name] = rebalancing_trips
#     tncs_results[scenario_name] = tncs_percentage

# # Plot the TSTT results as a bar chart
# plt.figure()
# bars = plt.bar(tstt_results.keys(), tstt_results.values(), width=0.4)  # Set bar width to 0.4
# plt.title('TSTT for Different Scenarios')
# plt.xlabel('Scenario')
# plt.ylabel('TSTT')

# # Add values above the bars
# for bar in bars:
#     yval = bar.get_height()
#     plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}', ha='center', va='bottom')

# plt.show()

# # Plot the congestion results as a bar chart
# plt.figure()
# bars = plt.bar(congestion_results.keys(), congestion_results.values(), width=0.4)  # Set bar width to 0.4
# plt.title('Congestion Percentage for Different Scenarios')
# plt.xlabel('Scenario')
# plt.ylabel('Congestion Percentage')

# # Add values above the bars
# for bar in bars:
#     yval = bar.get_height()
#     plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}', ha='center', va='bottom')

# plt.show()

# # Plot the VMT results as a bar chart
# plt.figure()
# bars = plt.bar(vmt_results.keys(), vmt_results.values(), width=0.4)  # Set bar width to 0.4
# plt.title('VMT for Different Scenarios')
# plt.xlabel('Scenario')
# plt.ylabel('VMT')

# # Add values above the bars
# for bar in bars:
#     yval = bar.get_height()
#     plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2e}', ha='center', va='bottom')

# plt.show()

# # Plot the private vehicle percentage results as a bar chart
# plt.figure()
# bars = plt.bar(private_vehicle_results.keys(), private_vehicle_results.values(), width=0.4)  # Set bar width to 0.4
# plt.title('Private Vehicle Percentage for Different Scenarios')
# plt.xlabel('Scenario')
# plt.ylabel('Private Vehicle Percentage')

# # Add values above the bars
# for bar in bars:
#     yval = bar.get_height()
#     plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}', ha='center', va='bottom')

# plt.show()

# # Plot the rebalancing trips results as a bar chart
# plt.figure()
# bars = plt.bar(rebalancing_trips_results.keys(), rebalancing_trips_results.values(), width=0.4)  # Set bar width to 0.4
# plt.title('Rebalancing Trips for Different Scenarios')
# plt.xlabel('Scenario')
# plt.ylabel('Number of Rebalancing Trips')

# # Add values above the bars
# for bar in bars:
#     yval = bar.get_height()
#     plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}', ha='center', va='bottom')

# plt.show()

# # Plot the TNCs percentage results as a bar chart
# plt.figure()
# bars = plt.bar(tncs_results.keys(), tncs_results.values(), width=0.4)  # Set bar width to 0.4
# #plt.title('TNCs Percentage for Different Scenarios')
# plt.xlabel('Scenario')
# plt.ylabel('TNCs Percentage')

# # Add values above the bars
# for bar in bars:
#     yval = bar.get_height()
#     plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}', ha='center', va='bottom')

# plt.show()



# Define the range of prices
uber_price_range = np.linspace(10, 50, 5)  # Generates 5 values from 10 to 50
ev_price_range = np.linspace(5, 30, 5)  # Generates 5 values from 5 to 30

# Initialize the results arrays for the contour plots
congestion_results = np.zeros((len(uber_price_range), len(ev_price_range)))
private_vehicle_results = np.zeros((len(uber_price_range), len(ev_price_range)))
vmt_results = np.zeros((len(uber_price_range), len(ev_price_range)))  # New array for VMT

# Define a fixed EV price for the line plot
fixed_ev_price = 16

# Initialize the results lists for the line plots
congestion_line_plot = []
private_vehicle_line_plot = []
vmt_line_plot = []  # New list for VMT

# Run the simulations for each combination of prices
for i, uber_price in enumerate(uber_price_range):
    for j, ev_price in enumerate(ev_price_range):
        print(f"Running simulation for Uber price: {uber_price}, EV price: {ev_price}")
        simulation = iterativeclass.MobilitySimulation(uber_price, ev_price, 0)
        congestion = simulation.calculate_congestion()
        private_vehicle_percentage = simulation.get_private_vehicle_percentage()
        vmt = simulation.get_vmt()  # New method to get VMT
        congestion_results[i, j] = congestion
        private_vehicle_results[i, j] = private_vehicle_percentage
        vmt_results[i, j] = vmt  # Store the VMT result

    # Run the simulation for the fixed EV price and varying Uber price
    print(f"Running simulation for Uber price: {uber_price}, Fixed EV price: {fixed_ev_price}")
    simulation = iterativeclass.MobilitySimulation(uber_price, fixed_ev_price, 0)
    congestion = simulation.calculate_congestion()
    private_vehicle_percentage = simulation.get_private_vehicle_percentage()
    vmt = simulation.get_vmt()  # Get VMT for the line plot
    congestion_line_plot.append(congestion)
    private_vehicle_line_plot.append(private_vehicle_percentage)
    vmt_line_plot.append(vmt)  # Add VMT to the line plot list

# Plot the congestion results as a contour plot
X, Y = np.meshgrid(uber_price_range, ev_price_range)
plt.figure()
cp = plt.contourf(X, Y, congestion_results.T, cmap='viridis')
colorbar = plt.colorbar(cp)
colorbar.set_label('Congestion Percentage')
#plt.title('Congestion percentage by TNCs and EVs Pricing')
plt.xlabel('Uber Base Price ($)')
plt.ylabel('EV Base Price ($)')
plt.show()

# Plot the private vehicle results as a contour plot
plt.figure()
cp = plt.contourf(X, Y, private_vehicle_results.T, cmap='viridis')
colorbar = plt.colorbar(cp)
colorbar.set_label('Private Vehicle Percentage')
#plt.title('Percentage of Private vehicles by changes in TNCs and EVs Pricing')
plt.xlabel('Uber Base Price ($)')
plt.ylabel('EV Base Price ($)')
plt.show()


plt.figure()
cp = plt.contourf(X, Y, vmt_results.T, cmap='viridis')
colorbar = plt.colorbar(cp)
colorbar.set_label('VMT')
#plt.title('VMT by TNCs and EVs Pricing')
plt.xlabel('Uber Base Price ($)')
plt.ylabel('EV Base Price ($)')
plt.show()

# Plot the results as a line plot for fixed EV price - Congestion
plt.figure()
plt.plot(uber_price_range, congestion_line_plot, marker='o', linestyle='-')
#plt.title(f'Congestion vs TNCs Pricing')
plt.xlabel('Uber Base Price ($)')
plt.ylabel('Congestion percentage')
plt.grid(True)
plt.show()

# Plot the results as a line plot for fixed EV price - Private Vehicle Percentage
plt.figure()
plt.plot(uber_price_range, private_vehicle_line_plot, marker='o', linestyle='-')
#plt.title(f'Private Vehicle Percentage vs TNCs Pricing ')
plt.xlabel('Uber Base Price ($)')
plt.ylabel('Private Vehicle Percentage')
plt.grid(True)
plt.show()

# Plot the results as a line plot for fixed EV price - VMT
plt.figure()
plt.plot(uber_price_range, vmt_line_plot, marker='o', linestyle='-')
#plt.title(f'VMT vs TNCs Pricing')
plt.xlabel('Uber Base Price ($)')
plt.ylabel('VMT')
plt.grid(True)
plt.show()

