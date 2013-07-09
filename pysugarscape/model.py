from random import randint, shuffle
from time import sleep
from math import pi, sqrt

from pyagents import Schedule, Agent, activate

class Thing(Agent):
    def __init__(self, id_, wealth, metabolism, vision, max_age, grid, sugar_grid, model):
        self.id_=id_
        self.wealth=wealth
        self.metabolism=metabolism
        self.vision=vision
        self.max_age=max_age
        self.grid = grid
        self.sugar_grid = sugar_grid
        self.model = model
        self.age = 0

    def neighbours(self):
        x, y = self.grid.find(self)
        return self.grid.neighbours(x, y, self.vision)

    @activate(level='grow')
    def grow(self):
        self.age += 1

    @activate(level='move')
    def move(self):
        target = None
        target_amt = self.sugar_grid.sugar_by_coords(*self.grid.find(self))
        neighbours = list(self.neighbours())
        shuffle(neighbours)
        for coords in neighbours:
            if self.grid.empty(*coords):
                amt = self.sugar_grid.sugar_by_coords(*coords)
                if target_amt < amt:
                    target_amt = amt
                    target = coords
        if target:
            self.grid.move(self, *target)
        sugar = self.sugar_grid.get_by_coords(*self.grid.find(self))
        if sugar:
            self.wealth += sugar.sugar
            sugar.sugar = 0
        self.wealth -= self.metabolism

    def __repr__(self):
        return "%03i" % self.id_

    def draw(self, cr, cx, cy):
        x, y = self.grid.find(self)
        wealth = self.wealth / float(self.model.wealth_range[1])
        cr.set_source_rgba(1, 1, 1, wealth)
        cr.arc(cx * (x + 0.5), cy * (y + 0.5), 0.4 * min([cx, cy]), 0, 2 * pi)
        cr.fill()

class SugarLocation(object):
    def __init__(self, max_sugar, grid):
        self.max_sugar = max_sugar
        self.sugar = 0
        self.grid = grid

    def grow(self, amt):
        if self.sugar < self.max_sugar:
            self.sugar += amt
            self.sugar = min(self.sugar, self.max_sugar)

    def draw(self, cr, cx, cy):
        x, y = self.grid.find(self)
        i = self.sugar/25.0
        cr.set_source_rgba(1, 0, 0, i)
        cr.rectangle(cx * x, cy * y, cx, cy)
        cr.fill()

