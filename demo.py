from antlia import *

# Create a GUI based on a layout file and a style file
GUI = Antlia("layout", "style")

# Define a handler for the button
def buttonHandler():
	print("Hello World")

	# Change the content of the label with something else
	GUI.change("hello_label", "parameter.text",
			"Hello World !")

# Bind the handler to the button
GUI.bind("hello_button", buttonHandler)