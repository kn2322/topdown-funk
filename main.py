import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window

Builder.load_string("""
#: kivy 1.9.1	

<Game>
	EntityContainer:
		id: entity_container
		size: root.size
		pos: root.pos
	

""")

Window.size = (800, 600)

# Container widget for all game entites, so they can be referenced by the game.
class EntityContainer(Widget):
	pass

class Entity(Widget):
	# hp, size, ai, in order
	game_entities = dict(
		'Zombie'=(100, (50,50), 
		)
	"""TODO: Determine different attributes of each game entity, inc but not
	limited to the source image, status effect modifiers, speed.
	"""
	def __init__(self, hp, size, ai, **kwargs):
		super(Entity, self).__init__(**kwargs)
		self.hp = hp
		self.size = size
		self.ai = ai

	def destroy(self):
		pass

class AI():

	def __init__(self):
		pass

class Game(Widget):

	def update(self, dt):
		pass

	"""Creates entity in the gamespace with parameter which points to dict of 
	possible entities. The higher level determining the positions and numbers of
	entites to spawn are done with a higher level object(?).
	"""
	def create_entity(self, entity):
		objects = Entity.game_entities
		if entity not in objects.keys():
			raise ValueError("'{}' is an invalid entity.".format(entity))
		e = objects[entity]
		self.entity_container.add_widget(Entity(*e))

# TDS: Top Down Shooter
class TDSApp(App):

	def build(self):
		game = Game()
		Clock.schedule_interval(game.update, 1/60)
		return game
		
if __name__ == '__main__':
	TDSApp().run()