class Grid(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._by_coords = dict([((x, y), None) for x in xrange(width) for y in xrange(height)])
        self._by_item = {} # starts empty as there are no items

    def items(self):
        for item in self._by_item.keys():
            yield item

    def coords(self, x, y):
        return (x % self.width, y % self.height)

    def get_by_coords(self, x, y):
        return self._by_coords[self.coords(x, y)]

    def empty(self, x, y):
        return not(self.get_by_coords(x, y))

    def occupied(self, x, y):
        return not(self.empty(x, y))
    
    def random_cell(self):
        return randint(0, self.width - 1), randint(0, self.height - 1)

    def neighbours(self, x, y, distance):
        for nx in xrange(x - distance, x + distance + 1):
            for ny in xrange(y - distance, y + distance + 1):
                if (nx, ny) != (x, y):
                    yield nx, ny

    def within_radius(self, x, y, radius):
        for nx, ny in self.neighbours(x, y, radius):
            if sqrt((nx - x)**2 + (ny - y)**2) <= radius:
                yield nx, ny

    def random_empty_cell(self):
        candidate = self.random_cell()
        while self.occupied(*candidate):
            candidate = self.random_cell()
        return candidate

    def place(self, item, x, y):
        coords = self.coords(x, y)
        self._by_coords[coords] = item
        self._by_item[item] = coords

    def place_randomly(self, item):
        x, y = self.random_empty_cell()
        self.place(item, x, y)

    def remove(self, item):
        from_x, from_y = self.find(item)
        del self._by_item[item]
        self._by_coords[(from_x, from_y)] = None
        
    def find(self, item):
        try:
            return self._by_item[item]
        except KeyError:
            raise UnknownItemError("Item not found [%s]" % item)

    def move(self, item, x, y):
        """this does all the heavy lifting"""
        from_x, from_y = self.find(item)
        to_x, to_y = self.coords(x, y)
        if self.occupied(to_x, to_y):
            raise OccupiedCellError("Cannot move into an occupied cell")
        self._by_item[item] = (to_x, to_y)
        self._by_coords[(from_x, from_y)] = None
        self._by_coords[(to_x, to_y)] = item


class SugarGrid(Grid, Agent):
    def __init__(self, width, height, growth_rate):
        Grid.__init__(self, width, height)
#        Agent.__init__(self)
        self.growth_rate = growth_rate

    def sugar_by_coords(self, x, y):
        item = self.get_by_coords(x, y)
        if not item:
            return 0
        else:
            return item.sugar
        
    def place_sugar(self, x, y, amount):
        coords = self.coords(x, y)
        item = self._by_coords[coords]
        if not item:
            item = SugarLocation(amount, self)
            self._by_coords[coords] = item
            self._by_item[item] = coords
        else:
            item.max_sugar += amount

    @activate(level='grow')
    def grow(self):
        for item in self._by_coords.values():
            if item:
                item.grow(self.growth_rate)

class OccupiedCellError(Exception): pass
class UnknownItemError(Exception): pass

class ThingGrid(Grid):

    def show(self, item):
        if item:
            return str(item)
        else:
            return '   '

    def __repr__(self):
        result = []
        for y in xrange(self.height):
            row = "|".join([self.show(self._by_coords[(x, y)]) for x in xrange(self.width)])
            result.append(row)
        return "\n".join(result)    

def uniform(myrange):
    return randint(*myrange)
    
class Model(Agent):
    def __init__(self, **kwargs):
        self.schedule = Schedule('grow', 'move', 'replace')
        self.agents = []
        self.id = 0
        Thing.activate(self.schedule)
        Model.activate(self.schedule)
        SugarGrid.activate(self.schedule)
        self.grid = ThingGrid(kwargs['width'], kwargs['height'])
        self.sugar_grid = SugarGrid(kwargs['width'], kwargs['height'], kwargs['growth_rate'])
        self.n_agents = kwargs['n_agents']
        self.wealth_range = kwargs['wealth_range']
        self.metabolism_range = kwargs['metabolism_range']
        self.vision_range = kwargs['vision_range']
        self.max_age_range = kwargs['max_age_range']

        third = (self.grid.width/3, self.grid.height/3)
        two_thirds = (self.grid.width/3*2, self.grid.height/3*2)

        for x, y in (third, two_thirds):
            for distance in xrange(10, min(third), 2):
                self.spread(x, y, distance, 1, 25)

        for i in xrange(self.n_agents):
            self.register(self.random_agent())
        self.tick = 0

    def spread(self, x, y, distance, probability, max_sugar):
        for nx, ny in self.grid.within_radius(x, y, distance):
            if randint(0, probability - 1):
                continue
            sugar = self.sugar_grid.get_by_coords(nx, ny)
            if sugar and sugar.max_sugar >= max_sugar:
                continue
            self.sugar_grid.place_sugar(nx, ny, 1)


    def next_id(self):
        self.id += 1
        return self.id

    def register(self, agent):
        self.agents.append(agent)
        self.grid.place_randomly(agent)

    def random_agent(self):
        return Thing(
            id_=self.next_id(),
            wealth=uniform(self.wealth_range),
            metabolism=uniform(self.metabolism_range),
            vision=uniform(self.vision_range),
            max_age=uniform(self.max_age_range),
            grid=self.grid,
            sugar_grid=self.sugar_grid,
            model=self
        )

    def run(self):
        self.tick = 0
        while True:
            self.step()
            yield self
            sleep(0.25)

    @activate(level='replace')
    def replace(self):
        for agent in self.agents:
            if agent.age > agent.max_age or agent.wealth <= 0:
                self.agents.remove(agent)
                self.grid.remove(agent)
        while len(self.agents) < self.n_agents:
            self.register(self.random_agent())
            
    def step(self):
        self.tick += 1
        self.schedule.execute(self.agents)
        self.schedule.execute([self, self.sugar_grid])

    def __repr__(self):
        return "%s\n%s" % (str(self.grid), "-" * self.grid.width * 4)

def main():
    model = Model(
        width=35, 
        height=35, 
        growth_rate=1, 
        n_agents=25,
        wealth_range=(5, 25),
        metabolism_range=(1, 4),
        vision_range=(1, 6),
        max_age_range=(60, 100)
    )
    for step in model.run():
        print step
    
if __name__ == "__main__":
    main()
