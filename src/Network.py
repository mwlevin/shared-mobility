import contextlib
from src import Node
from src import Link
from src import Path
from src import Zone
from src import Bush
from src import Params
from src import PASList
import math
import time
from src import Heap

class Network:

    # construct this Network with the name; read files associated with network name
    def __init__(self,name,B_prop,m,scal_time,scal_flow,timelimit, f_rsFile,sharedElectricVehicleFile,PrivateVehicleFile, UberDemandFile):
        self.nodes = [] 
        self.links = []
        self.zones = []
        self.origins =[]
        self.zone_dict = {}
        self.iterations = []
        self.tstt_values = []
        self.sptt_values = []
        self.tfftt_values = []
        self.gap_values = []
        self.aec_values = []
        self.vmt_values = []
        self.links2 = {}
        self.type = 'UE'
        self.TD = 0
        self.TC = 0 # total cost
        self.params = Params.Params()
        
        self.allPAS = PASList.PASList()
        
        

        self.time_isFlowEffective = 0
        self.time_flowShift = 0
        self.time_wholePAS = 0
        self.time_loadDemand = 0
        self.time_tracePathSet = 0
        self.time_minPath = 0
        self.time_addFlow = 0
        self.time_checkPAS = 0
        self.time_hasRelevantPAS = 0
        self.time_removeCycles = 0
        self.time_removeCycleAtNode = 0
        self.time_createPAS = 0
        self.time_wholeBush = 0
        self.time_dijkstra = 0
        self.time_tapas = 0
        self.time_findPAS = 0
        self.time_equilibratePAS = 0
        self.time_removePAS = 0
        self.time_wholeNetwork = 0
        self.time_tapas = 0


        self.inf = 1e+9
        self.tol = 1e-2
        
        self.readNetwork("data/"+name+"/net.txt",m,scal_time,scal_flow,timelimit)
        self.readTrips(PrivateVehicleFile,f_rsFile,sharedElectricVehicleFile,UberDemandFile,"data/Minneapolis/trips.txt",m,scal_time,scal_flow,timelimit)
        
        self.B = self.TC * B_prop # budget
        
        
        print('Total scaled demand',self.TD)
        print('Total cost',self.TC,'Budget',self.B)
        
    def setType(self, type):
        self.type = type
        
    # read file "/net.txt"
    def readNetwork(self, netFile,m,scal_time,scal_flow,timelimit):

        
        firstThruNode = 1
        numZones = 0
        numNodes = 0
        numLinks = 0
        newLinks = 0
        #with open('result8.txt', 'a') as file, contextlib.redirect_stdout(file):
        file = open(netFile, "r")

        line = ""
        
        while line.strip() != "<END OF METADATA>":
            line = file.readline()
            if "<NUMBER OF ZONES>" in line:
            
                numZones = int(line[line.index('>') + 1:].strip());
            
            elif "<NUMBER OF NODES>" in line:
                numNodes = int(line[line.index('>') + 1:].strip())
            elif "<NUMBER OF LINKS>" in line:
                numLinks = int(line[line.index('>') + 1:].strip())
            elif "<NUMBER OF NEW LINKS>" in line:
                newLinks = int(line[line.index('>') + 1:].strip())
            elif "<FIRST THRU NODE>" in line:
                firstThruNode = int(line[line.index('>') + 1:].strip())

        for i in range(0, numZones):
            self.zones.append(Zone.Zone(i + 1))
            self.zone_dict[(i+1)] = Zone.Zone(i + 1)

        for i in range(0, numNodes):
            if i < numZones:
                self.nodes.append(self.zones[i])
                
                if i + 1 < firstThruNode:
                    self.zones[i].setThruNode(False)

            else:
                self.nodes.append(Node.Node(i + 1))

        line = ""
        idlink = 0
        while len(line) == 0:
            line = file.readline().strip()
        #with open('result6.txt', 'a') as file, contextlib.redirect_stdout(file):
        for i in range(0, numLinks + newLinks):
            line = file.readline().split()
            if len(line) == 0:
                continue
            start = self.nodes[int(line[0]) - 1]
            end = self.nodes[int(line[1]) - 1]
            C = float(line[2]) * scal_flow

            t_ff = float(line[4]) * scal_time
            alpha = float(line[5])
            beta = float(line[6])
            
            #cost = float(line[10])
            cost = 0
            
            self.TC += cost
            lenght = float(line[3])
            #with open('result5.txt', 'w') as file, contextlib.redirect_stdout(file):
            link = Link.Link(idlink, start ,end, t_ff, C, alpha, beta, cost, lenght)
            idlink = idlink +1
            #print(start,end)
            self.links.append(link)
            #print(self.links)
            
            if i > numLinks:
                self.links2[(start, end)] = link
            
            #with open('result6.txt', 'a') as file, contextlib.redirect_stdout(file):
            #print(f"Start Node: {start}, End Node: {end}")
            #print(link)
        file.close()

        #with open('result6.txt', 'a') as file, contextlib.redirect_stdout(file):
            #print(start,end)
            #print(self.links)


    def readTrips(self,tripsFile1,tripsFile2,tripsFile3,uberDemandFile,totalDemandFile,m,scal_time,scal_flow,timelimit):
        
        file1 = open(tripsFile1, "r")

        lines1 = file1.readlines()
        
        line1_idx = 0
        
        while lines1[line1_idx].strip() != "<END OF METADATA>":
            line1_idx += 1
            
        line1_idx += 1
        
        while lines1[line1_idx].strip() == "":
            line1_idx += 1
            
        r1 = None
        
        idx1 = 0
        
        splitted1 = lines1[line1_idx].split()

        
        while len(lines1) < line1_idx or idx1 < len(splitted1):

            next1 = splitted1[idx1]
            #print(next)
            if next1 == "Origin":
                
                idx1 += 1
                r1 = self.zones[int(splitted1[idx1]) - 1]

            else:
                
                s1 = self.zones[int(splitted1[idx1]) - 1]
                idx1 += 2
                next1 = splitted1[idx1]
                d1 = float(next1[0:len(next1) - 1]) * scal_flow 
                
                r1.addDemand(s1, d1)
                r1.addDemandw(s1, d1)
                r1.addTotalDemand(s1, d1)
                self.TD += d1

            idx1 += 1

            if idx1 >= len(splitted1):
                line1_idx += 1
                while line1_idx < len(lines1) and lines1[line1_idx].strip() == "":
                    line1_idx += 1
                    
                if line1_idx < len(lines1):
                    line1 = lines1[line1_idx].strip()
                    splitted1 = line1.split()
                    idx1 = 0
            
        file1.close()
        for r in self.zones:
            if r.getProductions() > self.params.flow_epsilon:
                self.origins.append(r)
        ####################################################################
        file2 = open(tripsFile2, "r")

        lines2 = file2.readlines()
        
        
        line2_idx = 0
        
        
        while lines2[line2_idx].strip() != "<END OF METADATA>":
            line2_idx += 1
            
        line2_idx += 1
        
        while lines2[line2_idx].strip() == "":
            line2_idx += 1
            
        r2 = None
        
        idx2 = 0
        
        splitted2 = lines2[line2_idx].split()
        #print(splitted)
        
        while len(lines2) < line2_idx or idx2 < len(splitted2):
            #print(line_idx)
            #print(idx)
            #print(len(lines))This is the total number of line
            #print()
        #while lines < len(line_idx) or idx < len(splitted):

            next2 = splitted2[idx2]
            #print(next)
            if next2 == "Origin":
                
                idx2 += 1
                r2 = self.zones[int(splitted2[idx2]) - 1]

            else:
             
                s2 = self.zones[int(splitted2[idx2]) - 1]

                #print(s)
                idx2 += 2
                next2 = splitted2[idx2]
                d2 = float(next2[0:len(next2) - 1]) * scal_flow 
                
                r2.addDemand(s2, d2)
                r2.addDemandf(s2, d2)
                r2.addTotalDemand(s2, d2)
                self.TD += d2

            idx2 += 1

            if idx2 >= len(splitted2):
                line2_idx += 1
                while line2_idx < len(lines2) and lines2[line2_idx].strip() == "":
                    line2_idx += 1
                    
                if line2_idx < len(lines2):
                    line2 = lines2[line2_idx].strip()
                    splitted2 = line2.split()
                    idx2 = 0
            
        file2.close()
