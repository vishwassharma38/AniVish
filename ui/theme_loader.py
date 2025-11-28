import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from core.logger import get_logger

logger = get_logger("theme")


@dataclass
class ThemeColors:
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    text_secondary: str
    error: str
    success: str


@dataclass
class Theme:
    name: str
    colors: ThemeColors
    glass_blur: int
    glass_opacity: float
    glow_strength: int
    
    @staticmethod
    def load_from_file(path: Path) -> 'Theme':
        """Load theme from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        colors = ThemeColors(**data['colors'])
        
        return Theme(
            name=data['name'],
            colors=colors,
            glass_blur=data['glass']['blur_radius'],
            glass_opacity=data['glass']['opacity'],
            glow_strength=data['glass']['glow_strength']
        )