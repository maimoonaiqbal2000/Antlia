from .elements.translate import toArrayOfSizes, toBoolean
from .message import catch, ERROR, WARNING, OK
from .rect import Rect
import os
import sys
import ctypes
import time as ti
import pkg_resources

LIB_PATH = pkg_resources.resource_filename('antlia', 'lib/')

os.environ["PYSDL2_DLL_PATH"] = LIB_PATH
try:
	import sdl2
	import sdl2.sdlttf as sdl2ttf
	import sdl2.sdlimage as sdl2img
except ImportError:
	import traceback
	traceback.print_exc()
	sys.exit(1)

class Renderer:
	"""
	The Renderer initializes an SLD2 context
	and gives the ability to draw elements on it.

	Renderer()
	Renderer.refresh()
	Renderer.quit()
	"""
	def __init__(self, params):
		self.is_window_created = False
		self.need_update = False
		self.params = params
		self.is_running = True

		# Handlers
		self.onEvent = None
		self.onStart = None

		# Translation of the window parameters
		resolution, _ = catch(
			toArrayOfSizes, (self.params["resolution"],),
			ERROR, "Invalid .resolution")

		self.window_width, self.window_height = resolution
		self.show_borders = toBoolean(self.params["show-borders"])

		# List of element index to be built
		self.indices_to_be_built = []

	def createWindow(self):
		# Create the window context
		if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
			print(sdl2.SDL_GetError())
			return -1
		sdl2ttf.TTF_Init()
		sdl2img.IMG_Init(sdl2img.IMG_INIT_PNG)

		self.window = sdl2.SDL_CreateWindow(self.params["title"].encode(),
					   sdl2.SDL_WINDOWPOS_UNDEFINED,
					   sdl2.SDL_WINDOWPOS_UNDEFINED,
					   self.window_width,
					   self.window_height,
					   sdl2.SDL_WINDOW_OPENGL)
		sdl2.SDL_SetWindowBordered(self.window, self.show_borders)
		if not self.window:
			print(sdl2.SDL_GetError())
			return -1

		# Renderer
		self.renderer = sdl2.SDL_CreateRenderer(self.window, -1,
			sdl2.SDL_RENDERER_ACCELERATED|sdl2.SDL_RENDERER_PRESENTVSYNC)

		# Build the GUI
		self.buildElements()

		# onStart handler
		if self.onStart is not None:
			if self.onStart[1] is None:
				self.onStart[0]()
			else:
				self.onStart[0](self.onStart[1])

		# look for events
		self._loopForEvents()

	def minimizeWindow(self):
		sdl2.SDL_MinimizeWindow(self.window)

	def update(self, layout_elements, layout_rects):
		self.layout_elements = layout_elements
		self.layout_rects = layout_rects
		self.need_update = True

	def addElementIndexToBuild(self, element_index):
		self.indices_to_be_built.append(element_index)
		self.need_update = True

	def buildElements(self):
		for i, el in enumerate(self.layout_elements):
			el.build(self.renderer, self.layout_rects[i])

	def buildElement(self, i):
		self.layout_elements[i].build(self.renderer, self.layout_rects[i])

	def getWindowPosition(self):
		# Use pointers
		X = ctypes.pointer(ctypes.c_long(0))
		Y = ctypes.pointer(ctypes.c_long(0))
		sdl2.SDL_GetWindowPosition(self.window, X, Y)

		return X.contents.value, Y.contents.value

	def setWindowPosition(self, x, y):
		sdl2.SDL_SetWindowPosition(self.window, x, y)

	def quit(self):
		self.is_running = False
		# Give time for the other thread to end
		ti.sleep(0.05)

		# Destroy the SDL context
		sdl2.SDL_DestroyRenderer(self.renderer)
		sdl2.SDL_HideWindow(self.window)
		sdl2.SDL_DestroyWindow(self.window)
		sdl2.SDL_Quit()

	def setOnEvent(self, onEvent):
		self.onEvent = onEvent

	def setOnStart(self, onStart, args=None):
		self.onStart = (onStart, args)

	def _refreshElement(self, i):
		"""
		Only draw one element
		"""
		self.layout_elements[i].draw(self.renderer)
		sdl2.SDL_RenderPresent(self.renderer)

	def _refresh(self):
		"""
		Draws the entire GUI when it needs to be updated
		"""
		# Clear with white
		sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 255, 255);
		sdl2.SDL_RenderClear(self.renderer)

		# TODO
		# For each element of the layout, call its draw method
		for el in self.layout_elements:
			el.draw(self.renderer)

		# Render to the screen
		sdl2.SDL_RenderPresent(self.renderer)

	def _loopForEvents(self):
		event = sdl2.SDL_Event()

		sdl2.SDL_StartTextInput()
		while self.is_running:
			# Look at the event queue
			while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
				self.onEvent(event)

			# Look for layout changes
			if self.need_update:
				# Rebuilt only what is needed
				for i in self.indices_to_be_built:
					self.buildElement(i)
				self.indices_to_be_built = []

				# Draw the elements
				self._refresh()
				self.need_update = False
			sdl2.SDL_Delay(1)
