# Using this Stuff

assuming i haven't fucked it all up, here's the deal:

You want to create a BaudotInterface object with your audio in/out pins, and to read or write data to it, use the .read() and .write() methods. 

Use .enable_listener() and .pause_listener() to stop the listener from triggering, but allow the sender to run (basically it doesn't tie up the lock)



todo:
 use both audio outputs to control the pwm? have 1440 asserted unless 1800 needs to go?
 