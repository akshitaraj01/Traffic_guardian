"""
RESILIENT TRAFFIC GUARDIAN — Core Logic
----------------------------------------
This file contains everything except the visual dashboard:

  1. TrafficSimulator   -> fakes camera_count / sensor_count / historical data
  2. SensorValidator     -> Layer 1: do two independent sources agree?
  3. BehaviorEngine      -> Layer 2: does this traffic make sense right now?
  4. SafetyEngine        -> Layer 3: is the proposed command physically safe?
  5. TrustScoreCalculator-> combines all of the above into one 0-100 number
  6. ArduinoLink         -> talks to the Arduino over USB serial
                            (falls back to a "simulated" mode with no
                             hardware attached, so you can develop/demo
                             the software before your hardware is ready)
  7. ResilientTrafficGuardian -> orchestrates one full control-loop "tick"

Run this file directly for a quick command-line test:
    python traffic_guardian_core.py
"""

import random
import time
from dataclasses import dataclass, field


# =====================================================================
# 1. TRAFFIC SIMULATOR
# =====================================================================
class TrafficSimulator:
    """Generates realistic vehicle counts for Road A and Road B, and
    lets us inject each of the three attacks on demand."""

    def __init__(self):
        # Historical baseline: "typical" vehicle count by hour of day.
        # In a real deployment this would come from a CSV/SQLite log of
        # past traffic. For the demo we hard-code a believable pattern.
        self.hourly_baseline = {
            8: 90, 9: 100, 13: 60, 17: 95, 18: 110, 20: 40, 22: 15,
        }
        self.default_baseline = 55

        self.attack_mode = None   # None | "camera_spoof" | "malicious_command" | "server_down"
        self._tick = 0

    def get_baseline(self, hour=None):
        hour = hour if hour is not None else time.localtime().tm_hour
        return self.hourly_baseline.get(hour, self.default_baseline)

    def trigger_attack(self, attack_name):
        self.attack_mode = attack_name

    def clear_attack(self):
        self.attack_mode = None

    def read_sensors(self):
        """Returns (camera_count, sensor_count, requested_command, baseline, road_b_count)
        for the intersection. Road B is a second, independent approach — kept
        free of attacks so the contrast in the demo is obvious, and so the
        vehicle-count comparison between the two roads is meaningful."""
        self._tick += 1
        baseline = self.get_baseline()
        true_count = max(0, int(random.gauss(baseline, baseline * 0.08)))

        camera_count = true_count + random.randint(-3, 3)
        sensor_count = true_count + random.randint(-3, 3)
        requested_green_a = None  # None = "use normal adaptive logic"

        # Road B's own, independent traffic volume — usually lighter than Road A.
        road_b_baseline = max(10, int(baseline * 0.4))
        road_b_count = max(0, int(random.gauss(road_b_baseline, road_b_baseline * 0.15)))

        if self.attack_mode == "camera_spoof":
            camera_count = random.randint(0, 2)   # camera lies: "almost nobody here"
        elif self.attack_mode == "malicious_command":
            requested_green_a = 999  # a compromised "central server" demands 999s green
        elif self.attack_mode == "server_down":
            requested_green_a = "__NO_RESPONSE__"  # simulates the central server not answering

        return camera_count, sensor_count, requested_green_a, baseline, road_b_count


# =====================================================================
# 2. LAYER 1 — SENSOR VALIDATOR (multi-modal cross-check)
# =====================================================================
@dataclass
class ValidationResult:
    ok: bool
    difference: int
    reason: str
    bypassed_source: str = None   # "camera" | "sensor" | None — which feed was distrusted
    trusted_source: str = None    # the source relied on instead


class SensorValidator:
    def __init__(self, mismatch_threshold=15):
        self.mismatch_threshold = mismatch_threshold

    def check(self, camera_count, sensor_count):
        diff = abs(camera_count - sensor_count)
        if diff > self.mismatch_threshold:
            # The lower reading is treated as the compromised one — a real attack
            # here almost always under-reports (to hide vehicles from the system),
            # so we trust whichever source is reporting the more plausible (higher) count.
            if camera_count < sensor_count:
                bypassed, trusted = "camera", "sensor"
            else:
                bypassed, trusted = "sensor", "camera"
            return ValidationResult(
                ok=False,
                difference=diff,
                reason=f"Camera reported {camera_count}, road sensor reported "
                       f"{sensor_count} (diff={diff} > threshold={self.mismatch_threshold}).",
                bypassed_source=bypassed,
                trusted_source=trusted,
            )
        return ValidationResult(ok=True, difference=diff, reason="Sensors agree.")


