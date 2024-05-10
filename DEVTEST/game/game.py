#####
# BASIC TEXT ADVENTURE ENGINE #
#     V0.1   May, 2024
###
import json

''' REMOVE WHEN USING HARDWARE!!
import board
import usb_cdc 
import baudot_tty as bd
'''

class Room:
    # Parent class for any room!
    def __init__(self, ref_obj):
        self.name = ref_obj["name"]
        self.description = ref_obj["description"]
        self.verbs = ref_obj["verbs"]
        self.objects = self.init_objects(ref_obj["objects"])

    def init_objects(self, obj_list):
        pass # Make linked objects into an actual object form.

    def add_object(self, obj):
        pass

    def remove_obj(self, obj_pointer):
        removed = self.objects[obj_pointer]
        self.objects.remove(removed)
        return removed

class GameObject:
    def __init__(self, ref_obj):
        self.name = ref_obj["name"]
        self.description = ref_obj["description"]
        self.usable = ref_obj["usable"]
        self.static = ref_obj["static"]
        self.target = ref_obj["target"]

class Player:
    def __init__(self):
        self.location = "start"
        self.inventory = []


class Game:
    def __init__(self, data_path):
        self.rooms = []
        self.running = True
        self.player = Player()

run_local = True # DEV! if true, runs an input() field instead of polling the baudot kb



def send_msg(msg):
    lines = msg.splitlines()
    for l in lines:
        if run_local:
            print(l)
        else:
            # bd.send_message(msg)
            pass  

def poll_input():
    if run_local:
        result = input(">")
    else:
        pass # Replace with baudot reading when thats working
    
    return result

def main():
    game = Game("game/scenes.json")
    print("READY")
    while game.running:
        send_msg("pee")
        game.parse_command(poll_input())
        
        

main()