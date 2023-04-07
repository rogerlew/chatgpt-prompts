import time
import math
from typing import Tuple

import time


class Pump:
    def __init__(self, flow_rate: float):
        """Initialize a Pump object with a given flow rate.
        
        Args:
            flow_rate (float): Flow rate in mm³/s.
        """
        self._flow_rate = flow_rate
        self._status = False
        self._last_on_time = 0

    @property
    def status(self) -> bool:
        return self._status

    @status.setter
    def status(self, value: bool) -> None:
        if value:
            self._status = True
            self._last_on_time = time.time()
        else:
            if time.time() - self._last_on_time >= 2:
                self._status = False

    def flow_rate(self) -> float:
        """Returns the flow rate if the pump is on, otherwise returns 0."""
        return self._flow_rate if self.status else 0


class Drain:
    def __init__(self, diameter: float):
        """Initialize a Drain object with a given diameter.

        Args:
            diameter (float): Diameter in mm.
        """
        self.diameter = diameter

    def flow_rate(self, pressure: float) -> float:
        """Calculate the drain flow rate based on the given pressure.

        Args:
            pressure (float): Pressure in mm of water column.

        Returns:
            float: Drain flow rate in mm³/s.
        """
        return pressure * (math.pi * (self.diameter / 2) ** 2)


class Tank:
    def __init__(self, height: float, diameter: float, level: float):
        """Initialize a Tank object with given height, diameter, and level.
        
        Args:
            height (float): Height of the tank in mm.
            diameter (float): Diameter of the tank in mm.
            level (float): Water level as a fraction between 0 and 1.
        """
        self.height = height
        self.diameter = diameter
        self.level = level

    @property
    def volume(self) -> float:
        """Calculate the volume of the tank."""
        return self.level * math.pi * (self.diameter / 2) ** 2 * self.height

    @property
    def water_height(self) -> float:
        """Calculate the height of the water in the tank."""
        return self.height * self.level


class ControlSystem:
    def __init__(self, pump: Pump, tank_b: Tank, set_point: float, deadband: float):
        """Initialize a ControlSystem object.

        Args:
            pump (Pump): The pump object.
            tank_b (Tank): The Tank B object.
            set_point (float): The desired water level as a fraction.
            deadband (float): The allowed deviation from the set_point as a fraction.
        """
        self.pump = pump
        self.tank_b = tank_b
        self.set_point = set_point
        self.deadband = deadband

    def update(self) -> None:
        """Update the pump status based on the water level in Tank B."""
        if self.tank_b.level > self.set_point + self.deadband:
            self.pump.status = True
        elif self.tank_b.level < self.set_point - self.deadband:
            self.pump.status = False


class WaterSystem:
    def __init__(self, tank_a: Tank, tank_b: Tank, pump: Pump, drain: Drain, control_system: ControlSystem):
        """Initialize a WaterSystem object with the given components.

        Args:
            tank_a (Tank): The Tank A object.
            tank_b (Tank): The Tank B object.
            pump (Pump): The pump object.
            drain (Drain): The drain object.
            control_system (ControlSystem): The control system object.
        """
        self.tank_a = tank_a
        self.tank_b = tank_b
        self.pump = pump
        self.drain = drain
        self.control_system = control_system

    def step(self, delta_t: float) -> Tuple[float, float]:
        """Update the water levels in the tanks based on the current state of the system.

        Args:
            delta_t (float): Time step in seconds.

        Returns:
            Tuple[float, float]: Change in water levels for Tank A and Tank B.
        """
        self.control_system.update()

        pump_flow = self.pump.flow_rate() * delta_t
        tank_a_drain_pressure = max(self.tank_a.water_height - self.tank_b.water_height, 0)
        drain_flow = self.drain.flow_rate(tank_a_drain_pressure) * delta_t

        delta = pump_flow - drain_flow

        self.tank_a.level += delta / self.tank_a.volume
        self.tank_b.level -= delta / self.tank_b.volume

        return delta

import time
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    tank_a = Tank(200, 100, 0.5)
    tank_b = Tank(100, 100, 1.0)
    pump = Pump(8000)
    drain = Drain(9)
    control_system = ControlSystem(pump, tank_b, 0.5, 0.02)
    water_system = WaterSystem(tank_a, tank_b, pump, drain, control_system)

    start_time = time.time()
    last_print = start_time
    end_time = start_time + 300

    times = []
    tank_a_levels = []
    tank_b_levels = []

    while time.time() <= end_time:
        current_time = time.time()
        delta_t = current_time - start_time
        start_time = current_time

        water_system.step(delta_t)

        times.append(current_time)
        tank_a_levels.append(tank_a.level)
        tank_b_levels.append(tank_b.level)

        if current_time - last_print >= 1:
            print(
                f"Tank A Level: {tank_a.level:.2%}\n"
                f"Tank B Level: {tank_b.level:.2%}\n"
                f"Pump Status: {'On' if pump.status else 'Off'}\n"
                f"Drain Flow: {drain.flow_rate(tank_a.water_height - tank_b.water_height):.2f} mm³/s"
            )
            last_print = current_time

    times = np.array(times) - times[0]
    tank_a_levels = np.array(tank_a_levels)
    tank_b_levels = np.array(tank_b_levels)

    plt.plot(times, tank_a_levels, label="Tank A Level")
    plt.plot(times, tank_b_levels, label="Tank B Level")
    plt.xlabel("Time (s)")
    plt.ylabel("Water Level")
    plt.title("Water Levels in Tanks A and B")
    plt.legend()
    plt.savefig("ts.png", dpi=300)