# =====================================================================
# 3. LAYER 2 — BEHAVIOUR ENGINE (does this match history?)
# =====================================================================
@dataclass
class BehaviorResult:
    ok: bool
    reason: str


class BehaviorEngine:
    def __init__(self, allowed_deviation_ratio=0.5):
        self.allowed_deviation_ratio = allowed_deviation_ratio

    def check(self, reported_count, baseline):
        allowed = baseline * self.allowed_deviation_ratio
        low, high = baseline - allowed, baseline + allowed
        if reported_count < low or reported_count > high:
            return BehaviorResult(
                ok=False,
                reason=f"Expected roughly {int(low)}-{int(high)} vehicles for this "
                       f"time of day, received {reported_count}."
            )
        return BehaviorResult(ok=True, reason="Traffic matches historical pattern.")


# =====================================================================
# 4. LAYER 3 — SAFETY ENGINE (is the requested command physically safe?)
# =====================================================================
@dataclass
class SafetyResult:
    ok: bool
    applied_seconds: int
    reason: str


class SafetyEngine:
    MIN_GREEN = 5
    MAX_GREEN = 45

    def check(self, requested_seconds):
        if requested_seconds is None:
            return SafetyResult(True, None, "No override requested; adaptive logic applies.")
        clamped = max(self.MIN_GREEN, min(self.MAX_GREEN, requested_seconds))
        if clamped != requested_seconds:
            return SafetyResult(
                ok=False,
                applied_seconds=clamped,
                reason=f"Requested {requested_seconds}s green is outside the safe "
                       f"range [{self.MIN_GREEN}-{self.MAX_GREEN}]s. Clamped to {clamped}s."
            )
        return SafetyResult(True, clamped, "Command within safe bounds.")


# =====================================================================
# 5. TRUST SCORE
# =====================================================================
def compute_trust_score(sensor_ok, behavior_ok, safety_ok):
    """40% sensor agreement + 30% historical consistency + 30% command safety."""
    score = 0
    score += 40 if sensor_ok else 0
    score += 30 if behavior_ok else 0
    score += 30 if safety_ok else 0
    return score


# =====================================================================
# 5b. LOCAL LIGHT SIMULATOR (pure software — no hardware needed)
# =====================================================================
class LocalLightSimulator:
    """Mirrors the Arduino traffic-light state machine entirely in software,
    so the dashboard can display working 'traffic lights' before any
    hardware is wired up. Same states, same safety clamping logic."""

    YELLOW_S = 2
    ALL_RED_S = 1
    DEFAULT_GREEN_S = 15
    MIN_GREEN_S = SafetyEngine.MIN_GREEN
    MAX_GREEN_S = SafetyEngine.MAX_GREEN
    STATES = ["A_GREEN", "A_YELLOW", "ALL_RED_1", "B_GREEN", "B_YELLOW", "ALL_RED_2"]

    def __init__(self):
        self.state = "A_GREEN"
        self.state_start = time.time()
        self.green_a = self.DEFAULT_GREEN_S
        self.green_b = self.DEFAULT_GREEN_S
        self.safe_mode = False

    def set_greens(self, green_a, green_b):
        self.green_a = max(self.MIN_GREEN_S, min(self.MAX_GREEN_S, green_a))
        self.green_b = max(self.MIN_GREEN_S, min(self.MAX_GREEN_S, green_b))

    def enter_safe_mode(self):
        self.safe_mode = True
        self.green_a = self.DEFAULT_GREEN_S
        self.green_b = self.DEFAULT_GREEN_S

    def leave_safe_mode(self):
        self.safe_mode = False

    def advance(self):
        durations = {
            "A_GREEN": self.green_a, "A_YELLOW": self.YELLOW_S,
            "ALL_RED_1": self.ALL_RED_S, "B_GREEN": self.green_b,
            "B_YELLOW": self.YELLOW_S, "ALL_RED_2": self.ALL_RED_S,
        }
        if time.time() - self.state_start >= durations[self.state]:
            idx = self.STATES.index(self.state)
            self.state = self.STATES[(idx + 1) % len(self.STATES)]
            self.state_start = time.time()
        return self.state

    def time_remaining(self):
        durations = {
            "A_GREEN": self.green_a, "A_YELLOW": self.YELLOW_S,
            "ALL_RED_1": self.ALL_RED_S, "B_GREEN": self.green_b,
            "B_YELLOW": self.YELLOW_S, "ALL_RED_2": self.ALL_RED_S,
        }
        elapsed = time.time() - self.state_start
        return max(0, round(durations[self.state] - elapsed))

    def light_colors(self):
        """Returns (road_a_color, road_b_color), each 'red'/'yellow'/'green'."""
        mapping = {
            "A_GREEN": ("green", "red"), "A_YELLOW": ("yellow", "red"),
            "ALL_RED_1": ("red", "red"), "B_GREEN": ("red", "green"),
            "B_YELLOW": ("red", "yellow"), "ALL_RED_2": ("red", "red"),
        }
        return mapping[self.state]


