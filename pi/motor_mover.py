import smbus
# import time


class MotorMover(object):
    '''
    This class interfaces with the Motor Control board connected to the I2C
    pins on the Rasberry Pi.
    It is based off a basic Arduino class called SDPArduino.cpp (which at the
    time of writing is available from
    http://homepages.inf.ed.ac.uk/gde/work/sdp/SDPArduino.zip )
    '''

    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.motor_board_address = 0x4

    def motor_move(self, motor_n, motor_power):
        '''
        This method allows for the control of the motor with the number motor_n
        at the power given by motor_power.
        If the power is:
            Positive - Go Forwards
            Negative - Go Backwards
            Zero - Stop
        '''
        if motor_power > 0:
            self.motor_forward(motor_n, motor_power)
        elif motor_power < 0:
            self.motor_backward(motor_n, abs(motor_power))
        else:
            self.motor_stop(motor_n)

    def motor_forward(self, motor_n, motor_power):
        '''
        This method controls the motor a the motor_n to go in a forwards
        direction, using the motor_power to control how fast that happens
        '''
        motor_mode = 0x2
        cmd_byte = motor_n << 5 | 24 | motor_mode << 1
        pwr = int(motor_power * 2.55)

        cmd = [cmd_byte, pwr]

        print("writing: {:b}, {:b}".format(*cmd))
        self.bus.write_i2c_block_data(self.motor_board_address, 0, cmd)

    def motor_backward(self, motor_n, motor_power):
        '''
        This method controls the motor a the motor_n to go in a backwards
        direction, using the motor_power to control how fast that happens
        '''
        motor_mode = 0x3
        cmd_byte = motor_n << 5 | 24 | motor_mode << 1
        pwr = int(motor_power * 2.55)

        cmd = [cmd_byte, pwr]

        self.bus.write_i2c_block_data(self.motor_board_address, 0, cmd)

    def motor_stop(self, motor_n):
        '''
        This stops the motor_n
        '''
        motor_mode = 0x0
        cmd_byte = motor_n << 5 | 16 | motor_mode << 1

        self.bus.write_i2c_block_data(self.motor_board_address, 0, [cmd_byte])

    def all_motor_stop(self):
        '''
        This stops all motors
        '''
        cmd = 0x1
        self.bus.write_i2c_block_data(self.motor_board_address, 0, [cmd])
