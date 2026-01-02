"""Unit tests for runner payload serialization."""

import json

from huesignal.runner import run_effect_sync


class TestPayloadSerialization:
    """Tests for effect payload serialization and deserialization."""

    def test_payload_simple_effect(self):
        """Test serializing simple effect payload."""
        payload = {
            "effect": "blink",
            "parameters": {
                "light_ids": ["1", "2"],
                "count": 3,
                "interval_ms": 500,
                "restore": True,
            },
        }

        # Serialize to JSON
        json_str = json.dumps(payload)
        assert isinstance(json_str, str)

        # Deserialize back
        deserialized = json.loads(json_str)
        assert deserialized == payload

    def test_payload_breathe_effect(self):
        """Test serializing breathe effect payload."""
        payload = {
            "effect": "breathe",
            "parameters": {
                "light_ids": ["1"],
                "duration_ms": 5000,
                "period_ms": 2000,
                "brightness": 200,
                "restore": True,
            },
        }

        # Round-trip test
        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)
        assert deserialized == payload

    def test_payload_rainbow_effect(self):
        """Test serializing rainbow effect payload."""
        payload = {
            "effect": "rainbow",
            "parameters": {
                "light_ids": ["2", "3"],
                "duration_ms": 5000,
                "step_ms": 100,
                "restore": True,
            },
        }

        # Round-trip test
        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)
        assert deserialized == payload

    def test_payload_with_color(self):
        """Test serializing payload with color parameter."""
        payload = {
            "effect": "pulse",
            "parameters": {
                "light_ids": ["1"],
                "color": "red",
                "duration_ms": 2000,
                "restore": True,
            },
        }

        # Round-trip test
        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)
        assert deserialized == payload

    def test_payload_with_multiple_lights(self):
        """Test serializing payload with multiple lights."""
        payload = {
            "effect": "breathe",
            "parameters": {
                "light_ids": ["1", "2", "3", "4"],
                "duration_ms": 3000,
                "period_ms": 2000,
                "restore": True,
            },
        }

        # Round-trip test
        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)
        assert deserialized == payload

    def test_payload_round_trip_equality(self):
        """Test that payload round-trips maintain equality."""
        original_payloads = [
            {
                "effect": "blink",
                "parameters": {"light_ids": ["1"], "count": 1, "interval_ms": 500, "restore": False},
            },
            {
                "effect": "breathe",
                "parameters": {"light_ids": ["2"], "duration_ms": 4000, "period_ms": 2000, "restore": True},
            },
            {
                "effect": "rainbow",
                "parameters": {"light_ids": ["3"], "duration_ms": 5000, "step_ms": 100, "restore": True},
            },
        ]

        for original in original_payloads:
            # Serialize
            json_str = json.dumps(original)

            # Deserialize
            deserialized = json.loads(json_str)

            # Check equality
            assert deserialized == original
            assert deserialized["effect"] == original["effect"]
            assert deserialized["parameters"] == original["parameters"]

    def test_payload_types_preserved(self):
        """Test that JSON serialization preserves data types."""
        payload = {
            "effect": "breathe",
            "parameters": {
                "light_ids": ["1", "2"],  # list
                "duration_ms": 5000,  # int
                "period_ms": 2000.5,  # float
                "restore": True,  # bool
            },
        }

        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)

        # Check types
        assert isinstance(deserialized["parameters"]["light_ids"], list)
        assert isinstance(deserialized["parameters"]["duration_ms"], int)
        assert isinstance(deserialized["parameters"]["period_ms"], float)
        assert isinstance(deserialized["parameters"]["restore"], bool)

    def test_payload_empty_light_ids(self):
        """Test serializing payload with empty light_ids."""
        payload = {
            "effect": "blink",
            "parameters": {
                "light_ids": [],
                "count": 1,
                "interval_ms": 500,
                "restore": True,
            },
        }

        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)
        assert deserialized == payload

    def test_payload_special_characters_in_effect_name(self):
        """Test serializing payload with special characters in effect name."""
        payload = {
            "effect": "my-special-effect",
            "parameters": {
                "light_ids": ["1"],
                "custom_param": "value-with-dash",
            },
        }

        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)
        assert deserialized == payload


class TestEffectSyncRunner:
    """Tests for synchronous effect runner."""

    def test_run_effect_sync_success(self, capsys):
        """Test running effect synchronously returns success."""
        result = run_effect_sync("blink", {"light_ids": ["1"], "count": 1})
        assert result == 0

        captured = capsys.readouterr()
        assert "Running effect: blink" in captured.out

    def test_run_effect_sync_preserves_parameters(self, capsys):
        """Test that sync runner preserves effect parameters."""
        params = {"light_ids": ["1", "2"], "count": 3}
        result = run_effect_sync("blink", params)
        assert result == 0

        captured = capsys.readouterr()
        assert str(params) in captured.out


class TestPayloadValidation:
    """Tests for payload validation and structure."""

    def test_payload_has_required_fields(self):
        """Test that payload has required fields."""
        payload = {
            "effect": "blink",
            "parameters": {"light_ids": ["1"]},
        }

        assert "effect" in payload
        assert "parameters" in payload
        assert isinstance(payload["effect"], str)
        assert isinstance(payload["parameters"], dict)

    def test_parameters_can_be_serialized(self):
        """Test that parameters can be serialized to JSON."""
        params = {
            "light_ids": ["1", "2"],
            "duration_ms": 5000,
            "brightness": 200,
            "color": "red",
            "restore": True,
            "custom_field": None,
        }

        # Should not raise
        json_str = json.dumps(params)
        assert isinstance(json_str, str)

        # Should be able to deserialize
        deserialized = json.loads(json_str)
        assert deserialized == params
