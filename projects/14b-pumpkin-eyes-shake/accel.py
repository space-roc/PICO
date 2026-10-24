# Driver for the DFRobot Gravity I2C LIS2DW12 accelerometer (SEN0409).

from struct import unpack

ADDRESS = 0x19 # 0x18 if the board's address switch is set the other way

_WHO_AM_I = 0x0F
_CTRL1 = 0x20
_CTRL2 = 0x21
_CTRL6 = 0x25
_OUT_X_L = 0x28

# Full scale in g, the CTRL6 setting for it, and g per 14-bit count
_SCALES = {
    2: (0x00, 0.000244),
    4: (0x10, 0.000488),
    8: (0x20, 0.000976),
    16: (0x30, 0.001952),
}


class Accelerometer:
    def __init__(self, i2c, address=ADDRESS, full_scale=8):
        self.i2c = i2c
        self.address = address
        if i2c.readfrom_mem(address, _WHO_AM_I, 1)[0] != 0x44:
            raise OSError("not a LIS2DW12")
        ctrl6, self._scale = _SCALES[full_scale]
        i2c.writeto_mem(address, _CTRL2, b"\x0C") # Block data update, auto-increment
        i2c.writeto_mem(address, _CTRL6, bytes((ctrl6,)))
        i2c.writeto_mem(address, _CTRL1, b"\x54") # 100 Hz, high performance

    def read(self):
        """Return (x, y, z) acceleration in g."""
        x, y, z = unpack("<hhh", self.i2c.readfrom_mem(self.address, _OUT_X_L, 6))
        scale = self._scale
        # The 14-bit result is left-justified in 16 bits
        return (x >> 2) * scale, (y >> 2) * scale, (z >> 2) * scale
