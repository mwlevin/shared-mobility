import contextlib
from src import Node
from src import Link
from src import Path
from src import Zone
from src import Bush
from src import Params
from src import PASList

import math
from gurobipy import Model, GRB, quicksum
import time
from gurobipy import Model, GRB
totalf_rs = 0
def readTravelTimes(travelTimesFile, network):
    travel_times = {}

    with open(travelTimesFile, "r") as file1:
        lines1 = file1.readlines()

    line1_idx = 0

    while line1_idx < len(lines1) and lines1[line1_idx].strip() == "":
        line1_idx += 1

    r1 = None
    idx1 = 0

    if line1_idx < len(lines1):
        splitted1 = lines1[line1_idx].split()

    while line1_idx < len(lines1) and idx1 < len(splitted1):

        next1 = splitted1[idx1]
        if next1 == "Origin":
            idx1 += 1
            if idx1 < len(splitted1):
                try:
                    origin_id = int(splitted1[idx1])
                    if origin_id > 0 and origin_id <= len(network.zones):
                        r1 = network.zones[origin_id - 1]
                    else:
                        print(f"Warning: Origin ID {origin_id} is out of range.")
                        r1 = None
                except ValueError:
                    print(f"Error parsing origin ID: {splitted1[idx1]}")
                    r1 = None
            else:
                r1 = None
        else:
            if r1 is not None:
                try:
                    destination_id = int(splitted1[idx1])
                    if destination_id > 0 and destination_id <= len(network.zones):
                        s1 = network.zones[destination_id - 1]
                    else:
                        print(f"Warning: Destination ID {destination_id} is out of range.")
                        s1 = None

                    idx1 += 2
                    if idx1 < len(splitted1):
                        next1 = splitted1[idx1]
                        traveltime = float(next1[:-1]) 
                        if s1 is not None:
                            travel_times[(r1, s1)] = traveltime 
                            #print(r1, s1, travel_times[(r1, s1)])
                    else:
                        s1 = None
                except ValueError:
                    print(f"Error parsing destination ID or travel time: {splitted1[idx1]} or {splitted1[idx1 + 1]}")
                    s1 = None

        idx1 += 1

        if idx1 >= len(splitted1):
            line1_idx += 1
            while line1_idx < len(lines1) and lines1[line1_idx].strip() == "":
                line1_idx += 1

            if line1_idx < len(lines1):
                line1 = lines1[line1_idx].strip()
                splitted1 = line1.split()
                idx1 = 0
    #print(travel_times)
    return travel_times


