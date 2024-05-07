#####
#
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
    def __init__(self, object, name):
        self.name = name
        self.text = object["disp_text"]
        self.actions = object["acts"]
    
    def describe(self):
        send_msg(self.text)


class Game:
    def __init__(self, data_path):
        self.rooms = []
        with open(data_path, "r") as data_file:
            load_data = json.loads(data_file.read())
            for room in load_data:
                self.rooms.append(Room(load_data[room], room))
        print(self.rooms)
        self.current_room = 0
        self.last_room = 0
    def parse_command(self, command):
        if command.upper() == "BACK":
            self.current_room = self.last_room
            return True
        elif command.upper() in self.current_room["acts"]:
            pass

            

run_local = True # DEV! if true, runs an input() field instead of polling the baudot kb
running = True


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
    while running:
        send_msg("pee")
        game.parse_command(poll_input())
        
        

main()