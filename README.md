# 🛡️ Resilient Traffic Guardian

### Cyber-Physical Defense for Adaptive Traffic Signals

Resilient Traffic Guardian is a **Streamlit-based traffic-control command dashboard** designed to demonstrate how a cyber-physical traffic-signal system can continue operating safely when its data sources or central control link become unreliable or compromised.

The project combines a **Python/Streamlit dashboard**, an **Arduino Mega 2560**, road sensors, a camera-based vehicle-counting path, and a resilient controller (`traffic_guardian_core.py`). The dashboard presents the controller state, traffic counts, anomaly information, alerts, and hardware connection status in a single operator interface.

---

## ✨ Main Features

- 📊 **Live traffic monitoring** through the controller's camera and road-sensor data.
- 🚦 **Adaptive traffic-signal control** through the resilient guardian controller.
- 🛡️ **Safety checks** for suspicious or unsafe control commands.
- 📡 **Arduino hardware integration** for the physical traffic-light prototype.
- 🚨 **Automatic anomaly alerting** in the dashboard.
- 🔐 **Central-system compromise demonstration**.
- 🔄 **Continuous monitoring** with a 1-second dashboard refresh interval.
- 📷 **Camera vehicle count**.
- 📡 **Road-sensor vehicle count**.
- 🧾 **Alert/history display** for operator visibility.
- 🖥️ Operator-focused interface with the most important system state shown prominently.

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │      Camera Feed      │
                    │  Vehicle Detection   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Resilient Traffic    │
                    │ Guardian Controller  │
                    │ traffic_guardian_core│
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │ Road Sensors    │        │ Arduino Mega    │
        │ IR Sensor Data  │        │ 2560            │
        └─────────────────┘        └────────┬────────┘
                                            │
                         ┌──────────────────┼──────────────────┐
                         ▼                  ▼                  ▼
                  Traffic Lights        Buzzer          Warning LED

                               │
                               ▼
                    ┌──────────────────────┐
                    │ Streamlit Dashboard  │
                    │ Command Center       │
                    └──────────────────────┘