def setup_and_solve_optimization(network, mode, travel_times, demand_dict):
    construction_start_time = time.time()
    # Initialize the model
    m = Model("Transport_Optimization")
    # Decision Variables
    od_flows = {}  # Flow between origins and destinations
    non_zero_demand_od_pairs = []
    non_zero_demand_od_pairs_dict = {}

    for (origin, destination), demand in demand_dict.items():
       
        #if origin not in non_zero_demand_od_pairs_dict:
        #    non_zero_demand_od_pairs_dict[origin] = []
        od_flows[(origin.id, destination.id)] = m.addVar(lb=0, name=f"od_flow_{origin.id}_{destination.id}")
        #non_zero_demand_od_pairs.append((origin.id, destination.id))
        #non_zero_demand_od_pairs_dict[origin].append(destination)
        #print(f"Added variable for OD pair ({origin.id}, {destination.id}) with demand {demand}")
        #if travel_times[(origin, destination)] >= 15:
         #              od_flows[((origin.id, destination.id))] = demand

    '''
    # Create OD flow variables and populate dictionary for non-zero demands
    for origin in network.getZones():
        if origin not in non_zero_demand_od_pairs_dict:
            non_zero_demand_od_pairs_dict[origin] = []
        for destination in network.getZones():
            if origin != destination:
                demand = origin.demandf.get(destination, 0)
                if demand != 0:
                    od_flows[(origin.id, destination.id)] = m.addVar(lb=0, name=f"od_flow_{origin.id}_{destination.id}")
                    non_zero_demand_od_pairs.append((origin.id, destination.id))
                    non_zero_demand_od_pairs_dict[origin].append(destination)
                    if travel_times[(origin, destination)] >= 20:
                        od_flows[((origin.id, destination.id))] = demand
                        
'''
    # Auxiliary variable for the maximum expression
    max_var = m.addVar(name="max_var")
    # Update model to integrate new variables
    m.update()
    # Parameters
    alpha = 1.0  # Penalty factor
    N_v = 453970000 # Total number of vehicles, adjust as needed
    '''
    # Objective Function
    psi_expr = quicksum(
        od_flows[(origin.id, destination.id)] * network.getLambda(origin, destination) / 60
        
        for origin, destinations in non_zero_demand_od_pairs_dict.items()
        for destination in destinations) - N_v
    '''
            #print(travel_times[(origin, destination)], origin, destination)
    psi_expr = quicksum(
    od_flows[(origin.id, destination.id)] * travel_times[(origin, destination)] / 60
    for (origin, destination) in demand_dict.keys()) 

    # Max condition implemented via an auxiliary variable
    m.addConstr(max_var >= 0, "max_var_non_negative")
    m.addConstr(max_var >= psi_expr, "max_var_ge_psi_expr")

    # Minimize the scaled maximum of psi_expr and 0, scaled by alpha
    m.setObjective(alpha * max_var, GRB.MINIMIZE)

    # Flow constraints for demands
    for (origin, destination), demand in demand_dict.items():
        m.addConstr(od_flows[(origin.id, destination.id)] >= demand, f"Demand_{origin.id}_{destination.id}")
        #print(f"Added demand constraint for OD pair ({origin.id}, {destination.id}) with demand {demand}")

    for (origin, destination) in od_flows:
        m.addConstr(od_flows[(origin, destination)] >= 0, f"NonNegativity_{origin}_{destination}")

    incoming_demand = {node.id: 0 for node in network.getNodes()}
    outgoing_demand = {node.id: 0 for node in network.getNodes()}
    for (origin, destination), demand in demand_dict.items():
        outgoing_demand[origin.id] += demand
        incoming_demand[destination.id] += demand

    # Flow conservation constraints for each node
    for node in network.getNodes():
        od_inflow = quicksum(
            od_flows[(origin.id, node.id)] for origin in network.getZones()
            if origin != node and (origin.id, node.id) in od_flows)
        
        od_outflow = quicksum(
            od_flows[(node.id, destination.id)] for destination in network.getZones()
            if node != destination and (node.id, destination.id) in od_flows)

        #rhs_value = incoming_demand[node.id] - outgoing_demand[node.id]
        if outgoing_demand[node.id] > 0 and incoming_demand[node.id] == 0:
            pass
            
            #m.addConstr(od_outflow == outgoing_demand[node.id], f"FlowCons_Source_{node.id}")
        elif incoming_demand[node.id] > 0 and outgoing_demand[node.id] == 0:
            pass
            
            #m.addConstr(od_inflow == incoming_demand[node.id], f"FlowCons_Sink_{node.id}")
        else:
            
            m.addConstr(od_inflow - od_outflow == 0, f"FlowCons_{node.id}")
        #m.addConstr(od_inflow - od_outflow == 0, f"FlowCons_{node.id}")
    
    # Flow conservation constraints for each nod.
    '''
    for node in network.getNodes():
    
        od_inflow = quicksum(
            od_flows[(origin.id, node.id)] for origin in network.getZones()
            if origin != node and (origin.id, node.id) in od_flows)
        
        od_outflow = quicksum(
            od_flows[(node.id, destination.id)] for destination in network.getZones()
            if node != destination and (node.id, destination.id) in od_flows)

        #if od_inflow != 0 and od_outflow != 0:
        if node.id == 1:
            m.addConstr(od_inflow - od_outflow == -7.199836124407431, f"FlowCons_{node.id}")
        elif node.id == 32:
            m.addConstr(od_inflow - od_outflow == -10.774734344089707, f"FlowCons_{node.id}")
        else:
            m.addConstr(od_inflow - od_outflow == 0, f"FlowCons_{node.id}")
    '''
    total_vehicles_used = quicksum(
        od_flows[(origin.id, destination.id)] * travel_times[(origin, destination)] / 60
        for (origin, destination) in demand_dict.keys())
    m.addConstr(total_vehicles_used <= N_v, f"FleetSize_{mode}")

    construction_end_time = time.time()
    construction_duration = construction_end_time - construction_start_time
    print(f"Model construction time: {construction_duration:.2f} seconds")

    optimization_start_time = time.time()
    # Solve the model
    m.optimize()
    optimization_end_time = time.time()
    optimization_duration = optimization_end_time - optimization_start_time
    print(f"Model optimization time: {optimization_duration:.2f} seconds")

    if m.status == GRB.OPTIMAL:
        print("Optimal solution found:")
        optimal_psi_expr = 0
        total_od_flow = 0
        for (origin, destination) in demand_dict.keys():
            if type(od_flows[(origin.id, destination.id)]) == float:
                optimal_psi_expr += od_flows[((origin.id, destination.id))].x * travel_times[(origin, destination)] / 60
            else:
                optimal_psi_expr += (od_flows[(origin.id, destination.id)].x * travel_times[(origin, destination)]) / 60
            total_od_flow += (od_flows[(origin.id, destination.id)]).x
        print(f"Value of the first expression of the objective function: {optimal_psi_expr}")
        totalf_rs = total_od_flow
        # Write results to a text file
        write_frs_to_file(demand_dict)
        write_results_to_file(network, od_flows, optimal_psi_expr, demand_dict)
        
        return totalf_rs
    else:
        print("No optimal solution found")
        # Compute IIS
        print("Computing IIS...")
        m.computeIIS()
        m.write("model.ilp")
        print("IIS written to model.ilp")


