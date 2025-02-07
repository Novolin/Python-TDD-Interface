# adding a wrapper to make things nice and easy

import asyncio

class BaudotInterface:
    def __init__(self, input_interface, output_interface):
        self.incoming_buffer = ""
        self.io_lock = asyncio.Lock() # stop input and output 
        self.input_interface = input_interface #TODO: make this init an input obj
        self.output_interface = output_interface #TODO: make this init an output obj

    async def write(self, string):
        # Push a string to the output buffer, and signal that we are ready to output data
        # Maybe this is the best time to sanitize our inputs?
        self.output_interface.buffer_string(string)
        with self.io_lock: # don't let the input program fire while we're doing this.
            await self.output_interface.send_buffered_data()
    
    def read(self):
        # Return the data that was in the buffer, and clear it.
        output = self.incoming_buffer
        self.incoming_buffer = ""
        return output 
    
    async def pull_buffered_data(self):
        # pull data from the input object
        # awaitable because it may be busy handling/decoding input
        with self.io_lock: # lock the input from happening??
            self.incoming_buffer += await self.input_interface.get_buffered_input()
        
        