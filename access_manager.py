"""
AccessManager: Administrative Override & Identity Service.

Consolidates identity management, temporal safety watchdog logic, and 
high-visibility ANSI visualization into a single high-integrity module.

Architecture:
    - Model: AccessManager (Logic & State)
    - View: AccessDashboard (Chromatic ANSI UI)
    - Controller: Internal Pulse & Handshake logic

Author: Charles Austin - Principal Solutions Architect
"""

import time
import logging
import unittest
import sys
from dataclasses import dataclass, field
from typing import Final, Dict, Optional, Tuple, Any

# --- CELL 1: IMPORTS & CONFIG ---

# Configure Module-Level Logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("AccessManager")

@dataclass(frozen=True)
class AccessConfig:
    """System-wide immutable access constants."""
    MAINTENANCE_TIMEOUT_SEC: Final[float] = 300.0  # 5-Minute Watchdog
    HEARTBEAT_THRESHOLD_SEC: Final[float] = 1.0    # Emergency Signal Loss

    # Local Auth Cache (Contingency Path)
    auth_cache: Dict[str, str] = field(default_factory=lambda: {
        "OP-7721": "Standard Operator",
        "MAINT-900": "Maintenance Tech",
        "ARCH-001": "Senior Architect"
    })

@dataclass(frozen=True)
class ClearanceLevel:
    """Defines operator capabilities based on tier."""
    name: str
    tier_id: int
    speed_limit_scale: float
    stiffness_boost: float

# Define Tier Constants
TIER_1: Final[ClearanceLevel] = ClearanceLevel("Standard", 1, 0.5, 1.0)
TIER_2: Final[ClearanceLevel] = ClearanceLevel("Maintenance", 2, 0.8, 1.5)
TIER_3: Final[ClearanceLevel] = ClearanceLevel("Admin", 3, 1.0, 2.0)

# --- CELL 2: CLASS DEFINITIONS & LOGIC ---