```

The dashboard is the operator-facing layer. The controller is responsible for interpreting the live inputs and applying its safety logic before hardware actions are taken.

---

## 🔌 Hardware Setup

The prototype is based on an **Arduino Mega 2560**.

| Component | Arduino Pin |
|---|---:|
| Buzzer | D6 |
| Warning LED | D7 |
| IR Sensor 1 | D2 |
| IR Sensor 2 | D3 |
| Traffic Light 1 Green | D8 |
| Traffic Light 1 Yellow | D9 |
| Traffic Light 1 Red | D10 |
| Traffic Light 2 Green | D11 |
| Traffic Light 2 Yellow | D12 |
| Traffic Light 2 Red | D13 |
| Camera | USB → Computer |

The buzzer and warning LED are intended to provide physical indication of an alert condition, while the traffic-light outputs represent the intersection state.

> **Hardware note:** The dashboard uses the existing guardian attack path for the automatic compromise demonstration. Actual buzzer behavior depends on the implementation of `traffic_guardian_core.py` and the Arduino firmware.

---

## 📁 Project Structure

A typical project directory should contain:

```text
Resilient-Traffic-Guardian/
│
├── dashboard_anomaly_auto_1to4.py   # Main Streamlit dashboard
├── traffic_guardian_core.py         # Controller / resilience logic
├── arduino_traffic_controller.ino            # Arduino Mega firmware
├── README.md                         # Project documentation
└── requirements.txt                  # Python dependencies (recommended)
```

The exact Arduino firmware filename may differ depending on the project version.

---

## 🧰 Software Requirements

Recommended environment:

- Python 3.9+
- Streamlit
- Pandas
- Arduino IDE
- Arduino Mega 2560
- USB connection between Arduino and computer
- A compatible camera/webcam

Install the Python packages used by the dashboard with:

```bash
pip install streamlit pandas
```

If `traffic_guardian_core.py` has additional dependencies, install those as required by that module.

---

## 🚀 Running the Dashboard

1. Connect the Arduino Mega 2560 to the computer.
2. Confirm the Arduino's serial port. The current dashboard configuration uses:

```python
ARDUINO_PORT = "COM4"
```

   Change this value if Windows assigns a different COM port, or if you are running on Linux/macOS.

3. Make sure `traffic_guardian_core.py` is in the same project directory as the dashboard.
4. Connect the camera and upload the required Arduino firmware.
5. Open a terminal in the project directory.
6. Start Streamlit:

```bash
streamlit run dashboard_anomaly_auto_1to4.py
```

7. Open the local Streamlit address shown in the terminal, normally:

```text
http://localhost:8501
```

---

The implementation calls the controller's existing:

```python
guardian.trigger_attack("malicious_command")
```

after approximately five minutes of dashboard runtime.

This is intended as a **controlled project demonstration**, not as a real attack mechanism.

---

## 🛡️ Resilience and Anomaly Handling

The dashboard can surface several controller conditions, including:

- Normal operation
- Unsafe control commands
- Sensor/camera inconsistencies
- Traffic behavior anomalies
- Loss of central control communication
- Safe-mode operation
- The timed central-system compromise demonstration

When a non-normal condition is detected, the dashboard presents an alert rather than silently continuing as though everything is fine. Humanity has apparently decided traffic lights need cybersecurity too, so here we are.

---

## 🔔 Alerting

The dashboard provides:

- A prominent top-level system status.
- Active anomaly messaging.
- Alert/history information.
- Automatic refresh.
- Hardware/software communication error reporting.
  
The exact physical response, including buzzer activation, is determined by the connected controller and Arduino firmware.

---

## ⚠️ Important Limitations

- `traffic_guardian_core.py` is required for the dashboard to operate.
- The Arduino firmware is required for physical hardware behavior.
- The dashboard alone cannot guarantee that the buzzer sounds unless the controller/firmware implements the corresponding command.
- The camera count is dependent on the project's camera-processing implementation.
- The configured serial port (`COM4`) may need to be changed on another computer.

---

## 🔧 Troubleshooting

### Arduino is not detected

Check:

- USB cable connection.
- Arduino IDE serial-port selection.
- Windows Device Manager for the assigned COM port.
- `ARDUINO_PORT` in the dashboard.
- Whether another program is already using the serial port.

### Dashboard cannot import `traffic_guardian_core`

Ensure this file is located beside the dashboard:

```text
traffic_guardian_core.py
```

Then restart Streamlit.

### Camera count is not updating

Check the camera connection and the camera-processing implementation used by `traffic_guardian_core.py`.

### Buzzer does not activate during the demo

The dashboard triggers the guardian's `malicious_command` attack path, but physical buzzer behavior is not guaranteed by the dashboard code alone. Verify the Arduino firmware and the corresponding controller-to-Arduino command handling.

### Streamlit does not start

Try:

```bash
python -m pip install --upgrade streamlit pandas
streamlit run dashboard_anomaly_auto_1to4.py
```

---

## 🎯 Project Objective

The project demonstrates a resilient **cyber-physical traffic-control architecture** in which traffic information from multiple sources is monitored, suspicious conditions are detected, and the operator is given a clear indication when the system enters an abnormal state.

The central idea is:

> **Verify traffic data and control commands before allowing them to influence a physical traffic intersection.**

This connects cybersecurity, embedded systems, computer vision, sensor fusion, and intelligent traffic management in one demonstrable prototype.

---

## 📌 Current Build Summary

| Feature | Current Status |
|---|---|
| Streamlit dashboard | ✅ Implemented |
| Arduino Mega 2560 integration | ✅ Configured |
| Automatic monitoring | ✅ Enabled |
| Manual attack buttons | ❌ Removed in demo build |
| Alert display | ✅ Implemented |
| Hardware buzzer | ⚠️ Depends on controller/firmware |
| Traffic-light hardware | ✅ Prototype wiring documented |
| `traffic_guardian_core.py` | Required |

---

## 📜 License

Add the project's chosen license here if required by your institution or project team.

```text
License: _________________________________
```
