"""Tests for device models and resolution mapping."""
import pytest
from app.models.device import (
    get_device_resolution,
    get_all_device_models,
    validate_coordinates,
    DeviceResolution
)


def test_get_device_resolution_lanbon_l8():
    """Test getting resolution for Lanbon L8."""
    res = get_device_resolution("lanbon_l8")
    assert res is not None
    assert res.width == 480
    assert res.height == 320
    assert res.model == "Lanbon L8"


def test_get_device_resolution_wt32_sc01():
    """Test getting resolution for WT32-SC01."""
    res = get_device_resolution("wt32_sc01")
    assert res is not None
    assert res.width == 320
    assert res.height == 480


def test_get_device_resolution_case_insensitive():
    """Test that model lookup is case-insensitive."""
    res1 = get_device_resolution("LANBON_L8")
    res2 = get_device_resolution("lanbon_l8")
    assert res1 == res2


def test_get_device_resolution_unknown():
    """Test getting resolution for unknown model."""
    res = get_device_resolution("unknown_model")
    assert res is None


def test_get_all_device_models():
    """Test getting all device models."""
    models = get_all_device_models()
    assert isinstance(models, dict)
    assert len(models) >= 6  # At least 6 models defined
    assert "lanbon_l8" in models
    assert "wt32_sc01" in models


def test_validate_coordinates_valid():
    """Test valid coordinates."""
    is_valid, error = validate_coordinates(10, 20, 100, 50, 480, 320)
    assert is_valid is True
    assert error is None


def test_validate_coordinates_negative_x():
    """Test negative X coordinate."""
    is_valid, error = validate_coordinates(-10, 20, 100, 50, 480, 320)
    assert is_valid is False
    assert "negative" in error.lower()


def test_validate_coordinates_negative_y():
    """Test negative Y coordinate."""
    is_valid, error = validate_coordinates(10, -20, 100, 50, 480, 320)
    assert is_valid is False
    assert "negative" in error.lower()


def test_validate_coordinates_exceeds_width():
    """Test coordinates exceeding screen width."""
    is_valid, error = validate_coordinates(400, 20, 100, 50, 480, 320)
    assert is_valid is False
    assert "width" in error.lower()


def test_validate_coordinates_exceeds_height():
    """Test coordinates exceeding screen height."""
    is_valid, error = validate_coordinates(10, 300, 100, 50, 480, 320)
    assert is_valid is False
    assert "height" in error.lower()


def test_validate_coordinates_exact_fit():
    """Test object that exactly fits the screen."""
    is_valid, error = validate_coordinates(0, 0, 480, 320, 480, 320)
    assert is_valid is True
    assert error is None
