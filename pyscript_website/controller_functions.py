import asyncio
import legoeducation as le

class controller(le.Controller):

    def left_up(self):
        return self.sensor.leftPercent > 0

    def left_down(self):
        return self.sensor.leftPercent < 0

    def left_released(self):
        return self.sensor.leftPercent == 0

    def right_up(self):
        return self.sensor.rightPercent > 0

    def right_down(self):
        return self.sensor.rightPercent < 0

    def right_released(self):
        return self.sensor.rightPercent == 0

    def left_position(self):
        return self.sensor.leftPercent

    def right_position(self):
        return self.sensor.rightPercent

    async def drive(self, dm, t=100):
        for i in range(t):
            dm.movement_move_tank(self.left_position(),
                                  self.right_position(),
                                  blocking=False)
            await asyncio.sleep(0.1)
        dm.stop()
    