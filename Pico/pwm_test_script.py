import mpbd

test = mpbd.BaudotOutput(19)


def send_ryry():
    test.write("RYRYRY")

def send_and_debug(string:str):
    # sends a string and prints the binary values to console
    sent_string = test.sanitize_string(string)
    test.buffer_string(sent_string)
    for c in test.buffer:      
        print("0b0" + bin(c)[2:], end=" ")
    test.send_buffer() 
