'''
Kitronik Inventor's Kit Exp 7
Control a seven segment display.
Count up from 0 to 9 and then back again.
'''
import machine
import time
segA = machine.Pin(18, machine.Pin.OUT)
segB = machine.Pin(17, machine.Pin.OUT)
segC = machine.Pin(16, machine.Pin.OUT)
segD = machine.Pin(15, machine.Pin.OUT)
segE = machine.Pin(14, machine.Pin.OUT)
segF = machine.Pin(13, machine.Pin.OUT)
segG = machine.Pin(12, machine.Pin.OUT)
pins = [segA, segB, segC, segD, segE, segF, segG]
 
''' 
This list of 10 numbers shows the states of the pins for the segments 
to display the appropriate number. This is used to simplify the code
later - we can index the list to display the correct number.
'''
# numbers = [zero, one, two, three, four, five, six, seven, eight, nine, clear display]
numbers = [[1,1,1,1,1,1,0], 
          [0,1,1,0,0,0,0], 
          [1,1,0,1,1,0,1], 
          [1,1,1,1,0,0,1], 
          [0,1,1,0,0,1,1], 
          [1,0,1,1,0,1,1], 
          [1,0,1,1,1,1,1], 
          [1,1,1,0,0,0,0], 
          [1,1,1,1,1,1,1], 
          [1,1,1,0,0,1,1], 
          [0,0,0,0,0,0,0]]
clearDisplay = 10 # The position in the 'numbers list of the clear display setup
# This function takes in which number should be displayed, and then selects the correct pin/segment setup from the numbers list to control the output pins
def displayNumber(numberToDisplay):
    pin = 0
    for segment in range (7):
        pins[pin].value(numbers[numberToDisplay][segment])
        pin += 1
    
    return numberToDisplay
# Loop round displaying 0 - 9 - 0, clear, and repeat
while True: 
    for i in range(10):
        displayNumber(i)
        time.sleep_ms(600)
    
    for i in range (9, -1, -1):
        displayNumber(i)
        time.sleep_ms(600)
        
    displayNumber(clearDisplay)
    time.sleep_ms(1000)