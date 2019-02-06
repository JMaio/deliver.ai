from motor_mover import *
import time

m = MotorMover()

def self_test_wheels():
    direction = input("Direction?")

    if direction == "L":
        go_left()
    elif direction == "R":
        go_right()
    elif direction == "F":
        go_f()
    elif direction == "B":
        go_b()

    time.sleep(10)
    m.all_motor_stop

#Need to check directions
def go_left():
    dir = [(2,0),(3,40),(4,0),(5,-40)]
    for (mo,p) in dir:
        m.motor_move(mo, p)

def go_right():
    dir = [(2,0),(3,-40),(4,0),(5,40)]
    for (mo,p) in dir:
        m.motor_move(mo, p)

def go_f():
    dir = [(2,40),(3,0),(4,-40),(5,0)]
    for (mo,p) in dir:
        m.motor_move(mo, p)

def go_b():
    dir = [(2,-40),(3,0),(4,40),(5,0)]
    for (mo,p) in dir:
        m.motor_move(mo, p)
