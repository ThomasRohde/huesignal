"""Unit tests for light name resolver."""

from unittest.mock import MagicMock

import pytest

from huesignal.resolver import (
    AmbiguousLightError,
    LightNotFoundError,
    ResolvedLight,
    parse_light_argument,
    resolve_light,
    resolve_lights,
)


@pytest.fixture
def mock_bridge():
    """Create a mock HueBridge with test lights."""
    bridge = MagicMock()

    # Create mock lights
    lights = {}
    light_data = [
        ("1", "Desk Lamp"),
        ("2", "Bedroom Light"),
        ("3", "Living Room"),
    ]

    for light_id, light_name in light_data:
        light = MagicMock()
        light.metadata = MagicMock()
        light.metadata.name = light_name
        lights[light_id] = light

    bridge.lights = lights
    return bridge


class TestResolveLight:
    """Tests for resolve_light function."""

    @pytest.mark.asyncio
    async def test_resolve_by_exact_name(self, mock_bridge):
        """Test resolving light by exact name match."""
        result = await resolve_light(mock_bridge, light_name="Desk Lamp")
        assert result.light_id == "1"
        assert result.light_name == "Desk Lamp"

    @pytest.mark.asyncio
    async def test_resolve_by_case_insensitive_name(self, mock_bridge):
        """Test resolving light by case-insensitive name match."""
        result = await resolve_light(mock_bridge, light_name="desk lamp")
        assert result.light_id == "1"
        assert result.light_name == "Desk Lamp"

    @pytest.mark.asyncio
    async def test_resolve_by_light_id(self, mock_bridge):
        """Test resolving light by ID."""
        result = await resolve_light(mock_bridge, light_id="2")
        assert result.light_id == "2"
        assert result.light_name == "Bedroom Light"

    @pytest.mark.asyncio
    async def test_resolve_light_id_takes_precedence(self, mock_bridge):
        """Test that light_id takes precedence over light_name."""
        result = await resolve_light(mock_bridge, light_name="Desk Lamp", light_id="2")
        assert result.light_id == "2"
        assert result.light_name == "Bedroom Light"

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_light_by_name(self, mock_bridge):
        """Test that LightNotFoundError is raised for nonexistent light name."""
        with pytest.raises(LightNotFoundError):
            await resolve_light(mock_bridge, light_name="Nonexistent Light")

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_light_by_id(self, mock_bridge):
        """Test that LightNotFoundError is raised for nonexistent light ID."""
        with pytest.raises(LightNotFoundError):
            await resolve_light(mock_bridge, light_id="999")

    @pytest.mark.asyncio
    async def test_resolve_no_identifier_raises_error(self, mock_bridge):
        """Test that ValueError is raised when no identifier provided."""
        with pytest.raises(ValueError):
            await resolve_light(mock_bridge)

    @pytest.mark.asyncio
    async def test_ambiguous_light_name(self, mock_bridge):
        """Test that AmbiguousLightError is raised for ambiguous names."""
        # Add duplicate light names
        light = MagicMock()
        light.metadata = MagicMock()
        light.metadata.name = "Desk Lamp"
        mock_bridge.lights["4"] = light

        with pytest.raises(AmbiguousLightError) as exc_info:
            await resolve_light(mock_bridge, light_name="Desk Lamp")

        assert exc_info.value.name == "Desk Lamp"
        assert len(exc_info.value.candidates) == 2


class TestResolveLights:
    """Tests for resolve_lights function."""

    @pytest.mark.asyncio
    async def test_resolve_multiple_lights_by_name(self, mock_bridge):
        """Test resolving multiple lights by name."""
        result = await resolve_lights(mock_bridge, light_names=["Desk Lamp", "Bedroom Light"])
        assert len(result) == 2
        assert result[0].light_id == "1"
        assert result[1].light_id == "2"

    @pytest.mark.asyncio
    async def test_resolve_multiple_lights_by_id(self, mock_bridge):
        """Test resolving multiple lights by ID."""
        result = await resolve_lights(mock_bridge, light_ids=["1", "3"])
        assert len(result) == 2
        assert result[0].light_id == "1"
        assert result[1].light_id == "3"

    @pytest.mark.asyncio
    async def test_resolve_all_lights_when_no_args(self, mock_bridge):
        """Test resolving all lights when no arguments provided."""
        result = await resolve_lights(mock_bridge)
        assert len(result) == 3
        assert {r.light_id for r in result} == {"1", "2", "3"}

    @pytest.mark.asyncio
    async def test_resolve_lights_invalid_id(self, mock_bridge):
        """Test that LightNotFoundError is raised for invalid ID."""
        with pytest.raises(LightNotFoundError):
            await resolve_lights(mock_bridge, light_ids=["999"])

    @pytest.mark.asyncio
    async def test_resolve_lights_invalid_name(self, mock_bridge):
        """Test that LightNotFoundError is raised for invalid name."""
        with pytest.raises(LightNotFoundError):
            await resolve_lights(mock_bridge, light_names=["Nonexistent"])

    @pytest.mark.asyncio
    async def test_light_id_takes_precedence(self, mock_bridge):
        """Test that light_ids takes precedence over light_names."""
        result = await resolve_lights(
            mock_bridge,
            light_names=["Desk Lamp"],
            light_ids=["2"],
        )
        assert len(result) == 1
        assert result[0].light_id == "2"


class TestParseLightArgument:
    """Tests for parse_light_argument function."""

    def test_parse_single_light(self):
        """Test parsing a single light name."""
        result = parse_light_argument("Desk Lamp")
        assert result == ["Desk Lamp"]

    def test_parse_comma_separated_lights(self):
        """Test parsing comma-separated light names."""
        result = parse_light_argument("Desk Lamp,Bedroom Light,Living Room")
        assert result == ["Desk Lamp", "Bedroom Light", "Living Room"]

    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace."""
        result = parse_light_argument("Desk Lamp , Bedroom Light , Living Room")
        assert result == ["Desk Lamp", "Bedroom Light", "Living Room"]

    def test_parse_single_with_trailing_comma(self):
        """Test parsing with trailing comma."""
        result = parse_light_argument("Desk Lamp,")
        assert result == ["Desk Lamp"]

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = parse_light_argument("")
        assert result == []


class TestResolvedLight:
    """Tests for ResolvedLight dataclass."""

    def test_resolved_light_str(self):
        """Test string representation of ResolvedLight."""
        light = ResolvedLight(light_id="1", light_name="Desk Lamp")
        assert str(light) == "Desk Lamp (ID: 1)"

    def test_resolved_light_equality(self):
        """Test equality of ResolvedLight objects."""
        light1 = ResolvedLight(light_id="1", light_name="Desk Lamp")
        light2 = ResolvedLight(light_id="1", light_name="Desk Lamp")
        assert light1 == light2

    def test_resolved_light_inequality(self):
        """Test inequality of ResolvedLight objects."""
        light1 = ResolvedLight(light_id="1", light_name="Desk Lamp")
        light2 = ResolvedLight(light_id="2", light_name="Bedroom Light")
        assert light1 != light2
