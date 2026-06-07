import legoeducation as le
import time

dm = le.DoubleMotor()
dm.connect(card_color=le.LEGO_COLOR_MAGENTA, card_serial="1230")

if not dm.connected:
	print('Error connecting to Double Motor.')
	exit(1) # error connecting
      
	
print(f'position: {dm.motor[le.MOTOR_LEFT].position}')

for i in range(100):
    time.sleep(0.01)
    dm.movement_move_for_degrees(90)
    
    print(f'motorBitMask: {dm.motor[le.MOTOR_LEFT].motorBitMask}') 
    print(f'motorState: {dm.motor[le.MOTOR_LEFT].motorState}')
    print(f'absolutePosition: {dm.motor[le.MOTOR_LEFT].absolutePosition}')
    print(f'power: {dm.motor[le.MOTOR_LEFT].power}')
    print(f'speed: {dm.motor[le.MOTOR_LEFT].speed}')
    print(f'position: {dm.motor[le.MOTOR_LEFT].position}')
    print(f'gesture: {dm.motor[le.MOTOR_LEFT].gesture}\n')
	
	

    	# print(f'orientation: {dm.imu_device.orientation}')
	# print(f'yawFace: {dm.imu_device.yawFace}')
	# print(f'yaw: {dm.imu_device.yaw}')
	# print(f'pitch: {dm.imu_device.pitch}')
	# print(f'roll: {dm.imu_device.roll}')
	# print(f'accelerometerX: {dm.imu_device.accelerometerX}')
	# print(f'accelerometerY: {dm.imu_device.accelerometerY}')
	# print(f'accelerometerZ: {dm.imu_device.accelerometerZ}\n')
	# print(f'gyroscopeX: {dm.imu_device.gyroscopeX}')
	# print(f'gyroscopeY: {dm.imu_device.gyroscopeY}')
	# print(f'gyroscopeZ: {dm.imu_device.gyroscopeZ}\n')
	 # compare to Device Face constants
 # compare to Device Face constants
	# dm.movement_move_for_time(time_ms=1000,speed=50)
	# print(f'accelerometerX: {dm.imu_device.accelerometerX}')
	# print(f'accelerometerY: {dm.imu_device.accelerometerY}')
	# print(f'accelerometerZ: {dm.imu_device.accelerometerZ}\n')
	

# Disconnect
#help(dm.imu_device)
dm.disconnect()
exit(0) # successful execution