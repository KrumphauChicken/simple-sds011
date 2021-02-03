# simple-sds011
A minimal library for reading samples from a Nova Fitness SDS011 particulate sensor.


## In a nutshell
```
>>> import simple_sds011
>>> pm = simple_sds011.SDS011('/dev/ttyUSB0')
>>> pm.mode = simple_sds011.MODE_PASSIVE
>>> pm.period
{'type': 'period', 'value': 0, 'id': b'\xcb\xc2', 'checksum': True}
>>> pm.query()
{'type': 'sample', 'value': {'pm2.5': 8.5, 'pm10.0': 12.4}, 'id': b'\xcb\xc2', 'checksum': True}
```


## Quick help

### Writable properties
* SDS011.**active**: Whether the device fan and laser are powered (1) or not (0).
* SDS011.**mode**: Continuous (0) or passive (1) sampling. In continuous mode, the device sends sample data once a second or once a *sample period*. In passive mode, the device only sends sample data when queried.
* SDS011.**period**: The period between air samples. Can be 0 or any value between 1 and 30. The device will sleep for N * 60 - 30 seconds, then take a single sample at the end of a 30-second warm up.


### Read-only properties
* SDS011.**device_id**: A two-byte identifier unique to the sensor.
* SDS011.**firmware**: The device firmware identifier.
* SDS011.**port**: The open serial port the device is attached to.


### Commands
* SDS011.**query()**: Get a dictionary containing the current pm2.5 and pm10.0 levels as read by the sensor.


## Caveats/to-do
* Obviously unfinished and delicate. Most useful in the interactive shell for casual readings.
* Properties are not stored in the instance, but queried to the device. If the device is not active at that moment, an exception is returned. This includes the sleep phase when period != 0.
* The continuous-report mode is not yet supported—only single queries.
* The port and ID cannot be changed.
