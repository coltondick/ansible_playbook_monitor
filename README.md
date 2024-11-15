# Home Assistant Ansible Playbook Monitor

A custom integration for [Home Assistant](https://www.home-assistant.io/) to monitor the status of Ansible playbooks in real-time. This integration provides dynamic sensor creation and updates for each playbook, ensuring you stay informed about their execution status.

## Features

- **Dynamic Sensors**: Automatically creates sensor entities for Ansible playbooks as updates are received.
- **Real-Time Updates**: Reflects the latest status of playbooks (`started`, `completed`, `failed`, etc.).
- **Secure Webhook**: Enforces API key validation to ensure only authorized sources can update statuses.
- **Persistent Notifications**: Displays the generated API key during setup for secure access.

## Requirements

- Home Assistant 2023.5 or newer
- A working Ansible environment
- An HTTPS-accessible Home Assistant instance for the webhook

## Installation

### Installation via HACS

1. Ensure that you have [HACS](https://hacs.xyz/) installed in your Home Assistant setup.
2. Go to **HACS > Integrations**.
3. Click the **Menu (three dots)** in the top-right corner and select **Custom Repositories**.
4. Add this repository URL:
   ```
   https://github.com/coltondick/ansible_playbook_monitor
   ```
5. Set the category to **Integration** and click **Add**.
6. Go to **HACS > Integrations > Explore & Add Repositories**, search for **Ansible Playbook Monitor**, and click **Install**.
7. Restart Home Assistant.
8. Add the integration via **Settings > Devices & Services > Add Integration** and search for **Ansible Playbook Monitor**.
9. Save the API key displayed in the **Notifications** section of Home Assistant after setup.

### Manual Installation

1. Clone this repository into your Home Assistant `custom_components` directory:

   ```bash
   git clone https://github.com/coltondick/ansible_playbook_monitor.git custom_components/ansible_playbook_monitor
   ```

2. Restart Home Assistant.

3. Add the integration via **Settings > Devices & Services > Add Integration**.

4. Save the API key displayed in the **Notifications** section of Home Assistant after setup.

## Obtaining the API Key

- After successfully setting up the integration, navigate to the **Notifications** section in Home Assistant.
- You’ll see a notification titled **Ansible Playbook Monitor Setup** containing the generated API key.
- **Important:** Save this key securely, as it will not be shown again.

## Webhook Example

Send status updates to the integration using a POST request:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"playbook": "example_playbook", "status": "completed"}' \
  "https://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
```

Replace `YOUR_API_KEY` with the API key obtained from the notification and `your-home-assistant-instance` with your Home Assistant URL.

### Updating the `example_playbook` Placeholder

- Replace `example_playbook` in the `playbook` field with the **name of your Ansible playbook**.
- This name will be used to create a sensor entity in Home Assistant with the ID `sensor.<playbook>_playbook_status`.
- Example:
  - If your playbook is named `deploy_app`, the sensor will be created as `sensor.deploy_app_playbook_status`.

## Example Ansible Playbooks

### Successful Run

```yaml
- name: Notify Home Assistant of Playbook Start
  hosts: localhost
  tasks:
    - name: Notify HA webhook of playbook start
      uri:
        url: "https://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY"
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "started"}'
        body_format: json

    - name: Run a successful task
      command: echo "This task will succeed"

    - name: Notify HA webhook of playbook completion
      uri:
        url: "https://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY"
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "completed"}'
        body_format: json
```

### Handling Failures

```yaml
- name: Notify Home Assistant of Playbook Start
  hosts: localhost
  tasks:
    - name: Notify HA webhook of playbook start
      uri:
        url: "https://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY"
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "started"}'
        body_format: json

    - name: Run a task that might fail
      command: /nonexistent/command
      register: result
      ignore_errors: yes

    - block:
        - name: Notify HA webhook of playbook failure
          uri:
            url: "https://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
            method: POST
            headers:
              Authorization: "Bearer YOUR_API_KEY"
              Content-Type: "application/json"
            body: '{"playbook": "deploy_app", "status": "failed"}'
            body_format: json
      when: result.failed

    - name: Notify HA webhook of playbook completion
      uri:
        url: "https://your-home-assistant-instance/api/webhook/ansible_playbook_monitor_webhook"
        method: POST
        headers:
          Authorization: "Bearer YOUR_API_KEY"
          Content-Type: "application/json"
        body: '{"playbook": "deploy_app", "status": "completed"}'
        body_format: json
      when: not result.failed
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit issues or pull requests for features or bug fixes.
