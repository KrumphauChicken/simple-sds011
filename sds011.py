import serial

_MSG_HEAD = b'\xaa'  # 0xAA
_MSG_ID = b'\xb4'    # 0xB4
_MSG_TAIL = b'\xab'  # 0xAB

_CMD_REPORT_MODE = 2
_CMD_QUERY = 4
_CMD_DEV_ID = 5
_CMD_WAKE_STATE = 6
_CMD_FIRMWARE = 7
_CMD_WORK_PERIOD = 8

MODE_ACTIVE = 0
MODE_QUERY = 1
STATE_SLEEP = 0
STATE_WORK = 1

_BAUDRATE = 9600
_BYTESIZE = serial.EIGHTBITS
_PARITY = serial.PARITY_NONE
_STOPBITS = serial.STOPBITS_ONE


class SDS011:
    def __init__(self, port=None, device_id=b'\xff\xff', read_timeout=1):
        self._sd = serial.Serial(port, timeout=read_timeout)
        #self.device_id = device_id or b'\xff\xff'


    @property
    def device_id(self):
        """The device ID.

        (Unimplemented for now. Returns 'all' byte string.)
        """
        return b'\xff\xff'


    @property
    def firmware(self):
        """The device firmware byte string."""
        self._send_command(_CMD_FIRMWARE, 0, 0)
        return self._get_response()


    @property
    def port(self):
        """The open port in the backing serial-device object."""
        return self._sd.port


    @property
    def mode(self):
        """Active (0) or query (1) report mode.

        When the report mode is active, the device sends sample data
        once every work period (once per second in continuous sampling).
        When the report mode is query, the device sends sample data
        only when queried.

        NOTE: Only use 'query' mode for the time being. This draft does
        not contain functions to accommodate the continuous responses
        in the 'active' mode. Use the clear() function to clear the
        underlying input buffer if the device was left in 'active' mode.
        """
        self._send_command(_CMD_REPORT_MODE, 0, 0)
        return self._get_response()


    @property
    def period(self):
        """N-minute work period per sample.

        Values may be set between 0 (continuous sampling) or 30 minutes.
        A work period is N * 60 - 30 seconds of sleeping, followed
        one 30-second sample interval.
        """
        self._send_command(_CMD_WORK_PERIOD, 0, 0)
        return self._get_response()


    @property
    def state(self):
        """Whether the sensor is sleeping (0) or working (1)."""
        self._send_command(_CMD_WAKE_STATE, 0, 0)
        return self._get_response()


    @mode.setter
    def mode(self, mode: bool):
        self._send_command(_CMD_REPORT_MODE, 1, mode)
        return self._get_response()


    @period.setter
    def period(self, minutes: int):
        self._send_command(_CMD_WORK_PERIOD, 1, minutes)
        return self._get_response()


    @state.setter
    def state(self, active: bool):
        self._send_command(_CMD_WAKE_STATE, 1, active)
        return self._get_response()

    def _calc_payload_checksum(self, payload):
        """Return first 8 bits of the sum of the data bytes."""
        return sum(payload) & 255


    def _build_message(self, payload):
        """Given the payload, return the complete packet."""
        checksum_byte = bytes([self.__calc_payload_checksum(payload)])
        return _MSG_HEAD + _MSG_ID + payload + checksum_byte + _MSG_TAIL


    def _build_payload(self, command, mode, setting):
        """Given the command and options, return the packet payload."""
        payload = bytearray([command, mode, setting])
        payload += bytearray(10)
        payload += self.device_id
        return payload


    def _get_response(self):
        """Read a 10-byte response from the device."""
        return self._sd.read(10)


    def _send_command(self, command, mode, setting):
        """Send a command to the device.

        Encapsulates a command, command mode, and command argument in
        a checksummed packet, and sends this to the device.
        Returns return code from device, but not device reply.
        """
        payload = bytearray([command, mode, setting])
        payload += bytearray(10)
        payload += self.device_id
        checksum = bytes([sum(payload) & 255])
        message = _MSG_HEAD + _MSG_ID + payload + checksum + _MSG_TAIL
        return self._sd.write(message)


    def clear(self):
        """Clear the device buffer."""
        self._sd.reset_input_buffer()


    def open(self, port):
        """Open serial port if the instance was created without one."""
        if not self._sd.port:
            self._sd.port = port
            self._sd.open()


    def query(self):
        """Request a sample datum."""
        self._send_command(_CMD_QUERY, 0, 0)
        return self._get_response()