#####################################################
        file3 = open(tripsFile3, "r")
        

        lines3 = file3.readlines()
        
        
        line3_idx = 0
        
        
        while lines3[line3_idx].strip() != "<END OF METADATA>":
            line3_idx += 1
            
        line3_idx += 1
        
        while lines3[line3_idx].strip() == "":
            line3_idx += 1
            
        r3 = None
        
        idx3 = 0
        
        splitted3 = lines3[line3_idx].split()

        
        while len(lines3) < line3_idx or idx3 < len(splitted3):

            next3 = splitted3[idx3]
            #print(next)
            if next3 == "Origin":
                
                idx3 += 1
                r3 = self.zones[int(splitted3[idx3]) - 1]

            else:
                
                s3 = self.zones[int(splitted3[idx3]) - 1]
                idx3 += 2
                next3 = splitted3[idx3]
                d3 = float(next3[0:len(next3) - 1]) * scal_flow 
                
                r3.addDemand(s3, d3)
                r3.addDemandw(s3, d3)
                r3.addTotalDemand(s3, d3)
                self.TD += d3

            idx3 += 1

            if idx3 >= len(splitted3):
                line3_idx += 1
                while line3_idx < len(lines3) and lines3[line3_idx].strip() == "":
                    line3_idx += 1
                    
                if line3_idx < len(lines3):
                    line3 = lines3[line3_idx].strip()
                    splitted3 = line3.split()
                    idx3 = 0
            
        file3.close()
        ##################################################
        file4 = open(uberDemandFile, "r")
        

        lines4 = file4.readlines()
        
        
        line4_idx = 0
        
        
        while lines4[line4_idx].strip() != "<END OF METADATA>":
            line4_idx += 1
            
        line4_idx += 1
        
        while lines4[line4_idx].strip() == "":
            line4_idx += 1
            
        r4 = None
        
        idx4 = 0
        
        splitted4 = lines4[line4_idx].split()

        
        while len(lines4) < line4_idx or idx4 < len(splitted4):

            next4 = splitted4[idx4]
            #print(next)
            if next4 == "Origin":
                
                idx4 += 1
                r4 = self.zones[int(splitted4[idx4]) - 1]

            else:
                
                s4 = self.zones[int(splitted4[idx4]) - 1]
                idx4 += 2
                next4 = splitted4[idx4]
                d4 = float(next4[0:len(next4) - 1]) * scal_flow 
                
                r4.addDemandUber(s4, d4)
                #r4.addTotalDemand(s4, d4)
                #r3.getDemandUber()
                #r3.addDemandw(s3, d3)
                #r3.addTotalDemand(s3, d3)
                #self.TD += d3

            idx4 += 1

            if idx4 >= len(splitted4):
                line4_idx += 1
                while line4_idx < len(lines4) and lines4[line4_idx].strip() == "":
                    line4_idx += 1
                    
                if line4_idx < len(lines4):
                    line4 = lines4[line4_idx].strip()
                    splitted4 = line4.split()
                    idx4 = 0
            
        file4.close()
        ######################################
        file5 = open(totalDemandFile, "r")

        lines5 = file5.readlines()
        
        line5_idx = 0
        
        while lines5[line5_idx].strip() != "<END OF METADATA>":
            line5_idx += 1
            
        line5_idx += 1
        
        while lines5[line5_idx].strip() == "":
            line5_idx += 1
            
        r5 = None
        
        idx5 = 0
        
        splitted5 = lines5[line5_idx].split()

        
        while len(lines5) < line5_idx or idx5 < len(splitted5):

            next5 = splitted5[idx5]
            #print(next)
            if next5 == "Origin":
                
                idx5 += 1
                r5 = self.zones[int(splitted5[idx5]) - 1]

            else:
                
                s5 = self.zones[int(splitted5[idx5]) - 1]
                idx5 += 2
                next5 = splitted5[idx5]
                d5 = float(next5[0:len(next5) - 1]) * scal_flow 
                
                r5.addDemandBeforeModeChoice(s5, d5)
                #r1.addDemandw(s1, d1)
                #r1.addTotalDemand(s1, d1)
                self.TD += d5

            idx5 += 1

            if idx5 >= len(splitted5):
                line5_idx += 1
                while line5_idx < len(lines5) and lines5[line5_idx].strip() == "":
                    line5_idx += 1
                    
                if line5_idx < len(lines5):
                    line5 = lines5[line5_idx].strip()
                    splitted5 = line5.split()
                    idx5 = 0
            
        file5.close()

    def create_demand_dict(self):
        demand_dict = {}
        
        for origin in self.getZones():
            for destination in self.getZones():
                if origin != destination:
                    demand = origin.getDemandUber(destination)
                    #if demand != 0:
                    demand_dict[(origin, destination)] = demand
        return demand_dict





    def getLinks(self):
        return self.links
    
    def getNodes(self):
        return self.nodes
    
    def getZones(self):
        return self.zones

    def getZoneById(self, id):
        return self.zone_dict.get(id, None)

    # **********
    # Exercise 5(e)
    # ********** 
    # find the node with the given id
    def findNode(self, id):
        if id <= 0 or id > len(self.nodes):
            return None
        return self.nodes[id - 1]

    # find the link with the given start and end nodes
    def findLink(self, i, j):
        if i is None or j is None:
            return None

        for link in i.getOutgoing():
            if link.getEnd() == j:
                return link

        return None

    # find the node with the smallest cost (node.cost)
    def argmin1(self, set):
        best = None
        min = float("inf")

        for n in set:
            if n.cost < min:
                min = n.cost
                best = n

        return best

    #def argmin(self, set):
        # Sort the set based on the cost of the nodes
        #sorted_nodes = sorted(set, key=lambda x: x.cost)
        
        # Return a copy of the last node in the sortted list (which has the minimum cost)
        #return sorted_nodes[-1]

    # change
    def argmin(self, set):
        cost, node = min((n.cost, n) for n in set)
        return node



    def dijkstras(self, origin, networktype):
        #with open('result69.txt', 'a') as file, contextlib.redirect_stdout(file):
        
            for n in self.nodes:
                n.cost = 1E9
                n.pred = None

            origin.cost = 0.0

            Q = Heap.Heap()
            Q.insert(origin)
            #print(f"This is Q {Q}")

            while Q.size() > 0:

                #u = self.argmin(Q)
                u = Q.removeMin()

                for uv in u.outgoing:
                    v = uv.end
                    tt = uv.getTravelTime(uv.x, self.type)

                    if u.cost + tt < v.cost:
                        v.cost = u.cost + tt
                        v.pred = uv

                        if v.isThruNode():
                            Q.insert(v)
    def trace(self, r, s):
        curr = s
        #print(f"s is {s}")

        output = Path.Path()
        
        while curr != r and curr is not None:
            ij = curr.pred
            #print(ij)

            if ij is not None:
                output.addFront(ij)
                curr = curr.pred.start
        #print(output)
        return output
        
    def traceTree(self, tree, r, s):
        #with open('trace8.txt', 'a') as file, contextlib.redirect_stdout(file):
            curr = s
            #print(s)

            output = []
            #with open('trace4.txt', 'a') as file, contextlib.redirect_stdout(file):
            while curr != r and curr is not None:
                ij = tree[curr]
                #print(ij)

                if ij is not None:
                    output.append(ij)
                    #print(output)
                    curr = ij.start
            
            return output

    def getSPTree(self, r):
        
        start_time2 = time.time()
        self.dijkstras(r, self.type)
        end_time2 = time.time()
        #print(f"Time taken for dijkstra: {end_time2 - start_time2} seconds")
        self.time_dijkstra += (end_time2 - start_time2)

        output = {}
        
        for n in self.nodes:
            if n != r and n.cost < self.params.INFTY:
                output[n] = n.pred
                

        
        return output
    
    # returns the total system travel time
    def getTSTT(self):
        output = 0.0
        for ij in self.links:
            tt = ij.getTravelTime(ij.x, self.type)
            output += ij.x * tt
            #print(ij.x)
            #print(str(link)+ "\t" + ij, 'flow'+ "\t" +ij.x,'travel time'+ "\t" +tt, 'free flow travel time'+ "\t" +ij.t_ff, 'alpha'+ "\t" +ij.alpha, 'beta'+ "\t" +ij.beta, ij.C)
            #print('link: {}\tflow: {}\ttravel time: {}\tfree flow travel time: {}\talpha: {}\tbeta: {}\tC: {}'.format(str(ij), ij.x, tt, ij.t_ff, ij.alpha, ij.beta, ij.C))

        return output
    
    def getVMT(self):
        output = 0.0
        for ij in self.links:
            output += (ij.x * ij.lenght)
            
        return output

    # returns the total system travel time if all demand is on the shortest path
    def getSPTT(self):
        output = 0.0

        for r in self.zones:
            if r.getProductions() > 0:
                start_time3 = time.time()
                self.dijkstras(r, self.type)
                end_time3 = time.time()
                self.time_dijkstra += (end_time3 - start_time3)
                
                for s in self.zones:
                    if r.getDemand(s) > 0:
                        output += r.getDemand(s) * s.cost

        return output

    # returns the total number of trips in the network
    def getTotalTrips(self):
        output = 0.0

        for r in self.zones:
            output += r.getProductions()

        return output

    # returns the average excess cost
    def getAEC(self):
        return (self.getTSTT() - self.getSPTT()) / self.getTotalTrips()


    # find the step size for the given iteration number
    def calculateStepsize(self, iteration):
        return 1.0 / iteration
        #print(1.0 / iteration)


    # calculate the new X for all links based on the given step size
    def calculateNewX(self, stepsize):
        for ij in self.links:
            ij.calculateNewX(stepsize)


    # calculate the all-or-nothing assignment
    def calculateAON(self):
        for r in self.zones:
            if r.getProductions() > 0:
                start_time4 = time.time()
                self.dijkstras(r, self.type)
                end_time4 = time.time()
                self.time_dijkstra += (end_time4 - start_time4)
                
                for s in self.zones:
                    if r.getDemand(s) > 0:
                        pi_star = self.trace(r, s)
                        pi_star.addHstar(r.getDemand(s))

    def getLambda2(self, origin):
        self.dijkstras(origin, self.type)
        travel_times = {}
        
        for destination in self.zones:
            #if origin.getDemand(destination) > 0:
                #shortest_path = self.trace(origin, destination)
                travel_times[destination] = destination.cost #shortest_path.getTravelTime()
            #else:
                #travel_times[destination] = 0
                
        return travel_times
    
    def getFreeFlowTravelTime(self, origin):
        self.dijkstras(origin, self.type)
        freeFlowTravelTimes = {}

        for destination in self.zones:
            shortest_path = self.trace(origin, destination)
            freeFlowTravelTimes[destination] = shortest_path.getFreeFlowTravelTime()
        return freeFlowTravelTimes
    
    def getTotalFreeFlowTravelTime(self):
        output = 0.0
        for ij in self.links:
            tt = ij.t_ff
            output += ij.x * tt
            #print(ij.x)
            #print(str(link)+ "\t" + ij, 'flow'+ "\t" +ij.x,'travel time'+ "\t" +tt, 'free flow travel time'+ "\t" +ij.t_ff, 'alpha'+ "\t" +ij.alpha, 'beta'+ "\t" +ij.beta, ij.C)
            #print('link: {}\tflow: {}\ttravel time: {}\tfree flow travel time: {}\talpha: {}\tbeta: {}\tC: {}'.format(str(ij), ij.x, tt, ij.t_ff, ij.alpha, ij.beta, ij.C))

        return output


    def write_free_flow_travel_times_to_file(self):
        with open('free_flow_travel_times.txt', 'w') as file, contextlib.redirect_stdout(file):
            for origin in self.getZones():
                file.write(f"Origin \t{origin.id}\n")
                line_count = 0
                travel_times = self.getFreeFlowTravelTime(origin)  # Precompute travel times for the origin

                for destination in self.getZones():
                    travel_time = travel_times[destination]  # Retrieve the precomputed travel time
                    file.write(f"    {destination.id} : {travel_time}; ")
                    line_count += 1
                    if line_count % 5 == 0:
                        file.write("\n")
                file.write("\n")

    def write_travel_times_to_file(self):
        with open('travel_times.txt', 'w') as file, contextlib.redirect_stdout(file):
            for origin in self.getZones():
                file.write(f"Origin \t{origin.id}\n")
                line_count = 0
                travel_times = self.getLambda2(origin)  # Precompute travel times for the origin

                for destination in self.getZones():
                    travel_time = travel_times[destination]  # Retrieve the precomputed travel time
                    file.write(f"    {destination.id} : {travel_time}; ")
                    line_count += 1
                    if line_count % 5 == 0:
                        file.write("\n")
                file.write("\n")







    def msa(self, type, lbd, y, xinit):

        self.setType(type)
        max_iteration = 1000
        
        for ij in self.links:
            i = ij.start
            j = ij.end
            if (i,j) in y:            
                ij.setlbdCost(lbd[(i,j)]*y[(i,j)] + self.inf*(1 - y[(i,j)]))
        
        
        output = "Iteration\tAEC\n"
        
        
        

        for iteration in range(1, max_iteration + 1):
            self.calculateAON()
            stepsize = self.calculateStepsize(iteration)
            
            self.calculateNewX(stepsize)
            
            output += str(iteration) + "\t" + str(self.getAEC()) + "\n"
        
        return self.getLx(lbd, y), self.getXDict(), self.getTSTT()

    def getLx(self, lbd, y):
        Lx = 0
        for ij in self.links:
            Lx += ij.x * ij.getTravelTime(ij.x, 'TT')
            i = ij.start
            j = ij.end
            if (i,j) in y:
                Lx += lbd[(i,j)]*ij.x
            
        return Lx
            
    #def getXDict(self):
    #    output = {}
    #    for ij in self.links:
    #        print(self.links)
    #        output[(ij.start, ij.end)] = ij.x
    #        print(ij.x)
    #    return output


    #start_time4 = time.time()    
    def findPAS(self, ij, bush):
        
        if not self.allPAS.containsKey(ij):
            return None
        
        best = None
        max = self.params.bush_gap
        
        if ij in self.allPAS.forward:
            for p in self.allPAS.forward[ij]:
                temp = p.maxBackwardBushFlowShift(bush)

                if temp > max and p.isCostEffective(ij, self.params.pas_cost_mu):
                    max = temp
                    best = p
                
        if ij in self.allPAS.backward:
            for p in self.allPAS.backward[ij]:
                temp = p.maxForwardBushFlowShift(bush)

                if temp > max and p.isCostEffectiveForLink(ij, self.type, self.params.pas_cost_mu):
                    max = temp
                    best = p
        
        return best
        
    #end_time4 = time.time()
    #print(f"Time taken for findPAS: {end_time4 - start_time4} seconds")
    
    #start_time5 = time.time()
    def equilibratePAS(self, iter):
        output = False
        
        for a in self.allPAS.forward:
            for p in self.allPAS.forward[a]:
                if p.flowShift(self.type, self.params):
                    output = True
                    p.lastIterFlowShift = iter

        return output        
    
    def removeAPAS(self, p):
        self.allPAS.remove(p)
            
        for r in p.relevant:
            r.bush.relevantPAS.remove(p)
    
    def removePAS(self, iter):
        removed = []
        
        for a in self.allPAS.forward:
            for p in self.allPAS.forward[a]:
                if p.lastIterFlowShift < iter-2:
                    removed.append(p)
        
        for p in removed:
            self.removeAPAS(p)

       
    def saveTravelTimesToFile(self):
            # Write header to the file
        with open('LinkTravelTime.txt', 'w') as file, contextlib.redirect_stdout(file):
            file.write("Start_Node\tEnd_Node\tTravel_Time\n")
            
            for ij in self.links:
                # Assuming each link has attributes `start`, `end`, and a `getTravelTime` method
                start_node = ij.start
                end_node = ij.end
                travel_time = ij.getTravelTime(ij.x, self.type)
                
                # Write the link data to the file
                file.write(f"{start_node}\t{end_node}\t{travel_time:.6f}\n")




    def validateLinkFlows(self):
        output = True
        for ij in self.links:
            totbushflow = 0
            
            for r in self.origins:
                totbushflow += r.bush.getFlow(ij)
            
            if abs(ij.x - totbushflow) > self.params.flow_epsilon:
                #print(ij, ij.x, totbushflow, ij.x-totbushflow, ij.getTravelTime(ij.x, self.type))
                output = False
        return output


    #start_time3 = time.time() 
    def tapas(self, type, lbd, y, xinit):
        self.setType(type)
        
        max_iter = self.params.tapas_max_iter
        min_gap = self.params.min_gap
        
        #self.params.line_search_gap = pow(10, math.floor(math.log10(self.TD) - 6))
        
        
        last_iter_gap = 1
        
        #for r in self.zones:
        #    r.bush = Bush.Bush(self, r)
        for r in self.origins:
            if r.bush == None:
                r.bush = Bush.Bush(self, r)
    
        for iter in range(1, max_iter+1):
                        
            self.params.good_pas_flow_mu = 0
            self.params.good_pas_cost_mu = 0
            self.params.good_bush_gap = 0
            self.params.good_pas_cost_epsilon = 0

            if self.params.PRINT_TAP_ITER:
                print("Iteration\tTSTT\tSPTT\tgap\tAEC")
            # for every origin
            for r in self.origins:
                if self.params.PRINT_TAPAS_INFO:
                    print("removing cycles", r)
                
                
                r.bush.removeCycles()
                
                # find tree of least cost routes
                if self.params.PRINT_TAPAS_INFO:
                    print("checking for PAS", r)
                
                r.bush.checkPAS()
                if self.params.PRINT_PAS_INFO:
                    print("num PAS", r, r.bush.relevantPAS.size())
                
                # for every link used by the origin which is not part of the tree
                    # if there is an existing effective PAS
                        # make sure the origin is listed as relevant
                    # else
                        # construct a new PAS    
                                    
                # choose a random subset of active PASs
                # shift flow within each chosen PAS
                                
                r.bush.branchShifts()

                         
                printed = False                              
                for a in r.bush.relevantPAS.forward:
                    for p in r.bush.relevantPAS.forward[a]:
                        if self.params.PRINT_TAPAS_INFO and not printed:
                            print("initial flow shifts", r)
                            printed = True
                        p.flowShift(self.type, self.params)

            if self.params.PRINT_TAPAS_INFO:
                print("general flow shifts")

            modified = False
            for shiftIter in range(0, self.params.tapas_equilibrate_iter):
                # check if it should be eliminated
                self.removePAS(shiftIter)
                # perform flow shift to equilibrate costs
                modified = self.equilibratePAS(shiftIter)
                
                # redistribute flows between origins by the proportionality condition
                            
                # in the case that no flow shifting occurred, do not try to equilibrate more
                if not modified:
                    break


                
                

            tfftt = self.getTotalFreeFlowTravelTime()
            tstt = self.getTSTT()
            sptt = self.getSPTT()
            gap = (tstt - sptt)/tstt
            aec = (tstt - sptt)/self.TD
            VMT = self.getVMT()
            self.saveTravelTimesToFile()

            #self.tstt_values.append(tstt)
            #self.sptt_values.append(sptt)
            #self.gap_values.append(gap)
            #self.aec_values.append(aec)
            #self.iterations.append(iter)
            #self.tfftt_values.append(tfftt)
            if self.params.PRINT_TAP_ITER:
                print(str(iter)+"\t"+str(tstt)+"\t"+str(sptt)+"\t"+str(gap)+"\t"+str(aec)+"\t"+str(tfftt))
                
                #printLinkFlows();
            
                
            if gap < min_gap:
                break
                
            
        # there's an issue where PAS are labeled as not cost effective because the difference in cost is small, less than 5% of the reduced cost
        # for low network gaps, this is causing PAS to not flow shift
        # when the gap is low, increase the flow shift sensitivity
        '''
        if (last_iter_gap - gap) / gap < 0.01:
                self.params.pas_cost_mu = max(self.params.pas_cost_mu/10, 1e-9)
                self.params.line_search_gap = max(self.params.line_search_gap/10, 1e-9)
                
                if self.params.PRINT_TAPAS_INFO:
                    print("Adjusting parameters due to small gap "+str(self.params.pas_cost_mu)+" "+str(self.params.line_search_gap))
                    
        '''
        if (last_iter_gap - gap) < min_gap:
                
                
                self.params.line_search_gap = max(self.params.line_search_gap/10, self.params.min_line_search_gap)
                
                #if self.params.good_pas_cost_mu <= 10 and self.params.pas_cost_mu > 5e-5:
                self.params.pas_cost_mu = max(self.params.pas_cost_mu/10, 1e-6)   
                    
                #elif self.params.good_pas_flow_mu <= 10 and self.params.pas_flow_mu > 5e-5:
                self.params.pas_flow_mu = max(self.params.pas_flow_mu/10, 1e-6) 
                   
                #elif self.params.good_pas_cost_epsilon <= 10 and self.params.pas_cost_epsilon > 5e-6:
                self.params.pas_cost_epsilon = max(self.params.pas_cost_epsilon/10, 1e-6) 
                    
                #elif self.params.bush_gap > 5e-6:
                self.params.bush_gap = max(self.params.bush_gap/10, 1e-6)


                if self.params.PRINT_PARAM_ADJ:
                    print('TAPAS gap check', self.params.bush_gap, self.params.pas_cost_mu, self.params.pas_flow_mu, self.params.pas_cost_epsilon)
                    print("\t", self.params.good_bush_gap, self.params.good_pas_cost_mu, self.params.good_pas_flow_mu, self.params.good_pas_cost_epsilon)
                
        last_iter_gap = gap
        iter+= 1

        for a in self.links:
            a.x = round(a.x,self.params.rd)
            #

        self.tstt_values.append(tstt)
        self.sptt_values.append(sptt)
        self.gap_values.append(gap)
        self.aec_values.append(aec)
        self.iterations.append(iter)
        self.tfftt_values.append(tfftt)
        #self.tfftt_values.append(tfftt)
        self.vmt_values.append(VMT)
        
        
        #self.getTSTTlinks()
        #self.getTTlinks()
        #self.getVMTlinks()
        #self.getVMTdemand()
        #self.getVMTlength()

                

        #for zone in self.getZones():
            #print(f"Zone {zone.id} demands:")
            #zone.displayDemands()
            #print("\n")
   
            
    




