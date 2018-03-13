"""
Support for ThermoPi thermostats.

For more details about this platform, please refer to the documentation at
https://github.com/groupwhere/homeassistant-thermopi
"""
import logging
from socket import timeout
import datetime
import json
import urllib
from urllib.error import HTTPError,URLError

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import (
    ClimateDevice, PLATFORM_SCHEMA, ATTR_FAN_MODE, ATTR_FAN_LIST,
    ATTR_OPERATION_MODE, ATTR_OPERATION_LIST, SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_AWAY_MODE, SUPPORT_OPERATION_MODE)
from homeassistant.const import (
    CONF_PASSWORD, CONF_USERNAME, TEMP_CELSIUS, TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE, CONF_REGION, CONF_HOST, CONF_PORT, CONF_NAME, CONF_DEVICE)

_LOGGER = logging.getLogger(__name__)

DEVICE_DEFAULT_NAME = 'ThermoPi'
DEFAULT_NAME = 'ThermoPi'
DEFAULT_PORT = 88
DEFAULT_DEVICE = '0'
DEFAULT_UNITS = 'F'
TEMP_UNITS = ['F', 'C']

ATTR_FAN = 'fan'
ATTR_SYSTEM_MODE = 'system_mode'
ATTR_CURRENT_OPERATION = 'equipment_output_status'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_DEVICE, default=DEFAULT_DEVICE): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.string,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the ThermoPi thermostat."""
    name     = config.get(CONF_NAME)
    host     = config.get(CONF_HOST)
    port     = config.get(CONF_PORT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    device = 0

    return _setup(host, port, device, name, username, password, config, add_devices)

# config will be used later
def _setup(host, port, device, name, username, password, config, add_devices):
    add_devices([ThermoPiThermostat(host, port, device, name, username, password)])

    return True

class ThermoPiThermostat(ClimateDevice):
    """Representation of a ThermoPi Thermostat."""

    def __init__(self, host, port, device, name, username, password):
        """Initialize the thermostat."""
        self.debug = True
        self._name = name
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._device = {}

        self.update()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        supported = (SUPPORT_TARGET_TEMPERATURE & SUPPORT_AWAY_MODE & SUPPORT_OPERATION_MODE)

        return supported

    @property
    def is_fan_on(self):
        """Return true if fan is on."""
        return self._device['fan']

    @property
    def name(self):
        """Return the name of the thermopi, if any."""
        return self._device['name']

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return (TEMP_CELSIUS if self._device['units'] == 'C'
                else TEMP_FAHRENHEIT)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self._device['temp'])

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device['targetTemp']
#        if self._device['runmode'] == 'cool':
#            return self._device.setpoint_cool
#        return self._device.setpoint_heat

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        oper = self._device['runmode']
        if self._device['schedule']:
            active = 'off'
            if self._device['schedule']['active'] == 'True':
                active = 'on'
            oper = oper + '(' + self._device['schedule']['name'] + '[' + active + '])'
        return oper

    def get_schedule(self):
        # Return currently active schedule and whether enabled
        host = 'http://' + self._host + ':' + str(self._port) + '/api/schedule'
        header = {'content-type': 'application/json'}

        _LOGGER.warning("Connecting to: %s", host)

        try:
            req = urllib.request.Request(url=host, headers=header, method='GET')
            res = urllib.request.urlopen(req, timeout=10)

            rawrtrn = res.read().decode('utf8')
            rtrn = json.loads(rawrtrn)

            _LOGGER.warning("Status: %s", rtrn)
            return rtrn['schedule']
        except timeout:
            if self.debug:
                _LOGGER.warning("Connection timed out...")

    def get_schedules(self, name=''):
        # Return details of all or namesd schedule
        # http://192.168.1.79:88/api/schedules/?name=Weekend LIST ONLY NAMED SCHEDULE
        # http://192.168.1.79:88/api/schedules/ LIST ALL
        host = 'http://' + self._host + ':' + str(self._port) + '/api/schedules/'
        if name:
            host = host + '?name=' + name
        header = {'content-type': 'application/json'}

        _LOGGER.warning("Connecting to: %s", host)

        try:
            req = urllib.request.Request(url=host, headers=header, method='GET')
            res = urllib.request.urlopen(req, timeout=10)

            rawrtrn = res.read().decode('utf8')
            rtrn = json.loads(rawrtrn)

            _LOGGER.warning("Status: %s", rtrn)
        except (HTTPError, URLError) as error:
            _LOGGER.error("Connection error...")
        except timeout:
            if self.debug:
                _LOGGER.warning("Connection timed out...")

    def update(self):
        host = 'http://' + self._host + ':' + str(self._port) + '/api/'
        header = {'content-type': 'application/json'}

        _LOGGER.warning("Connecting to: %s", self._host)

        try:
            req = urllib.request.Request(url=host, headers=header, method='GET')
            res = urllib.request.urlopen(req, timeout=10)

            rawrtrn = res.read().decode('utf8')
            rtrn = json.loads(rawrtrn)

            #_LOGGER.warning("Status: %s", rtrn)
            #Status: {'status': [{'fan': True, 'temp': 77, 'targetTemp': 80, 'heat': False, 'cool': False, 'runmode': 'heat'}]}

            tmp = rtrn['status']
            self._device = tmp[0]
            schedule = self.get_schedule()
            tmp = schedule[0]
            self._device['schedule'] = tmp

            _LOGGER.warning("Status: %s", self._device)
            self._device['name'] = self._name
        except (HTTPError, URLError) as error:
            _LOGGER.error("Connection error...")
        except timeout:
            if self.debug:
                _LOGGER.warning("Connection timed out...")

    def set_temperature(self, **kwargs):
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        host = 'http://' + self._host + ':' + str(self._port) + '/api/'
        header = {'content-type': 'application/json'}

        _LOGGER.warning("Connecting to: %s", self._host)

        try:
            query = '?mode=' + self._device['runmode'] + '&temp=' + temperature
            req = urllib.request.Request(url=host + query, headers=header, method='GET')
            res = urllib.request.urlopen(req, timeout=20)

            rawrtrn = res.read().decode('utf8')
            rtrn = json.loads(rawrtrn)

            tmp = rtrn['status']
            self._device = tmp[0]
            _LOGGER.warning("Status: %s", self._device)
            self._device['name'] = self._name
        except (HTTPError, URLError) as error:
            _LOGGER.error("Connection error...")
        except timeout:
            if self.debug:
                _LOGGER.warning("Connection timed out...")

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
#        data = {
#            ATTR_FAN: (self.is_fan_on and 'running' or 'idle'),
#            ATTR_FAN_MODE: self._device.fan_mode,
#            ATTR_OPERATION_MODE: self._device['runmode'],
#        }
#        data[ATTR_FAN_LIST] = somecomfort.FAN_MODES
#        data[ATTR_OPERATION_LIST] = somecomfort.SYSTEM_MODES
#        return data

    @property
    def is_away_mode_on(self):
        """Return true if away mode is on."""
        return self._away

    def turn_away_mode_on(self):
        """Turn away on.

        Somecomfort does have a proprietary away mode, but it doesn't really
        work the way it should. For example: If you set a temperature manually
        it doesn't get overwritten when away mode is switched on.
        """
        self._away = True
#        import somecomfort
#        try:
#            # Get current mode
#            mode = self._device['runmode']
#        except somecomfort.SomeComfortError:
#            _LOGGER.error('Can not get system mode')
#            return
#        try:
#
#            # Set permanent hold
#            setattr(self._device,
#                    "hold_{}".format(mode),
#                    True)
#            # Set temperature
#            setattr(self._device,
#                    "setpoint_{}".format(mode),
#                    getattr(self, "_{}_away_temp".format(mode)))
#        except somecomfort.SomeComfortError:
#            _LOGGER.error('Temperature %.1f out of range',
#                          getattr(self, "_{}_away_temp".format(mode)))

    def turn_away_mode_off(self):
        """Turn away off."""
        self._away = False
#        import somecomfort
#        try:
#            # Disabling all hold modes
#            self._device.hold_cool = False
#            self._device.hold_heat = False
#        except somecomfort.SomeComfortError:
#            _LOGGER.error('Can not stop hold mode')

    def set_operation_mode(self):
        """Set the system mode (Cool, Heat, etc)."""
        if hasattr(self._device, ATTR_SYSTEM_MODE):
            self._device.system_mode = operation_mode

#    def update(self):
#        """Update the state."""
#        import somecomfort
#        retries = 3
#        while retries > 0:
#            try:
#                self._device.refresh()
#                break
#            except (somecomfort.client.APIRateLimited, OSError,
#                    requests.exceptions.ReadTimeout) as exp:
#                retries -= 1
#                if retries == 0:
#                    raise exp
#                if not self._retry():
#                    raise exp
#                _LOGGER.error(
#                    "SomeComfort update failed, Retrying - Error: %s", exp)

    def _retry(self):
        """Recreate a new somecomfort client.

#        When we got an error, the best way to be sure that the next query
#        will succeed, is to recreate a new somecomfort client.
#        """
#        import somecomfort
#        try:
#            self._client = somecomfort.SomeComfort(
#                self._username, self._password)
#        except somecomfort.AuthError:
#            _LOGGER.error("Failed to login to thermopi account %s",
#                          self._username)
#            return False
#        except somecomfort.SomeComfortError as ex:
#            _LOGGER.error("Failed to initialize thermopi client: %s",
#                          str(ex))
#            return False
#
#        devices = [device
#                   for location in self._client.locations_by_id.values()
#                   for device in location.devices_by_id.values()
#                   if device.name == self._device.name]
#
#        if len(devices) != 1:
#            _LOGGER.error("Failed to find device %s", self._device.name)
#            return False
#
#        self._device = devices[0]
#        return True
