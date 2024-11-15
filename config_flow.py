from homeassistant import config_entries
import secrets
import voluptuous as vol
from . import DOMAIN


class AnsiblePlaybookMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is None:
            # Display the form to the user
            return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

        # Generate a secure random API key
        api_key = secrets.token_hex(32)

        # Create a persistent notification to show the API key
        self.hass.components.persistent_notification.create(
            f"The API key for this integration is: {api_key}. "
            "Please save it, as it will not be displayed again.",
            title="Ansible Playbook Monitor Setup",
            notification_id=f"{DOMAIN}_api_key",
        )

        # Create the configuration entry with the generated API key
        return self.async_create_entry(
            title="Ansible Playbook Monitor", data={"api_key": api_key}
        )
