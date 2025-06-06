import numpy as np
from src import Network
from src import Zone
import contextlib
import numpy as np
from src import Network
from src import Zone
import Optimization
import numpy as np
import os
import matplotlib.pyplot as plt

class ModeChoice:
    def __init__(self, network, travel_times_file, initial_run=True):
        self.initial_run = initial_run
        self.network = network
        self.travel_times = Optimization.readTravelTimes(travel_times_file, network)
        self.modes = ['Private Vehicle', 'Public Transportation', 'Uber/Lyft', 'Shared Scooter or Bike', 'Shared Electric Vehicle']
        self.beta = {'intercept': -0.5, 'IVTT': -0.075522, 'OVTT': -0.432463, 'Cost': -0.016339}
        self.mode_percentages = []
        self.ovtt_dict = None  
        self.total_uber_demand = 0
        self.total_f_rs = 0
        self.uber_lyft_demand = {}  # Dictionary to hold Uber/Lyft specific demands

    def calculate_total_uber_demand(self):
        total_demand = 0
        for origin in self.network.zones:
            for destination in self.network.zones:
                total_demand += origin.getDemandUber(destination)
        return total_demand

   

    def calculate_utility(self, ivtt, ovtt, cost):
        return (self.beta['intercept'] + 
                self.beta['IVTT'] * ivtt + 
                self.beta['OVTT'] * ovtt + 
                self.beta['Cost'] * cost)
        
    def calculate_mode_utilities(self, origin, destination, demands):
        utilities = {}
        for mode in self.modes:
            ivtt = self.calculate_ivtt(origin, destination, mode)
            ovtt = self.calculate_ovtt(origin, destination, mode)
            cost = self.calculate_cost(origin, destination, mode)
            utilities[mode] = self.calculate_utility(ivtt, ovtt, cost)
        return utilities
    
    def calculate_ivtt(self, origin, destination, mode):
        travel_time = self.travel_times[(origin, destination)]
        if mode == 'Shared Scooter or Bike':
            ivtt = 3 * travel_time
        else:
            ivtt = travel_time
        return ivtt 

    def calculate_ovtt_uber(self):
        ovtt_dict = {}
        
        for destination in self.network.zones:
            ovtt1 = 0
            ovtt2 = 0
            for origin in self.network.zones:
                if origin != destination:
                    demand = origin.getDemandf(destination)
                    travel_time = self.travel_times[(origin, destination)]
                    ovtt1 += demand * travel_time
                    ovtt2 += demand
            if ovtt2 != 0:
                ovtt_dict[destination] = ovtt1 / (4.1 * ovtt2)
            else:
                ovtt_dict[destination] = 7

        self.ovtt_dict = ovtt_dict
        return ovtt_dict

    def calculate_ovtt(self, origin, destination, mode):
        if mode == "Private Vehicle":
            ovtt = np.random.uniform(1, 3)
        elif mode == "Public Transportation":
            ovtt = np.random.uniform(1, 5) + np.random.uniform(1, 15) + np.random.uniform(1, 5) 
        elif mode == "Uber/Lyft":
            if self.initial_run:
                ovtt = 1
            else:
                if self.ovtt_dict is None:
                    self.calculate_ovtt_uber()  
                ovtt = self.ovtt_dict.get(destination, 0)
        elif mode == "Shared Scooter or Bike":
            ovtt = np.random.uniform(1, 5) + np.random.uniform(1, 5)
        elif mode == "Shared Electric Vehicle":
            ovtt = np.random.uniform(1, 5) + np.random.uniform(1, 5)
        return ovtt
    
    def calculate_cost(self, origin, destination, mode):
        travel_time = self.travel_times[(origin, destination)]
        if mode == "Private Vehicle":
            cost = 0.5 + (0.1 * travel_time)
            #cost = 100000
        elif mode == "Public Transportation":
            cost = 2.5
            #cost = 100000
        elif mode == "Uber/Lyft":
            cost = 7 + (0.3 * travel_time)
            #cost = 100000
        elif mode == "Shared Scooter or Bike":
            cost = 1 + (0.39 * travel_time)
        elif mode == "Shared Electric Vehicle":
            #cost = ((16 / 60) * travel_time)
            cost = ((16/60)* travel_time)
        return cost
    
    def mode_choice_probabilities(self, utilities):
        exp_utilities = {mode: np.exp(utility) for mode, utility in utilities.items()}
        total_exp_utility = sum(exp_utilities.values())
        return {mode: exp_utility / total_exp_utility for mode, exp_utility in exp_utilities.items()}
        
    def distribute_demand(self, origin, destination, demand):
        utilities = self.calculate_mode_utilities(origin, destination, demand)
        probabilities = self.mode_choice_probabilities(utilities)
        mode_demands = {}
        for mode, prob in probabilities.items():
            mode_demand = demand * prob
            mode_demands[mode] = mode_demand
            if mode == 'Uber/Lyft':
                self.uber_lyft_demand[(origin.id, destination.id)] = mode_demand
        return mode_demands

    def solve_mode_choice(self):
        uber_demand_dict = {}
        results = {mode: {origin.id: {destination.id: 0 for destination in self.network.zones}
                        for origin in self.network.zones} for mode in self.modes}
        total_demand = 0
        self.mode_total_demand = {mode: 0 for mode in self.modes}  # Now it's an instance variable

        for origin in self.network.zones:
            for destination in self.network.zones:
                demand = origin.getDemandBeforeModeChoice(destination)
                if demand > 0:
                    mode_demands = self.distribute_demand(origin, destination, demand)
                    total_demand += demand
                    for mode, mode_demand in mode_demands.items():
                        self.mode_total_demand[mode] += mode_demand
                        results[mode][origin.id][destination.id] = mode_demand
                        if mode == 'Uber/Lyft' and mode_demand != 0:
                            uber_demand_dict[(origin, destination)] = mode_demand

        for mode in self.modes:
            self.write_results_to_file(mode, results[mode], total_demand, self.mode_total_demand[mode])
        
        mode_percentages = {mode: (self.mode_total_demand[mode] / total_demand) * 100 for mode in self.modes}
        self.mode_percentages.append(mode_percentages)
        
        return uber_demand_dict

   


    def write_results_to_file(self, mode, results, total_demand, mode_demand):
    # Define the base directory where files should be saved
        #base_dir = r"D:\DNDP-master 3"
        
        # Create a safe filename by replacing spaces and slashes
        #safe_mode_name = mode.replace(' ', '_').replace('/', '_').lower()
        #file_name = f"{safe_mode_name}_mode_choice_results.txt"
        
        # Combine the base directory and filename to create the full path
        #full_path = os.path.join(base_dir, file_name)
        
        # Ensure the directory exists, and if not, create it
        #os.makedirs(base_dir, exist_ok=True)
        safe_mode_name = mode.replace(' ', '_').replace('/', '_').lower()
        file_name = f"{safe_mode_name}_mode_choice_results.txt"
        # Write results to the file
        with open(file_name, "w") as file:
            file.write(f"Mode: {mode}\n")
            file.write(f"Total Demand: {total_demand:.1f}\n")
            file.write(f"Total Demand for {mode}: {mode_demand:.1f} ({mode_demand/total_demand:.1%})\n")
            file.write("<NUMBER OF ZONES> {}\n".format(len(self.network.getZones())))
            file.write("<TOTAL OD FLOW> {:.1f}\n".format(total_demand))
            file.write("<END OF METADATA>\n\n")
            
            for origin_id in results:
                file.write(f"Origin \t{origin_id}\n")
                line_count = 0
                line = ""
                for destination_id in results[origin_id]:
                    demand = results[origin_id][destination_id]
                    line += "    {} : {:.1f}; ".format(destination_id, demand)
                    line_count += 1
                    if line_count % 5 == 0:
                        file.write(line + "\n")
                        line = ""
                if line:
                    file.write(line + "\n")
                file.write("\n")
        
          
