

class Path:
    # construct this Path; it contains a list of links representing the links in this path
    def __init__(self):
        self.links = []
        self.type = 'UE'
        
    def add(self, ij):
        self.links.append(ij)
        #print(ij)
    
    def addFront(self, ij):
        self.links.insert(0, ij)
        #print(ij)
        
    def size(self):
        return len(self.links)
        
    def __str__(self):
        return str(self.links)
    
    # **********
    # Exercise 6(a)
    # **********   
    # returns the travel time of this path
    def getTravelTime(self):
        output = 0
        for ij in self.links:
            output += ij.getTravelTime(ij.x, self.type)
        return output
    
    def getFreeFlowTravelTime(self):
        output = 0
        for ij in self.links:
            output += ij.t_ff
        return output
        
    # returns True if this path represents a connected list of links, or False otherwise
    def isConnected(self):
        for x in range(1, len(self.links)):
            if self.links[x].getStart() != self.links[x - 1].getEnd():
                return False
        return True
    
    # returns the origin node of this path
    def getSource(self):
        return self.links[0].getStart()
    
    # returns the destination node of this path
    def getDest(self):
        return self.links[-1].getEnd()
        
    # **********
    # Exercise 8(a)
    # **********  
    def addHstar(self, h):
        for ij in self.links:
            ij.addXstar(h)

