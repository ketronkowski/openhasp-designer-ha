"""Device resolution mapping and utilities."""
from typing import Dict, Optional
from pydantic import BaseModel


class DeviceResolution(BaseModel):
    """Device screen resolution."""
    width: int
    height: int
    model: str
    description: Optional[str] = None


# Device model to resolution mapping
DEVICE_RESOLUTIONS: Dict[str, DeviceResolution] = {
    # Lanbon series
    "lanbon_l8": DeviceResolution(
        width=480,
        height=320,
        model="Lanbon L8",
        description="Lanbon L8 3-gang switch"
    ),
    "lanbon_l8_hd": DeviceResolution(
        width=800,
        height=480,
        model="Lanbon L8 HD",
        description="Lanbon L8 HD high-resolution"
    ),
    
    # WT32-SC01 series
    "wt32_sc01": DeviceResolution(
        width=320,
        height=480,
        model="WT32-SC01",
        description="WT32-SC01 3.5\" display"
    ),
    "wt32_sc01_plus": DeviceResolution(
        width=480,
        height=320,
        model="WT32-SC01 Plus",
        description="WT32-SC01 Plus 3.5\" display"
    ),
    
    # ESP32 series
    "esp32_2432s028r": DeviceResolution(
        width=240,
        height=320,
        model="ESP32-2432S028R",
        description="ESP32-2432S028R 2.8\" display (Cheap Yellow Display)"
    ),
    "esp32_3248s035c": DeviceResolution(
        width=480,
        height=320,
        model="ESP32-3248S035C",
        description="ESP32-3248S035C 3.5\" display"
    ),
    "esp32_4827s043": DeviceResolution(
        width=480,
        height=272,
        model="ESP32-4827S043",
        description="ESP32-4827S043 4.3\" display"
    ),
    "esp32_8048s070": DeviceResolution(
        width=800,
        height=480,
        model="ESP32-8048S070",
        description="ESP32-8048S070 7\" display"
    ),
    
    # Other devices
    "freetouchdeck": DeviceResolution(
        width=480,
        height=320,
        model="FreeTouchDeck",
        description="FreeTouchDeck ESP32 touchscreen"
    ),
    "m5stack_core2": DeviceResolution(
        width=320,
        height=240,
        model="M5Stack Core2",
        description="M5Stack Core2 2\" display"
    ),
    "lilygo_t_display": DeviceResolution(
        width=135,
        height=240,
        model="LILYGO T-Display",
        description="LILYGO T-Display 1.14\" TFT"
    ),
    
    # Generic size presets
    "small_portrait": DeviceResolution(
        width=240,
        height=320,
        model="Small Portrait",
        description="Generic small portrait (240x320)"
    ),
    "medium_portrait": DeviceResolution(
        width=320,
        height=480,
        model="Medium Portrait",
        description="Generic medium portrait (320x480)"
    ),
    "large_portrait": DeviceResolution(
        width=480,
        height=800,
        model="Large Portrait",
        description="Generic large portrait (480x800)"
    ),
    "small_landscape": DeviceResolution(
        width=320,
        height=240,
        model="Small Landscape",
        description="Generic small landscape (320x240)"
    ),
    "medium_landscape": DeviceResolution(
        width=480,
        height=320,
        model="Medium Landscape",
        description="Generic medium landscape (480x320)"
    ),
    "large_landscape": DeviceResolution(
        width=800,
        height=480,
        model="Large Landscape",
        description="Generic large landscape (800x480)"
    ),
}



def get_device_resolution(model_key: str) -> Optional[DeviceResolution]:
    """Get resolution for a device model."""
    return DEVICE_RESOLUTIONS.get(model_key.lower())


def get_all_device_models() -> Dict[str, DeviceResolution]:
    """Get all known device models and their resolutions."""
    return DEVICE_RESOLUTIONS


def validate_coordinates(x: int, y: int, width: int, height: int, 
                        device_width: int, device_height: int) -> tuple[bool, Optional[str]]:
    """
    Validate object coordinates against device screen size.
    
    Returns:
        (is_valid, error_message)
    """
    if x < 0 or y < 0:
        return False, f"Coordinates cannot be negative: x={x}, y={y}"
    
    if x + width > device_width:
        return False, f"Object extends beyond screen width: {x + width} > {device_width}"
    
    if y + height > device_height:
        return False, f"Object extends beyond screen height: {y + height} > {device_height}"
    
    return True, None
