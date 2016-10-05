from kivy.uix.widget import Widget
from random import randint
import timeit.timeit as ti
from functools import partial
import utilfuncs import circle_collide as cc

if __name__ == '__main__':
	t1 = #[Widget(pos=(randint(0, 800), randint(0, 600))
		  #for i in range(2)]
	ti(partial(cc, t1[0], t1[1]))
	ti(t1[0].collide_widget())