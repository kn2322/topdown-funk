from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import Rectangle, Ellipse, Color
from kivy.vector import Vector
from kivy.uix.gridlayout import GridLayout

"""Module used to contain all information about the game map(s),
including obstacles to be placed, and other fine details that
aren't suitable for the main file.

The map will be split into chunks of (PREMATURE OPTIMIZATION).
"""

# The map class which will take arguments from a data struct to create a map
# make this a container, containing bg image, and map objects, while the collision is all handled by it!
class Map(Widget):

    MAPS = {
        'galaxy': (
        (820, 540), Rectangle(size=(820, 540), source='./assets/maps/galaxy.jpg')
        )
    }

        
    # not magic method to work around kv not being able to pass arguments to __init__.
    def __init__(self, map_name, **kw):
        super(Map, self).__init__(**kw)
        self.pos = 0, 0
        self.size, self.graphics = self.MAPS[map_name]
        self.background = './assets/maps/skybg.jpg' # Temporary background solution, better to have some structure for changing bg later on.
        self.time = 0
        self.bg_size = 1500

    def reset(self):
    	self.time = 0
        

    def update(self, game): # very questionable
        offset = game.camera.offset
        self.canvas.clear()
        self.canvas.add(Color())
        self.bg_size = 1500 - self.time / 5 # Scales background size with time elapsed, to give 'floating away' feeling.
        self.canvas.add(Rectangle(pos=(0,0), size=(self.bg_size, self.bg_size), source=self.background))


        self.graphics.pos = offset
        self.canvas.add(Color())
        self.canvas.add(self.graphics)

        self.time += 1

# Serves little purpose, since collision is handled by map
class MapObject(Widget):

    def __init__(self, **kwargs):
        super(MapObject, self).__init__(**kwargs)

class Boulder(MapObject):

    def __init__(self, **kwargs):
        super(Boulder, self).__init__(**kwargs)
        self.size = 50, 50
        self.graphics = Ellipse(size=self.size)


