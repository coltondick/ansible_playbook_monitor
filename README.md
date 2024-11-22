# Home Assistant Ansible Playbook Monitor

A custom integration for [Home Assistant](https://www.home-assistant.io/) to monitor the status of Ansible playbooks in real-time. This integration provides dynamic sensor creation and updates for each playbook, ensuring you stay informed about their execution status.

## Features

- **Dynamic Sensors**: Automatically creates sensor entities for Ansible playbooks as updates are received.
- **Real-Time Updates**: Reflects the latest status of playbooks (`started`, `completed`, `failed`, etc.).
- **Attributes Support**: Allows additional metadata to be sent with playbook updates, such as stage, datetime, and result.
- **Secure Webhook**: Supports API key validation to ensure only authorized sources can update statuses.
- **Persistent Notifications**: Displays the generated API key during setup for secure access.

## Requirements

- Home Assistant 2023.5 or newer
- A working Ansible environment
- Access to your Home Assistant instance (either via HTTPS or HTTP)

## Installation

### Installation via HACS (Custom Repository)

1. **Install HACS**:

   - If you don’t already have [HACS](https://hacs.xyz/), install it by following the instructions on the HACS website.

2. **Add the Repository as a Custom Integration**:

   - Go to **HACS > Integrations**.
   - Click the **Menu (three dots)** in the top-right corner and select **Custom Repositories**.
   - Add the repository URL:
     ```plaintext
     https://github.com/coltondick/ansible_playbook_monitor
     ```
   - Set the category to **Integration** and click **Add**.

3. **Install the Integration**:

   - After adding the repository, go to **HACS > Integrations > Explore & Add Repositories**.
   - Search for **Ansible Playbook Monitor** and click **Install**.

4. **Restart Home Assistant**:

   - Restart Home Assistant to load the integration.

5. **Add the Integration**:
   - Go to **Settings > Devices & Services > Add Integration**.
   - Search for **Ansible Playbook Monitor** and follow the setup process.
   - Save the API key displayed in the **Notifications** section.

### Manual Installation

1. **Clone or Download the Repository**:

   - Clone the repository or download it as a ZIP file:
     ```bash
     git clone https://github.com/coltondick/ansible_playbook_monitor.git
     ```

2. **Ensure the Folder Structure**:

   - Verify that the folder structure matches the following:
     ```plaintext
     ansible_playbook_monitor/
     ┣ .github/
     ┃ ┗ workflows/
     ┃   ┣ hacs.yml
     ┃   ┗ hassfest.yml
     ┣ custom_components/
     ┃ ┗ ansible_playbook_monitor/
     ┃   ┣ config_flow.py
     ┃   ┣ manifest.json
     ┃   ┣ sensor.py
     ┃   ┣ strings.json
     ┃   ┗ __init__.py
     ┣ .gitignore
     ┣ hacs.json
     ┗ README.md
     ```

3. **Copy the Integration Files**:

   - Copy the contents of the `custom_components/ansible_playbook_monitor/` folder into your Home Assistant `custom_components/` directory:
     ```bash
     cp -r custom_components/ansible_playbook_monitor/ /path/to/home-assistant/config/custom_components/
     ```

4. **Restart Home Assistant**:

   - Restart Home Assistant to load the new integration.

5. **Add the Integration**:
   - Go to **Settings > Devices & Services > Add Integration**.
   - Search for **Ansible Playbook Monitor** and follow the setup process.
   - Save the API key displayed in the **Notifications** section.

## Obtaining the API Key

- After successfully setting up the integration, navigate to the **Notifications** section in Home Assistant.
- You’ll see a notification titled **Ansible Playbook Monitor Setup** containing the generated API key.
- **Important:** Save this key securely, as it will not be shown again.

## Webhook Usage

The integration provides a webhook endpoint to update playbook statuses in Home Assistant. Depending on whether you use HTTP or HTTPS, use the appropriate URL.

### HTTPS Webhook Access

If your Home Assistant instance is accessible via HTTPS (recommended), use the following example:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"playbook": "example_playbook", "status": "completed"}' \
  "https://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
```

### HTTP Webhook Access

If your Home Assistant instance is not configured for HTTPS:

1. Replace `https://` with `http://` in the webhook URL.
2. Ensure your network is secure, as HTTP does not encrypt traffic and exposes your API key.

Example:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"playbook": "example_playbook", "status": "completed"}' \
  "http://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
```

**Warning:** Using HTTP is less secure and exposes sensitive data. It is recommended only for local or trusted networks.

## Example Ansible Playbooks

### Successful Run

```yaml
- name: Notify Home Assistant of Playbook Start
  hosts: localhost
  tasks:
    - name: Notify HA webhook of playbook start
      uri:
        url: "http://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY" # Replace with your actual API key
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "started"}'
        body_format: json

    - name: Run a successful task
      command: echo "This task will succeed"

    - name: Notify HA webhook of playbook completion
      uri:
        url: "http://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY" # Replace with your actual API key
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "completed", "attributes": {"stage": "finalizing", "datetime": "{{ ansible_date_time.iso8601 }}", "result": "success"}}'
        body_format: json
```

### Handling Failures

```yaml
- name: Notify Home Assistant of Playbook Start
  hosts: localhost
  tasks:
    - name: Notify HA webhook of playbook start
      uri:
        url: "http://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY" # Replace with your actual API key
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "started"}'
        body_format: json

    - name: Run a task that might fail
      command: /nonexistent/command
      register: result
      failed_when: result.rc != 0 # Mark the task as failed if the return code is not zero
      ignore_errors: yes # Continue execution even if the task fails

    - block:
        - name: Notify HA webhook of playbook failure
          uri:
            url: "http://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
            method: POST
            headers:
              Authorization: "Bearer YOUR_API_KEY" # Replace with your actual API key
              Content-Type: "application/json"
            body: '{"playbook": "deploy_app", "status": "failed", "attributes": {"stage": "error_handling", "datetime": "{{ ansible_date_time.iso8601 }}", "result": "failure"}}'
            body_format: json
      when: result is defined and result.failed

    - name: Notify HA webhook of playbook completion
      uri:
        url: "http://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY" # Replace with your actual API key
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "completed"}'
        body_format: json
      when: result is defined and not result.failed
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit issues or pull requests for features or bug fixes.
