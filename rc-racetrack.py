import time
from ev3dev.ev3 import *

drive = LargeMotor()
turn = MediumMotor()

rc = RemoteControl()
ts = TouchSensor()

cl = ColorSensor()
cl.mode = 'RGB-RAW'


### remote control functions that return functions ###
def run(motor, direction, speed, ramp):
    'for the driving motors'
    'time to reach max speed is in milliseconds'
    motor.ramp_up_sp = ramp

    def on_press(state):
        if state:
            motor.run_forever(speed_sp=speed * direction)
        else:
            motor.stop(stop_action='brake')
    return on_press


def run_until(motor, position, speed):
    'for the rack & pinion'
    def on_press(state):
        if state:
            motor.run_to_abs_pos(
                position_sp=position, speed_sp=speed, stop_action='brake')
        else:
            motor.stop(stop_action='brake')
    return on_press
### end remote control functions ###


### gate verification functions ###
def between(element, target, variance):
    'helper function that checks if element is within a range'
    if element >= target - variance and element <= target + variance:
        return True

    return False


def detectGate(color, gatecolor):
    ''
    matches = 0
    for i in range(3):
        if between(color[i], gatecolor[i], 10):
            matches += 1

    if matches == 3:
        Sound.beep()
        return True

    return False
### end gate verification functions ###


# the event handler assigned to on_press(state)
# permanent event handlers for drive
rc.on_blue_up = run(drive, 1, 360, 3 * 1000)
rc.on_blue_down = run(drive, -1, 360, 3 * 1000)

# temporary event handlers for pinion calibration
rc.on_red_up = run(turn, 1, 90, 0)
rc.on_red_down = run(turn, -1, 90, 0)

print('press touch sensor when done calibration')
while not ts.value():
    rc.process()
    home = turn.position
print('calibrated')

# permanent event handlers for turning
rc.on_red_up = run_until(turn, home + 105, 90)
rc.on_red_down = run_until(turn, home - 105, 90)

# rgb characteristics of the gates
gates = {'pink': [218, 134, 102],
         'green': [115, 177, 81],
         'purple': [110, 79, 90]}


print('timer will begin when rc is pressed')
while not rc.any():
    pass
Sound.speak('3, 2, 1, GO!').wait()

start = stamp = time.time()
pinkgate = greengate = purplegate = False
while not (pinkgate and greengate and purplegate):
    rc.process()

    pos = turn.position

    r = cl.value(0)
    g = cl.value(1)
    b = cl.value(2)

    # as soon as we see the gate, the gate variable becomes
    # permanently triggered
    if pinkgate == False:
        pinkgate = detectGate([r, g, b], gates['pink'])
    if greengate == False:
        greengate = detectGate([r, g, b], gates['green'])
    if purplegate == False:
        purplegate = detectGate([r, g, b], gates['purple'])

    # print position and gatestatus every 0.2 seconds
    now = time.time()
    diff = now - stamp
    if diff > 0.2:
        print(pos)
        stamp = time.time()
        print('gatestatus: ', pinkgate, greengate, purplegate)

end = time.time()
print(end - start)

turn.stop(stop_action='brake')
drive.stop(stop_action='brake')

# text to speech, round the float with format function
Sound.speak(format(end - start, '.2f')).wait()