# =====================================================================
# 6. ARDUINO LINK  (works with or without real hardware attached)
# =====================================================================
class ArduinoLink:
    def __init__(self, port=None, baud=9600):
        self.simulated = True
        self.serial = None
        if port:
            try:
                import serial  # pyserial
                self.serial = serial.Serial(port, baud, timeout=1)
                time.sleep(2)  # allow Arduino to reset after opening the port
                self.simulated = False
            except Exception as e:
                print(f"[ArduinoLink] Could not open {port} ({e}). "
                      f"Running in SIMULATED hardware mode.")

    def send_heartbeat(self):
        if self.simulated:
            return
        self.serial.write(b"HEARTBEAT\n")

    def send_set(self, green_a, green_b):
        if self.simulated:
            print(f"[SIMULATED ARDUINO] would send SET,{green_a},{green_b}")
            return None
        self.serial.write(f"SET,{green_a},{green_b}\n".encode())
        return self._read_response()

    def _read_response(self):
        if self.simulated or self.serial is None:
            return None
        line = self.serial.readline().decode(errors="ignore").strip()
        return line or None


# =====================================================================
# 7. ORCHESTRATOR
# =====================================================================
@dataclass
class TickResult:
    camera_count: int
    sensor_count: int
    baseline: int
    sensor_check: ValidationResult
    behavior_check: BehaviorResult
    safety_check: SafetyResult
    trust_score: int
    mode: str          # "NORMAL" | "DEGRADED" | "SAFE_MODE"
    arduino_response: str = None
    road_a_color: str = "red"
    road_b_color: str = "red"
    seconds_remaining: int = 0
    road_b_count: int = 0
    green_a_applied: int = 0
    green_b_applied: int = 0
    signal_decision_reason: str = ""
    log: list = field(default_factory=list)


