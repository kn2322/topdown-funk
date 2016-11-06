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
        

    def update(self, game): # very questionable
        offset = game.camera.offset
        self.canvas.clear()

        self.graphics.pos = offset
        self.canvas.add(Color())
        self.canvas.add(self.graphics)

# Serves little purpose, since collision is handled by map
class MapObject(Widget):

    def __init__(self, **kwargs):
        super(MapObject, self).__init__(**kwargs)

class Boulder(MapObject):

    def __init__(self, **kwargs):
        super(Boulder, self).__init__(**kwargs)
        self.size = 50, 50
        self.graphics = Ellipse(size=self.size)