def write_results_to_file(network, od_flows, total_od_flow, demand_dict):
    with open('trips_frs.txt', 'w') as file, contextlib.redirect_stdout(file):
        file.write("<NUMBER OF ZONES> {}\n".format(len(network.getZones())))
        file.write("<TOTAL OD FLOW> {:.1f}\n".format(total_od_flow))
        file.write("<END OF METADATA>\n\n")

        for origin in network.getZones():
            file.write("Origin \t{}\n".format(origin.id))
            line_count = 0
            for destination in network.getZones():
                if origin != destination and (origin, destination) in demand_dict:
                    #if type(od_flows[(origin.id, destination.id)]) == float:
                        #flow = od_flows[(origin.id, destination.id)]
                    #else:
                    
                    flow = od_flows[(origin.id, destination.id)].x
                    #print(f"Origin {origin.id}, Destination {destination.id}, Flow: {flow}")  
                else:
                    flow = 0
                file.write("    {} : {}; ".format(destination.id, flow))
                line_count += 1
                if line_count % 5 == 0:
                    file.write("\n")
            file.write("\n")

def write_frs_to_file(demand_dict):
    with open('demand_frs.txt', 'w') as file, contextlib.redirect_stdout(file):
        for (origin, destination), demand in demand_dict.items():
            file.write(f"Origin {origin.id} -> Destination {destination.id}: Demand {demand}\n")

'''
def calculate_total_demand(file_path):
    total_demand = 0.0
    with open(file_path, 'r') as file:
        lines = file.readlines()
        in_demand_section = False
        for line in lines:
            if line.strip() == "<END OF METADATA>":
                in_demand_section = True
                continue
            
            if in_demand_section:
                if line.startswith("Origin"):
                    continue
                parts = line.strip().split()
                for i in range(0, len(parts), 3):
                    demand = float(parts[i + 2].rstrip(';'))
                    total_demand += demand

    return total_demand

# Example usage
trips_file1 = 'data/SiouxFalls/asymmetric_trips.txt'
trips_file2 = 'results9.txt'
total_demand1 = calculate_total_demand(trips_file1)
total_demand2 = calculate_total_demand(trips_file2)
print(f"Total demand for asymmetric demand: {total_demand1}")
print(f"Total f_rs: {total_demand2}")
'''