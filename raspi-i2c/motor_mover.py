import smbus

motor_board_address = 0x4

bus = smbus.SMBus(1)

def motor_forward(motor_n, motor_power):
    motor_mode = 0x2
    cmd_byte = motor_n << 5 | 24 | motor_mode << 1
    pwr = int(motor_power * 2.55)

    cmd = [cmd_byte, pwr]

    print("writing: {:b}, {:b}".format(*cmd))
    bus.write_i2c_block_data(motor_board_address, 0, cmd)


motor_forward(3, 50)

# motor_forward(1, 10)
# motor_forward(1, 10)

# void motorForward(int motorNum, int motorPower) { //Makes Motor motorNum go forwards at a power of motorPower
#   if (motorNum >= 0 and motorNum <= 5){
#     if (motorPower < 0){ //Lowest power possible = 0.
#       motorPower = 0;
#     }
#     if (motorPower > 100) {//Highest power possible = 100.
#       motorPower = 100;
#     }
    # int motorMode = 2; //Mode 2 is Forward
    # byte motor1 = motorNum<<5 | 24 | motorMode<<1 ;//Build Command Byte
    # byte motor2 = int(motorPower * 2.55);
    # uint8_t sender[2] = {motor1, motor2};
    # Wire.beginTransmission(MotorBoardI2CAddress); //open I2C communation to Motor Board.
    # Wire.write(sender,2);                    //send data.
    # byte fred = Wire.endTransmission();		//end I2C communcation.
#   }
# }
