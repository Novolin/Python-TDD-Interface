###
# File loading script, for importing game data
#
###

import json

class FileTool:
    def __init__(self, file_loc):
        self.file_loc = file_loc
        self.file_data = open(file_loc)