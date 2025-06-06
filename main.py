# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 18:46:55 2024

@author: david
"""
import time
import contextlib
#from memory_profiler import memory_usage
import numpy as np
import matplotlib.pyplot as plt
#---modules
from src import Network
from src import Params 
from src import PAS
import ModeChoice
pas_instance = PAS.PAS()
#net = 'SF'
#ins = 'DNDP_10_1'
#data = inout.read_instance(net,ins,0.5,500,1e-0,1e-3,600)
start_time = time.time()
pas = PAS.PAS()
network = Network.Network("SiouxFalls",0.5,500,1e-0,1e-0,600,"data/SiouxFalls/asymmetric_trips.txt")
#network = Network.Network("grid3",1,1,1,1,1)



#mode_choice_solver = ModeChoice.ModeChoice(network)
#mode_choice_solver.solve_mode_choice()




y1 = {(i,j):1 for (i,j) in network.links2}
l0 = {(i,j):0 for (i,j) in network.links2}

#---initialize link flows in the network (0 is default)
x0 = {(i,j):0 for (i,j) in network.links2}

#---arbitrary (nonzero) lambda
lbd = {(i,j):1 for (i,j) in network.links2}

start_time5 = time.time()




network.tapas('UE', l0, y1, x0)


                
end_time5 = time.time()
network.time_tapas += (end_time5-start_time5)
'''
for node in network.getNodes():
    print(f"node.id {node.id}, node.pred {node.pred}")
    print(f"node.id {node.id}, node.pred2 {node.pred2}")
'''
end_time = time.time()
print(f"Runtime of the whole code: {end_time - start_time} seconds")

print(f"Time taken for dijkstra: {network.time_dijkstra} seconds, percentage of the total run time {network.time_dijkstra * 100/(end_time-start_time)}")
print(f"Time taken for tapas: {network.time_tapas} seconds, percentage of the total run time {network.time_tapas * 100/(end_time-start_time)}")
print(f"Time taken for findPAS: {network.time_findPAS} seconds, percentage of the total run time {network.time_findPAS * 100/(end_time-start_time)}")
print(f"Time taken for loadDemand: {network.time_loadDemand} seconds, percentage of the total run time {network.time_loadDemand * 100/(end_time-start_time)}")
print(f"Time taken for addFlow: {network.time_addFlow + pas.time_addFlowPAS} seconds, percentage of the total run time {(network.time_addFlow + pas.time_addFlowPAS) * 100/(end_time-start_time)}")
print(f"Time taken for createPAS: {network.time_createPAS} seconds, percentage of the total run time {network.time_createPAS * 100/(end_time-start_time)}")
print(f"Time taken for checkPAS: {network.time_checkPAS} seconds, percentage of the total run time {network.time_checkPAS * 100/(end_time-start_time)}")
print(f"Time taken for equilibratePAS: {network.time_equilibratePAS} seconds, percentage of the total run time {network.time_equilibratePAS * 100/(end_time-start_time)}")
print(f"Time taken for removeCycles: {network.time_removeCycles} seconds, percentage of the total run time {network.time_removeCycles* 100/(end_time-start_time)}")
print(f"Time taken for Pas flowshift: {network.time_flowShift} seconds, percentage of the total run time {network.time_flowShift* 100/(end_time-start_time)}")


#mem_usage = memory_usage(network.tapas('UE', l0, y1, x0))
#print(f"Memory usage: {max(mem_usage) - min(mem_usage)} MiB")

#---solve UE with lambda=0 
#Lx, x, tstt = network.msa('UE',l0,y1,x0)
#Lx, x, tstt = test_optim.TAP(data,G,'UE','MSA',l0,y1,x0)
#print('Lx: %.1f' % Lx)
#print('tstt: %.1f' % tstt)

#---solve SO with lambda=lbd
#Lx, x, tstt = network.msa('SO',lbd,y1,x0)
#Lx, x, tstt = test_optim.TAP(data,G,'SO','MSA',lbd,y1,x0)
#print('Lx: %.1f' % Lx)
#print('tstt: %.1f' % tstt)