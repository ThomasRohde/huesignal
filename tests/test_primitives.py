"""Unit tests for primitive operations."""

import pytest

from huesignal.effects.primitives import PrimitiveResult, SetState, Wait


class TestPrimitiveResult:
    """Tests for PrimitiveResult dataclass."""

    def test_success_result(self):
        """Test successful primitive result."""
        result = PrimitiveResult(light_id="light-1", success=True)
        assert result.light_id == "light-1"
        assert result.success is True
        assert result.error is None

    def test_failure_result(self):
        """Test failed primitive result with error message."""
        result = PrimitiveResult(light_id="light-2", success=False, error="Connection timeout")
        assert result.light_id == "light-2"
        assert result.success is False
        assert result.error == "Connection timeout"


class TestSetState:
    """Tests for SetState primitive."""

    def test_setstate_defaults(self):
        """Test SetState with default values."""
        primitive = SetState()
        assert primitive.on is True
        assert primitive.brightness is None
        assert primitive.color is None
        assert primitive.transition_ms == 500

    def test_setstate_custom_values(self):
        """Test SetState with custom values."""
        primitive = SetState(on=False, brightness=150, color="blue", transition_ms=1000)
        assert primitive.on is False
        assert primitive.brightness == 150
        assert primitive.color == "blue"
        assert primitive.transition_ms == 1000

    def test_setstate_brightness_validation_minimum(self):
        """Test SetState accepts minimum valid brightness."""
        primitive = SetState(brightness=1)
        assert primitive.brightness == 1

    def test_setstate_brightness_validation_maximum(self):
        """Test SetState accepts maximum valid brightness."""
        primitive = SetState(brightness=254)
        assert primitive.brightness == 254

    def test_setstate_brightness_validation_invalid_zero(self):
        """Test SetState rejects brightness of 0."""
        with pytest.raises(ValueError, match="Brightness must be between 1 and 254"):
            SetState(brightness=0)

    def test_setstate_brightness_validation_invalid_negative(self):
        """Test SetState rejects negative brightness."""
        with pytest.raises(ValueError, match="Brightness must be between 1 and 254"):
            SetState(brightness=-1)

    def test_setstate_brightness_validation_invalid_too_high(self):
        """Test SetState rejects brightness above 254."""
        with pytest.raises(ValueError, match="Brightness must be between 1 and 254"):
            SetState(brightness=255)

    def test_setstate_transition_ms_validation_zero(self):
        """Test SetState accepts transition_ms of 0."""
        primitive = SetState(transition_ms=0)
        assert primitive.transition_ms == 0

    def test_setstate_transition_ms_validation_negative(self):
        """Test SetState rejects negative transition_ms."""
        with pytest.raises(ValueError, match="transition_ms must be >= 0"):
            SetState(transition_ms=-1)

    def test_setstate_estimated_duration(self):
        """Test SetState estimated_duration_ms calculation."""
        primitive = SetState(transition_ms=1000)
        # Should be transition time + 50ms buffer
        assert primitive.estimated_duration_ms() == 1050

    def test_setstate_estimated_duration_with_zero_transition(self):
        """Test estimated_duration_ms with zero transition time."""
        primitive = SetState(transition_ms=0)
        assert primitive.estimated_duration_ms() == 50

    def test_setstate_turn_on_with_brightness(self):
        """Test SetState to turn on with specific brightness."""
        primitive = SetState(on=True, brightness=200)
        assert primitive.on is True
        assert primitive.brightness == 200

    def test_setstate_turn_off(self):
        """Test SetState to turn off light."""
        primitive = SetState(on=False)
        assert primitive.on is False

    def test_setstate_with_color_name(self):
        """Test SetState with named color."""
        primitive = SetState(color="red")
        assert primitive.color == "red"

    def test_setstate_with_hex_color(self):
        """Test SetState with hex color code."""
        primitive = SetState(color="#FF5733")
        assert primitive.color == "#FF5733"

    def test_setstate_full_specification(self):
        """Test SetState with all parameters specified."""
        primitive = SetState(on=True, brightness=180, color="green", transition_ms=750)
        assert primitive.on is True
        assert primitive.brightness == 180
        assert primitive.color == "green"
        assert primitive.transition_ms == 750


class TestWait:
    """Tests for Wait primitive."""

    def test_wait_default(self):
        """Test Wait with default duration."""
        primitive = Wait()
        assert primitive.duration_ms == 500

    def test_wait_custom_duration(self):
        """Test Wait with custom duration."""
        primitive = Wait(duration_ms=2000)
        assert primitive.duration_ms == 2000

    def test_wait_zero_duration(self):
        """Test Wait accepts zero duration."""
        primitive = Wait(duration_ms=0)
        assert primitive.duration_ms == 0

    def test_wait_duration_validation_negative(self):
        """Test Wait rejects negative duration."""
        with pytest.raises(ValueError, match="duration_ms must be >= 0"):
            Wait(duration_ms=-1)

    def test_wait_estimated_duration(self):
        """Test Wait estimated_duration_ms."""
        primitive = Wait(duration_ms=1500)
        assert primitive.estimated_duration_ms() == 1500

    def test_wait_estimated_duration_zero(self):
        """Test Wait estimated_duration_ms with zero."""
        primitive = Wait(duration_ms=0)
        assert primitive.estimated_duration_ms() == 0


class TestPrimitiveExecution:
    """Tests for primitive execution (integration-style tests without real bridge)."""

    @pytest.mark.asyncio
    async def test_wait_executes_successfully(self):
        """Test Wait primitive executes without error."""
        import time

        primitive = Wait(duration_ms=100)

        # Execute wait - note: ctx and light_id are not used but required by signature
        start = time.time()
        result = await primitive.execute(ctx=None, light_id="dummy")  # type: ignore
        elapsed_ms = (time.time() - start) * 1000

        assert result.success is True
        assert result.error is None
        # Check that it actually waited approximately the right amount of time
        # Allow generous variance for system load and timing jitter
        assert 90 <= elapsed_ms <= 200  # Allow some variance

    @pytest.mark.asyncio
    async def test_wait_zero_duration_executes_immediately(self):
        """Test Wait with zero duration completes immediately."""
        import time

        primitive = Wait(duration_ms=0)

        start = time.time()
        result = await primitive.execute(ctx=None, light_id="dummy")  # type: ignore
        elapsed_ms = (time.time() - start) * 1000

        assert result.success is True
        assert elapsed_ms < 50  # Should be nearly instant
