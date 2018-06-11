'''
Created on 2017年6月29日

@author: Vic
'''

import copy

class Grid():
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
    
    def get_info(self):
        info = "x: " + str(self.x) + "\ty: " + str(self.y) + "\tv: " + str(self.value) + "\t"
        return info

class Glist():
    
    def __init__(self):
        self.glist = []
        self.xmap = {}
        self.xlist = []
        self.ymap = {}
        self.ylist = []
    
    def add(self, g):
        self.glist.append(g)
        if g.x not in self.xmap:
            self.xmap[g.x] = None
            self.xlist.append(g.x)
        if g.y not in self.ymap:
            self.ymap[g.y] = None
            self.ylist.append(g.y)
        
    def get_new_glist(self, x, y):
        new_glist = Glist()
        for g in self.glist:
            if g.x != x and g.y != y:
                new_glist.add(g)
        return new_glist
    
    def print_all(self):
        for x in self.xlist:
            line = ""
            for y in self.ylist:
                for i in self.glist:
                    if i.x == x and i.y == y:
                        line = line + i.get_info() + "|"
                        break
            print(line)
            
gl1 = Glist()
g = Grid(1, 1, 6)
gl1.add(g)
g = Grid(1, 2, 6)
gl1.add(g)
g = Grid(1, 3, 6)
gl1.add(g)
g = Grid(1, 4, 6)
gl1.add(g)
g = Grid(2, 1, 6)
gl1.add(g)
g = Grid(2, 2, 92)
gl1.add(g)
g = Grid(2, 3, 46)
gl1.add(g)
g = Grid(2, 4, 30)
gl1.add(g)
g = Grid(3, 1, 60)
gl1.add(g)
g = Grid(3, 2, 23)
gl1.add(g)
g = Grid(3, 3, 46)
gl1.add(g)
g = Grid(3, 4, 23)
gl1.add(g)
g = Grid(4, 1, 61)
gl1.add(g)
g = Grid(4, 2, 13)
gl1.add(g)
g = Grid(4, 3, 27)
gl1.add(g)
g = Grid(4, 4, 85)
gl1.add(g)

gl1.print_all()

gl2 = gl1.get_new_glist(1, 2)
print()
#gl2.print_all()

def get_max(gl,gl_ysize,chose,chose_group):
    for x in gl.xlist:
        for y in gl.ylist:
            for i in gl.glist:
                if i.x == x and i.y == y:
                    #print(i.get_info())
                    chose.append(i)
                    if len(chose) == gl_ysize:
                        line = ""
                        sum_ = 0
                        for c in chose:
                            sum_ += c.value
                            line = line + c.get_info() + "|"
                        print(line)
                        chose_group.append((copy.copy(chose),sum_))
                    break
            new_gl = gl.get_new_glist(x,y)
            
            chose_group = get_max(new_gl,gl_ysize,copy.copy(chose),chose_group)
            chose.pop()
            break
    return chose_group


chose_group = get_max(gl1,len(gl1.ymap),[],[])

sorted_chose_group = sorted(chose_group, key=lambda x:x[1], reverse=1)

for i in sorted_chose_group:
    print(i[0][0].get_info(),i[0][1].get_info(),i[0][2].get_info(),i[0][3].get_info(),i[1])
    
    
    
    
    
    
    
    
    
