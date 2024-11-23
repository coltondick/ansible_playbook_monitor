from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN, DISPATCHER_SIGNAL
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor entities dynamically from the integration."""
    _LOGGER.debug("Setting up sensor entry with config: %s", config_entry)

    entities = hass.data[DOMAIN]["entities"]
    save_entities = hass.data[DOMAIN]["save_entities"]
    all_sensors = hass.data[DOMAIN].setdefault("all_sensors", [])

    async def handle_playbook_update(playbook, status, attributes=None):
        """Handle updates to playbook status."""
        _LOGGER.debug(
            "Updating playbook %s with status %s and attributes %s",
            playbook,
            status,
            attributes,
        )

        # Check if the sensor already exists
        sensor = next(
            (sensor for sensor in all_sensors if sensor.playbook == playbook), None
        )

        if sensor is None:
            # Create a new sensor if it does not exist
            _LOGGER.debug("Creating new sensor for playbook: %s", playbook)
            sensor = AnsiblePlaybookSensor(playbook, status, attributes)
            all_sensors.append(sensor)
            entities[playbook] = {"status": status, "attributes": attributes or {}}
            async_add_entities([sensor])
        else:
            # Update the existing sensor
            _LOGGER.debug("Updating existing sensor for playbook: %s", playbook)
            sensor.update_state(status, attributes)
            entities[playbook].update(
                {"status": status, "attributes": attributes or {}}
            )

        await save_entities()

    # Restore existing sensors
    for playbook, data in entities.items():
        _LOGGER.debug("Restoring sensor for playbook: %s with data: %s", playbook, data)
        sensor = AnsiblePlaybookSensor(playbook, data["status"], data.get("attributes"))
        all_sensors.append(sensor)
        async_add_entities([sensor])

    # Connect to dispatcher signal
    _LOGGER.debug("Connecting to dispatcher signal: %s", DISPATCHER_SIGNAL)
    async_dispatcher_connect(hass, DISPATCHER_SIGNAL, handle_playbook_update)


class AnsiblePlaybookSensor(SensorEntity):
    """Sensor representing an Ansible playbook."""

    def __init__(self, playbook, status, attributes):
        _LOGGER.debug(
            "Initializing sensor for playbook: %s with status: %s and attributes: %s",
            playbook,
            status,
            attributes,
        )
        self.playbook = playbook
        self._state = status
        self._attributes = attributes

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{DOMAIN}_{self.playbook}"

    @property
    def name(self):
        return f"Ansible Playbook {self.playbook}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    def update_state(self, status, attributes):
        _LOGGER.debug(
            "Updating state for sensor %s to status: %s with attributes: %s",
            self.name,
            status,
            attributes,
        )
        self._state = status
        self._attributes = attributes
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Run when entity is added to Home Assistant."""
        _LOGGER.debug("Sensor %s added to Home Assistant.", self.name)

    async def async_will_remove_from_hass(self):
        """Run when entity is about to be removed from Home Assistant."""
        _LOGGER.debug("Sensor %s will be removed from Home Assistant.", self.name)