class ResilientTrafficGuardian:
    def __init__(self, arduino_port=None):
        self.simulator = TrafficSimulator()
        self.validator = SensorValidator()
        self.behavior = BehaviorEngine()
        self.safety = SafetyEngine()
        self.arduino = ArduinoLink(port=arduino_port)
        self.lights = LocalLightSimulator()  # software-only visual, works with no hardware
        self.history = []  # keep last N ticks for the dashboard chart/log

    def trigger_attack(self, name):
        self.simulator.trigger_attack(name)

    def clear_attack(self):
        self.simulator.clear_attack()

    def tick(self):
        camera_count, sensor_count, requested_green, baseline, road_b_count = self.simulator.read_sensors()

        server_down = (requested_green == "__NO_RESPONSE__")
        if server_down:
            requested_green = None  # nothing to validate; server just isn't talking

        sensor_result = self.validator.check(camera_count, sensor_count)
        # Trust the sensor with the larger, more plausible count when they disagree.
        trusted_count = max(camera_count, sensor_count) if not sensor_result.ok else sensor_count
        behavior_result = self.behavior.check(trusted_count, baseline)
        safety_result = self.safety.check(requested_green)

        trust = compute_trust_score(sensor_result.ok, behavior_result.ok, safety_result.ok)

        if server_down:
            trust = 0  # no central link at all -> zero trust in the central command path
            mode = "SAFE_MODE"
            arduino_response = "WARN,ENTERED_SAFE_MODE,central_server_silent (simulated)"
            self.lights.enter_safe_mode()
            green_a, green_b = self.lights.DEFAULT_GREEN_S, self.lights.DEFAULT_GREEN_S
            reason = ("Central link is down, so the intersection is not comparing live "
                      "vehicle counts right now — it's running a fixed, pre-approved "
                      "timing on its own until the link is restored.")
        else:
            self.arduino.send_heartbeat()
            if requested_green is not None:
                # An explicit override command was requested (possibly unsafe) — honor
                # the safety-clamped value for Road A, keep Road B on its own share.
                green_a = safety_result.applied_seconds
                green_b = self._adaptive_green(road_b_count)
                reason = (f"An override command requested Road A's green time directly "
                          f"(applied at {green_a}s after safety clamping) rather than "
                          f"the normal vehicle-count comparison.")
            else:
                green_a, green_b = self._proportional_greens(trusted_count, road_b_count)
                if trusted_count > road_b_count:
                    winner, w_count, loser, l_count, w_g, l_g = (
                        "Main Street", trusted_count, "Cross Street", road_b_count, green_a, green_b)
                elif road_b_count > trusted_count:
                    winner, w_count, loser, l_count, w_g, l_g = (
                        "Cross Street", road_b_count, "Main Street", trusted_count, green_b, green_a)
                else:
                    winner = None
                if winner:
                    reason = (f"{winner} has more traffic right now ({w_count} vehicles vs "
                              f"{l_count} on {loser}), so it gets a longer green "
                              f"({w_g}s vs {l_g}s) — busier direction, more time to clear.")
                else:
                    reason = (f"Both directions have similar traffic ({trusted_count} vs "
                              f"{road_b_count} vehicles), so green time is split evenly "
                              f"({green_a}s / {green_b}s).")

            arduino_response = self.arduino.send_set(green_a, green_b)
            mode = "NORMAL" if (sensor_result.ok and behavior_result.ok and safety_result.ok) else "DEGRADED"
            self.lights.leave_safe_mode()
            self.lights.set_greens(green_a, green_b)

        self.lights.advance()
        road_a_color, road_b_color = self.lights.light_colors()
        seconds_remaining = self.lights.time_remaining()

        result = TickResult(
            camera_count=camera_count,
            sensor_count=sensor_count,
            baseline=baseline,
            sensor_check=sensor_result,
            behavior_check=behavior_result,
            safety_check=safety_result,
            trust_score=trust,
            mode=mode,
            arduino_response=arduino_response,
            road_a_color=road_a_color,
            road_b_color=road_b_color,
            seconds_remaining=seconds_remaining,
            road_b_count=road_b_count,
            green_a_applied=green_a,
            green_b_applied=green_b,
            signal_decision_reason=reason,
        )
        self.history.append(result)
        self.history = self.history[-100:]
        return result

    @staticmethod
    def _adaptive_green(count):
        # Simple proportional mapping, clamped to the same safe bounds.
        seconds = int(10 + count * 0.3)
        return max(SafetyEngine.MIN_GREEN, min(SafetyEngine.MAX_GREEN, seconds))

    @classmethod
    def _proportional_greens(cls, count_a, count_b):
        """Splits available green time between the two roads in proportion to
        how many vehicles each one has waiting — this IS the adaptive logic,
        made comparable and explainable rather than a black box."""
        total = count_a + count_b
        if total <= 0:
            return SafetyEngine.MIN_GREEN, SafetyEngine.MIN_GREEN
        pool = SafetyEngine.MIN_GREEN * 2 + int((SafetyEngine.MAX_GREEN - SafetyEngine.MIN_GREEN) * 1.6)
        share_a = count_a / total
        green_a = int(SafetyEngine.MIN_GREEN + share_a * (pool - 2 * SafetyEngine.MIN_GREEN))
        green_b = int(SafetyEngine.MIN_GREEN + (1 - share_a) * (pool - 2 * SafetyEngine.MIN_GREEN))
        green_a = max(SafetyEngine.MIN_GREEN, min(SafetyEngine.MAX_GREEN, green_a))
        green_b = max(SafetyEngine.MIN_GREEN, min(SafetyEngine.MAX_GREEN, green_b))
        return green_a, green_b


# =====================================================================
# QUICK CLI TEST
# =====================================================================
if __name__ == "__main__":
    guardian = ResilientTrafficGuardian(arduino_port=None)  # set e.g. "COM5" or "/dev/ttyUSB0"

    scenarios = [None, None, "camera_spoof", "malicious_command", "server_down", None]
    for scenario in scenarios:
        guardian.trigger_attack(scenario)
        r = guardian.tick()
        print("-" * 60)
        print(f"Attack forced: {scenario}")
        print(f"Camera={r.camera_count}  Sensor={r.sensor_count}  Baseline={r.baseline}")
        print(f"Sensor check   : {'OK' if r.sensor_check.ok else 'FAIL'} - {r.sensor_check.reason}")
        print(f"Behavior check : {'OK' if r.behavior_check.ok else 'FAIL'} - {r.behavior_check.reason}")
        print(f"Safety check   : {'OK' if r.safety_check.ok else 'FAIL'} - {r.safety_check.reason}")
        print(f"Trust score    : {r.trust_score}%   Mode: {r.mode}")
        print(f"Signal decision: {r.signal_decision_reason}")
        time.sleep(0.3)
