from src import Node


class Zone(Node.Node):


    def __init__(self, id):
        super().__init__(id)
        self.demand = {}
        self.demandf = {}
        self.demandw = {}
        self.demandBeforeModeChoice = {}
        self.totalDemand = {}
        self.demandUber = {}
        self.totaldemand = 0
        self.thruNode = True
        self.bush = None
        self.heap_idx = -1

    # adds the specified demand to an internal data structure for the demand from this node to the destination
    def addDemand(self, dest, dem):
        if dest in self.demand.keys():
            self.demand[dest] = self.demand[dest] + dem 
        else:
            self.demand[dest] = dem
            
        self.totaldemand += dem

    def addDemandBeforeModeChoice(self, dest, dem):
        if dest in self.demandBeforeModeChoice.keys():
            self.demandBeforeModeChoice[dest] = self.demandBeforeModeChoice[dest] + dem
        else:
            self.demandBeforeModeChoice[dest] = dem
        


    # This is the f_rs of Uber/Lyft
    def addDemandf(self, dest, dem):
        if dest in self.demandf.keys():
            self.demandf[dest] = self.demandf[dest] + dem 
        else:
            self.demandf[dest] = dem
            
    # This should be the demand wwithout Uber/Lyft
    def addDemandw(self, dest, dem):
        if dest in self.demandw.keys():
            self.demandw[dest] = self.demandw[dest] + dem 
        else:
            self.demandw[dest] = dem


    #This is the total demand for each origin
    def addTotalDemand(self, dest, dem):
        if dest in self.totalDemand.keys():
            self.totalDemand[dest] = self.totalDemand[dest] + dem
        else:
            self.totalDemand[dest] = dem

    def addDemandUber(self, dest, dem):
        if dest in self.demandUber.keys():
            self.demandUber[dest] = self.demandUber[dest] + dem
        else:
            self.demandUber[dest] = dem

    def getDemandUber(self,dest):
        if dest in self.demandUber.keys():
            return self.demandUber[dest]
        else:
            return 0 
        
    def getDemandBeforeModeChoice(self, dest):
        if dest in self.demandBeforeModeChoice.keys():
            return self.demandBeforeModeChoice[dest]
        else:
            return 0 

    def getTotalDemand(self, dest):
        if dest in self.totalDemand.keys():
            return self.totalDemand[dest]
        else:
            return 0

        #return self.totaldemand
        
    # returns the number of trips from this node to the destination
    def getDemand(self, dest):
        if dest in self.demand.keys():
            return self.demand[dest]
        else:
            return 0
    

    def getDemandf(self,dest):
        if dest in self.demandf.keys():
            
            return self.demandf[dest]
        else:
            return 0
        
    def getDemandw(self,dest):
        if dest in self.demandw.keys():
            return self.demandw[dest]
        else:
            return 0

    # returns the total number of outgoing trips from this node
    def getProductions(self):
    
        total = 0.0
        
        for s in self.demand.keys():
            total += self.demand[s]
        
        return total

    # returns aboolean indicating whether this node is a thru node
    def isThruNode(self):
        return self.thruNode
    
    # set a boolean indicating whether this node is a thru node
    def setThruNode(self, thru):
        self.thruNode = thru

    def displayDemands(self):
        for dest, demand in self.demand.items():
            print(f"Destination: {dest.id}, Demand: {demand}")