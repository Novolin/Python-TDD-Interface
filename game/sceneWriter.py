###
#
# TOOL FOR WRITING SCENES
#
###


import tkinter as tk
import tkinter.font as tkFont
import json


class Room:
    def __init__(self, text, exits, items, id, lock = False):
        self.text = text
        self.exits = exits
        self.items = items
        self.id = id
        self.lock = lock
        self.north = 0
        self.south = 0
        self.east = 0
        self.west = 0
    
    def modify_text(self, new_text):
        self.text = new_text


class Item:
    def __init__(self, name, id):
        self.name = name
        self.id = id

class Game:
    def __init__(self, filepath):
        self.filepath = filepath
        self.rooms = []
        self.items = []
    
    def export_script(self, format):
        if format == "txt":
            pass # write a parser here
        elif format == "json":
            pass # write a parser here!!!!!!

