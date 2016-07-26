from kivy.clock import Clock
from kivy.vector import Vector

"""A baseclass for all of the active abilities in the game,
each ability is put into a data structure representing the category of it
"""
# Write more pythonic (useful) code with base classes, as in learn to do that
class ActiveAbility:

	description = ''
	category = None

	"""Each ability is assigned to a button, and __init__ contains attributes
	that can change from leveling up
	"""
	def __init__(self):
		self.level = 0
		self.cooldown = 0

	# Returns the printable name of ability.
	def __str__(self):
		return ''

	# This is temporary, remove if needed.
	def __repr__(self):
		f = 'Ability name: {}, Category: {}, Cooldown: {}'
		return f.format(str(self), self.category, self.cooldown)

	def __call__(self):
		return None

	def get_desc(self):
		return self.description

class SuperSpeed(ActiveAbility):

	description = 'Gain a speed up for a short duration.'
	category = 'utility'
	"""data in the format of 'level cooldown duration magnitude'
	"""
	data = [
			(5, 3, .3), # level 0
			(5, 3, .45) # level 1, etc.
			]
	def __init__(self, level=0):
		self.level = level
		self.cooldown = 0
		self.duration = 0
		self.magnitude = 0
		self.update_level()

	def __str__(self):
		return 'Super Speed'

	"""Confused as of now, to the active effects system. I don't know whether
	to have the action component of entities handle the effects, by passing
	effect information to them, or handle them from the skill itself, here.
	Decided on effect 1, because it allows effect information to be decoupled
	from actual effect, and allows the information to be retrieved easily.
	"""
	# Need to figure out how to extend duration instead of stack effects, from
	# the same ability. RESOLVED

	# As of now, it extends the effect from this skill if the skill is called again when its effect is still active
	def __call__(self, player):
		a = player.components['Action']
		for i in a.effects:
			if type(i) is SpeedUp and i.origin == self:
				i.__init__(self, self.duration, self.magnitude)
				return None
		a.effects.append(SpeedUp(self, self.duration, self.magnitude))

	# For updating effects when self.level variable is changed
	def update_level(self):
		self.cooldown, self.duration, self.magnitude = self.data[self.level]

"""TODO: Rewrite ability button to use game's update loop instead, so that the
game can be paused.
"""

class SpeedUp:

	def __init__(self, origin, duration, magnitude):
		self.origin = origin # origin is the source of the effect, used for stacking effects properly
		self.time_left = duration
		self.magnitude = magnitude

	def __call__(self, entity):
		if self.time_left <= 0:
			entity.components['Action'].effects.remove(self)
		self.time_left -= 1/60
		# As of now cannot handle multiple buffs stacked on top of eachother
		# without going crazy :p.
		entity.velocity = Vector(entity.velocity) * (1 + self.magnitude)
