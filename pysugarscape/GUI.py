import logging
import pygtk
pygtk.require('2.0')
import gtk

from model import Model

from gobject import timeout_add
import cairo

class gtkGrid(gtk.DrawingArea):
    def __init__(self, grid, sugar_grid):
        super(gtk.DrawingArea, self).__init__()
        self.grid = grid
        self.sugar_grid = sugar_grid
        self.connect("expose_event", self.expose)

    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        self.context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        self.context.clip()
        self.draw(self.context)

    def draw(self, cr):
        rect = self.get_allocation()
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(0, 0, rect.width, rect.height)
        cr.fill()
        cr.set_line_width(0.25)
        coefficients = float(rect.width)/self.sugar_grid.width, float(rect.height)/self.sugar_grid.height
        for item in self.sugar_grid.items():
            item.draw(cr, *coefficients)

        coefficients = float(rect.width)/self.grid.width, float(rect.height)/self.grid.height
        for item in self.grid.items():
            item.draw(cr, *coefficients)

class GUI(object):
    def __init__(self, model, timeout=200):
        window = gtk.Window()
        window.resize(600, 600)
        window.set_position(gtk.WIN_POS_CENTER)
        window.set_title("Sugarscape")
        window.connect("destroy", gtk.main_quit)
        self.model = model
        self.grid = gtkGrid(self.model.grid, self.model.sugar_grid)
        window.add(self.grid)
        window.show_all()
        timeout_add(timeout, self.step)

    def step(self):
        self.model.step()
        self.grid.queue_draw()
        return True

def main():
    model = Model(
        width=150, 
        height=150, 
        growth_rate=1, 
        n_agents=250,
        wealth_range=(5, 25),
        metabolism_range=(1, 4),
        vision_range=(1, 6),
        max_age_range=(60, 100)
    )
    gui = GUI(model, timeout=150)
    gtk.main()

if __name__ == "__main__":
    main()
