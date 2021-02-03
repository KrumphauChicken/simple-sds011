"""simple-sds011 is a minimal python library for managing
Nova SDS011 particulate matter sensors.
"""

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

MODE_CONTINUOUS = 0
MODE_PASSIVE = 1
PERIOD_NONE = 0
PERIOD_FIVE = 5
PERIOD_TEN = 10
PERIOD_MAX = 30

_BAUDRATE = 9600
_BYTESIZE = serial.EIGHTBITS
_PARITY = serial.PARITY_NONE
_STOPBITS = serial.STOPBITS_ONE


class SDS011:
    def __init__(self, port=None, device_id=b'\xff\xff', read_timeout=1):
        self._sd = serial.Serial(port, timeout=read_timeout)
        #self.device_id = device_id or b'\xff\xff'


    @property
    def active(self):
        """Whether the device fan and laser are powered (1) or not (0).

        Use this to sleep the device, preserving the life of
        the laser diode and fan.
        """
        self._send_command(_CMD_WAKE_STATE, 0, 0)
        return self._get_response()


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
        """Continuous (0) or passive (1) report mode.

        When the report mode is 'continuous', the device sends sample
        data once every work period (or once per second with no period).
        When the report mode is 'passive', the device sends sample data
        only when queried.

        NOTE: Only use 'passive' mode for the time being. This draft
        does does not handle the nonstop input from 'continuous' mode.
        Use the clear() function to clear the underlying input buffer
        if the device was left in 'continuous' mode.

        NOTE: Continuous and passive sampling are called 'active' and
        'query' in the spec sheet, but the 'active' term can be confused
        with an active device versus a sleeping device.
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


    @active.setter
    def active(self, value: bool):
        self._send_command(_CMD_WAKE_STATE, 1, value)
        return self._get_response()


    @mode.setter
    def mode(self, mode: bool):
        self._send_command(_CMD_REPORT_MODE, 1, mode)
        return self._get_response()


    @period.setter
    def period(self, minutes: int):
        self._send_command(_CMD_WORK_PERIOD, 1, minutes)
        return self._get_response()


    def _calc_payload_checksum(self, payload):
        """Return first 8 bits of the sum of the data bytes."""
        return sum(payload) & 255


    def _verify_packet(self, packet):
        """Verify the checksum of a packet."""
        our_checksum = self._calc_payload_checksum(packet[2:8])
        return our_checksum == packet[8]


    def _build_message(self, payload):
        """Given the payload, return the complete packet."""
        checksum_byte = bytes([self.__calc_payload_checksum(payload)])
        return _MSG_HEAD + _MSG_ID + payload + checksum_byte + _MSG_TAIL


    def _build_payload(self, command, write: bool, value, int):
        """Given the command and options, return the packet payload."""
        payload = bytearray([command, write, value])
        payload += bytearray(10)
        payload += self.device_id
        return payload


    def _get_response(self, interpret=True):
        """Read a 10-byte response from the device."""
        response = self._sd.read(10)
        if interpret:
            response = self.interpret(response)
        return response


    def _interpret_property(self, bytestring):
        """interpret() sub-function: property replies.

        Translate a response packet from property get/set into
        a human-readable dictionary.
        """
        property_switch = {
            0x02: 'mode',
            0x05: 'id',
            0x06: 'active',
            0x07: 'firmware',
            0x08: 'period'
        }
        reply = {'type': property_switch[bytestring[2]]}
        if reply['type'] == 'firmware':
            year = 2000 + bytestring[3]
            month = bytestring[4]
            day = bytestring[5]
            reply['value'] = f'{year}-{month}-{day}'
        else:
            reply['value'] = bytestring[4]
        return reply


    def _interpret_sample(self, bytestring):
        """interpret() sub-function: sample replies.

        Translate a response packet from a sample request into
        a human-readable dictionary.
        """
        reply = {
            'type': 'sample',
            'value': {
                'pm2.5': int.from_bytes(bytestring[2:4], 'little')/10,
                'pm10.0': int.from_bytes(bytestring[4:6], 'little')/10
            }
        }
        return reply


    def _send_command(self, command, write: bool, value: int):
        """Send a command to the device.

        Encapsulates a command, command mode, and command argument in
        a checksummed packet, and sends this to the device.
        Returns return code from device, but not device reply.
        """
        payload = bytearray([command, write, value])
        payload += bytearray(10)
        payload += self.device_id
        checksum = bytes([sum(payload) & 255])
        message = _MSG_HEAD + _MSG_ID + payload + checksum + _MSG_TAIL
        return self._sd.write(message)


    def clear(self):
        """Clear the device buffer."""
        self._sd.reset_input_buffer()


    def interpret(self, bytestring):
        """Translate a raw device response into a dictionary."""
        switch = {
            0xc5: lambda : self._interpret_property(bytestring),
            0xc0: lambda : self._interpret_sample(bytestring),
        }
        reply = switch[bytestring[1]]()
        reply['id'] = bytestring[6:8]
        reply['checksum'] = self._verify_packet(bytestring)
        return reply


    def open(self, port):
        """Open serial port if the instance was created without one."""
        if not self._sd.port:
            self._sd.port = port
            self._sd.open()


    def query(self):
        """Request a sample datum."""
        self._send_command(_CMD_QUERY, 0, 0)
        return self._get_response()