class AccessManager:
    """
    Manages identity verification and maintenance mode watchdog.
    Decouples safety logic from user authorization.
    """

    def __init__(self, config: AccessConfig = AccessConfig()) -> None:
        """Initialize the manager with default system config."""
        self.cfg = config
        self._active_session: Optional[ClearanceLevel] = None
        self._last_presence_time: float = 0.0
        self._active_badge: Optional[str] = None

    @property
    def is_override_active(self) -> bool:
        """Returns True if the system is currently in an override state."""
        return self._active_session is not None

    @property
    def active_session(self) -> Optional[ClearanceLevel]:
        """Public getter for session monitoring."""
        return self._active_session

    @property
    def active_badge(self) -> Optional[str]:
        """Public getter for currently logged-in badge ID."""
        return self._active_badge

    @property
    def last_presence_time(self) -> float:
        """Public getter for presence telemetry."""
        return self._last_presence_time

    @last_presence_time.setter
    def last_presence_time(self, value: float) -> None:
        """Internal setter for simulation/testing purposes."""
        self._last_presence_time = value

    def request_override(self, badge_id: str, voice_intent: str) -> bool:
        """
        Implements a 2-FA Handshake for system override.

        Raises:
            AttributeError: If inputs are None.
        """
        # 0. Input Normalization (Triggers AttributeError if None)
        clean_badge = badge_id.strip()
        clean_intent = voice_intent.strip().lower()

        # 1. Primary Check: Validate Badge
        if clean_badge not in self.cfg.auth_cache:
            LOGGER.warning("Auth Denied: Invalid Badge ID [%s]", clean_badge)
            return False

        # 2. Logic Gate: Voice Intent Verification
        valid_intents = ["start maintenance", "admin override", "system check"]
        if clean_intent not in valid_intents:
            LOGGER.warning("Auth Denied: Intent '%s' not recognized.", clean_intent)
            return False

        # 3. Grant Access based on ID Prefix
        if clean_badge.startswith("ARCH"):
            self._active_session = TIER_3
        elif clean_badge.startswith("MAINT"):
            self._active_session = TIER_2
        else:
            self._active_session = TIER_1

        self._active_badge = clean_badge
        self._last_presence_time = time.monotonic()

        LOGGER.info("OVERRIDE GRANTED: %s (Tier %d)",
                    self._active_session.name, self._active_session.tier_id)
        return True

    def maintenance_pulse(self, operator_present: bool) -> Tuple[bool, str]:
        """
        Processes a single heartbeat pulse and returns (success, message).
        Matches the signature expected by the high-integrity test suite.
        """
        if not self.is_override_active:
            return True, "STANDBY: No active override."

        current_time = time.monotonic()
        if operator_present:
            self._last_presence_time = current_time

        elapsed = current_time - self._last_presence_time

        if elapsed > self.cfg.MAINTENANCE_TIMEOUT_SEC:
            LOGGER.error("WATCHDOG EXPIRED: Operator absent.")
            self.secure_logout()
            return False, "EMERGENCY: Watchdog timeout. Reverting to Safe Mode."

        remaining = int(self.cfg.MAINTENANCE_TIMEOUT_SEC - elapsed)
        return True, f"ACTIVE: Session confirmed. Timeout in {remaining}s"

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Assembles a telemetry packet for the dashboard view.
        Separates data from logic for MVC compliance.
        """
        if not self.is_override_active:
            return {"active": False, "msg": "STANDBY", "time_left": 0.0}

        elapsed = time.monotonic() - self._last_presence_time
        time_left = max(0.0, self.cfg.MAINTENANCE_TIMEOUT_SEC - elapsed)

        return {
            "active": True,
            "tier": self._active_session.name if self._active_session else "N/A",
            "badge": self._active_badge,
            "time_left": time_left
        }

    def secure_logout(self) -> None:
        """Safely terminates the current session."""
        if self._active_session:
            LOGGER.info("SECURE LOGOUT: User %s session closed.", self._active_badge)
        self._active_session = None
        self._active_badge = None
        self._last_presence_time = 0.0


class AccessDashboard:
    """Handles high-visibility visual cues with ANSI color support."""

    BAR_WIDTH: Final[int] = 30

    # ANSI Color Constants
    CLR_RESET: Final[str] = "\033[0m"
    CLR_GREEN: Final[str] = "\033[92m"   # Safe
    CLR_YELLOW: Final[str] = "\033[93m"  # Caution / Bar
    CLR_RED: Final[str] = "\033[91m"     # Warning
    CLR_BOLD: Final[str] = "\033[1m"     # Attention

    @staticmethod
    def display_banner() -> None:
        """Prints the system startup header to satisfy R0903 and improve UI."""
        banner = "\n--- MINI FACTORY: ACCESS STATUS MONITOR (COLOR ENABLED) ---"
        print(banner)

    @staticmethod
    def render(telemetry: Dict[str, Any]) -> None:
        """Prints a color-coded visual status line to the terminal."""
        if not telemetry["active"]:
            # White text, Green bar
            status = " [SYSTEM SAFE: STANDARD GUARDS ACTIVE] "
            bar_content = "░" * AccessDashboard.BAR_WIDTH
            status_bar = f"{AccessDashboard.CLR_GREEN}{bar_content}{AccessDashboard.CLR_RESET}"
            out = f"\r{status} [{status_bar}]"
        else:
            # Calculate remaining time percentage
            percent = telemetry["time_left"] / 300.0
            filled = int(AccessDashboard.BAR_WIDTH * percent)

            # Colored bar (Yellow) for the override mode
            bar_text = "█" * filled + "·" * (AccessDashboard.BAR_WIDTH - filled)
            status_bar = f"{AccessDashboard.CLR_YELLOW}{bar_text}{AccessDashboard.CLR_RESET}"

            tier = telemetry["tier"].upper()
            rem = int(telemetry["time_left"])

            # White text surrounding a Bold Red Caution message
            caution = (f"{AccessDashboard.CLR_BOLD}{AccessDashboard.CLR_RED}"
                       f"CAUTION: {tier} OVERRIDE ACTIVE{AccessDashboard.CLR_RESET}")
            prefix = f" [!] {caution} ({rem}s) [!] "
            out = f"\r{prefix} [{status_bar}]"

        sys.stdout.write(out)
        sys.stdout.flush()


# --- CELL 3: UNIT TESTS ---

class TestAccessSystem(unittest.TestCase):
    """Verifies core logic and telemetry flow."""

    def setUp(self) -> None:
        self.manager = AccessManager()

    def test_override_telemetry(self) -> None:
        """Verify telemetry dictionary content during override."""
        self.manager.request_override("MAINT-900", "start maintenance")
        data = self.manager.get_telemetry()
        self.assertTrue(data["active"])
        self.assertEqual(data["tier"], "Maintenance")

    def test_none_input_failure(self) -> None:
        """Verify that passing None raises AttributeError (Type Integrity)."""
        with self.assertRaises(AttributeError):
            self.manager.request_override(None, "admin override") # type: ignore


# --- CELL 4: MISSION EXECUTION ---

def run_visual_audit() -> None:
    """Executes a diagnostic simulation with full visual output."""
    manager = AccessManager()
    dashboard = AccessDashboard()

    dashboard.display_banner()

    # 1. Initial State
    manager.maintenance_pulse(operator_present=False)
    dashboard.render(manager.get_telemetry())
    time.sleep(1.0)

    # 2. Granting Access
    print("\n\n[ACTION] Admin Badging In...")
    if manager.request_override("ARCH-001", "admin override"):
        # 3. Active Pulse
        for _ in range(5):
            manager.maintenance_pulse(operator_present=True)
            dashboard.render(manager.get_telemetry())
            time.sleep(0.5)

        print("\n\n[ACTION] Operator Leaves Area...")
        # Simulate time jump to trigger the countdown
        manager.last_presence_time = time.monotonic() - 295.0

        # Final Countdown visual
        for _ in range(10):
            active, _ = manager.maintenance_pulse(operator_present=False)
            dashboard.render(manager.get_telemetry())
            time.sleep(1.0)
            if not active:
                break

    print("\n\n--- AUDIT COMPLETE: SYSTEM REVERTED TO SAFE ---")

if __name__ == "__main__":
    # 1. Run Tests
    LOADER = unittest.TestLoader()
    SUITE = LOADER.loadTestsFromTestCase(TestAccessSystem)
    RUNNER = unittest.TextTestRunner(verbosity=0)
    RESULT = RUNNER.run(SUITE)

    # 2. Run Audit if tests pass
    if RESULT.wasSuccessful():
        run_visual_audit()
