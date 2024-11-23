# Release Notes: Version 1.0.0

## **Overview**
This release introduces several new features and enhancements to the Ansible Playbook Monitor integration for Home Assistant, focusing on persistence, dynamic updates, and improved functionality.

---

## **New Features**

### **Persistent Storage**
- Added support for storing and restoring sensor entities using Home Assistant's `Store` functionality.
- Ensures sensor entities persist across Home Assistant restarts.

### **Attribute Support for Playbooks**
- Sensors now include additional attributes from webhook data, enhancing visibility and monitoring capabilities.

### **Signal Dispatching**
- Implemented a dynamic signal dispatcher to handle real-time updates for playbook statuses and attributes.

---

## **Enhancements**

### **Improved Webhook Handling**
- Webhook logic updated to validate API keys more robustly.
- Supports parsing and updating of playbook attributes directly from webhook payloads.

### **Notification System**
- Utilizes Home Assistant's `persistent_notification` service for better user feedback during integration setup.
- Displays the generated API key in a notification for easy access.

### **Refined Sensor Management**
- Sensors are now dynamically created and updated based on webhook signals.
- Improved logging for better debugging and traceability of sensor state changes.

---

## **Bug Fixes**
- Fixed minor issues with webhook validation logic.
- Enhanced logging to ensure better error reporting and debugging.

---

## **File Changes Summary**

### **Modified Files**
- `__init__.py`: Added persistent storage and signal dispatching.
- `config_flow.py`: Enhanced notification handling for API key generation.
- `sensor.py`: Improved logic for dynamic sensor creation and attribute updates.



---

Thank you for using Ansible Playbook Monitor. Your feedback is invaluable!

