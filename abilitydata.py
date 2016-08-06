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
	def __init__(self, level=0):
		self.level = level
		self.cooldown = 0
		self.current_cd = 0

	# Returns the printable name of ability.
	# For in tool tips, level ups, etc.
	def __str__(self):
		return ''

	# This is temporary, remove if needed.
	def __repr__(self):
		f = 'Ability name: {}, Category: {}, Cooldown: {}'
		return f.format(str(self), self.category, self.cooldown)

	# Use this instead of __call__, slightly more readable.
	def activate(self, entity):
		pass

	def get_desc(self):
		return self.description

"""Damage information class which is given when damage is dealt, contains info
on the attacker, damage type, and any other useful information.
"""
class DamageInfo:

	damage_types = ['projectile', 'contact']

	def __init__(self, attacker, amount, dmg_type):
		self.attacker = attacker
		self.amount = amount
		# For trouble shooting.
		if dmg_type in self.damage_types:
			self.type = dmg_type
		else:
			raise ValueError('{} is not a valid damage type'.format(dmg_type))

class SuperSpeed(ActiveAbility):

	description = 'Gain a speed up for a short duration.'
	category = 'utility'
	"""data in the format of 'level #cooldown duration magnitude'
	"""
	data = [
			(5, 3, 1.3), # level 0
			(5, 3, 1.45) # level 1, etc.
			]
	def __init__(self, level=0):
		self.level = level
		self.cooldown = 0
		self.duration = 0
		self.magnitude = 0
		self.effect = SpeedUp
		# Tangible cooldown to be subtracted.
		self.current_cd = 0
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
	def activate(self, entity):
		args = self.data[self.level]
		a = entity.components['Action']
		# cd counter has started, time_step is called in the entity (not sure if best).
		self.current_cd = self.cooldown
		for i in a.effects:
			# Refreshes buff if the duration and cooldown happens to overlap
			if type(i) is type(self.effect) and i.origin_id == self:
				i.__init__(*args)
				return None
		a.effects.append(self.effect(self, self.duration, self.magnitude))

	# For counting down cooldown.
	def time_step(self):
		self.current_cd -= 1

	# For updating effects when self.level variable is changed, and __init__
	def update_level(self):
		self.cooldown, self.duration, self.magnitude = self.data[self.level]
		# Convert seconds to frames
		self.cooldown *= 60

"""Below here is the ability effects.
"""

# General 'effect' class, shouldn't really 'bear' hero specific children
# That change attributes the general entity class doesn't have!!!
class Effect:

	"""All the methods are completely replacable, I am not sure if it's good
	practice to still but basic versions here.
	"""
	# m for multiplication, a for addition, looped twice.
	m_modifier_list = {}
	a_modifier_list = {}
	spec_modifier_list = {}

	def __init__(self, origin_id, duration):
		self.origin_id = origin_id # origin is the source of the effect, used for stacking effects properly
		self.duration = duration * 60 # In frames

	# idk if this will appear in the game
	def __str__(self):
		return ''

	# For listing modifies attributes.
	def list_modifiers(self):
		return set(list(m_modifier_list.keys()) + list(a_modifier_list.keys()))

	# Called when updating action component, used for counting cooldown
	def time_step(self):
		self.duration -= 1

	# Mode system is replaced by two separate functions, to be more explicit.
	def m_apply_modifier(self, attribute_id, val):
		if attribute_id in self.m_modifier_list.keys():
			modifier = self.m_modifier_list[attribute_id]
			return val * modifier
		else:
			return val

	def a_apply_modifier(self, attribute_id, val):
		if attribute_id in self.a_modifier_list.keys():
			modifier = self.a_modifier_list[attribute_id]
			return val + modifier
		else:
			return val

	def spec_apply_modifier(self, attribute_id, val):
		if attribute_id in self.spec_modifier_list.keys():
			modifier = self.spec_modifier_list[attribute_id]
			# Provisional, the order of spec modifiers are not decided.
			return modifier(attribute_id, val)
		else:
			return val

class SpeedUp(Effect):

	def __init__(self, origin_id, duration, magnitude):
		self.origin_id = origin_id
		self.duration = duration * 60
		self.magnitude = magnitude

		self.m_modifier_list = {'velocity_multiplier': self.magnitude}

	def __str__(self):
		return '{}% speedup, {} seconds remaining.'.format(
			self.magnitude - 1, round(self.duration / 60, 3)
			)

class Invincibility(Effect):

	def __init__(self, origin_id, duration):
		self.origin_id = origin_id
		self.duration = duration * 60

		self.spec_modifier_list = {'can_be_damaged': lambda *args: False}



