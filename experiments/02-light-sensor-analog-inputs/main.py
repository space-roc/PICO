'''
Kitronik Inventor's Kit Exp 2
Turns an LED on and off in response to changing light level.
The Pico has an on-board LED you can control, connected to GP25.
A phototransistor is connected to Analogue-In A0, pulling it up to 3.3V.
As the light level varies the analogue input will vary, with bright light being nearer full scale, and dark being near to 0.
We can then use this to turn on the on-board LED as it gets dark.
'''
import machine
lightSensor = machine.ADC(26) # Setup the analogue (A0) on GP26 with a human-readable name
LED = machine.Pin(25, machine.Pin.OUT) # Setup the onboard LED Pin as an output
lightLevelToSwitchAt = 13000 # Set to about 20 percent of scale - Pico ADC is 0 to 65535
# The loop function runs forever, reading the light level and turning on the LED if it's dark
while True:
  # First read the light value on the analog input
  lightValue = lightSensor.read_u16()
  # Now decide what to do
  if (lightValue > lightLevelToSwitchAt): # Then it is bright, so turn off the LED
    LED.value(0)   # Turn the LED off
  else:
    LED.value(1)   # turn the LED