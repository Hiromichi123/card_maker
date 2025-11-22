"""
Background manager with parallax effect
"""
import pygame
import math
import os
import random


class ParallaxBackground:
    """Background with mouse-based parallax effect"""
    
    def __init__(self, width, height, bg_type="menu"):
        """
        Args:
            width: Screen width
            height: Screen height
            bg_type: Type of background ("menu" or "battle")
        """
        self.width = width
        self.height = height
        self.bg_type = bg_type
        
        # Parallax offset
        self.offset_x = 0
        self.offset_y = 0
        self.target_offset_x = 0
        self.target_offset_y = 0
        
        # Create or load background
        self.background = self.create_background()
        
        # Create larger surface for parallax effect
        self.parallax_width = int(width * 1.1)
        self.parallax_height = int(height * 1.1)
        self.parallax_surface = pygame.transform.smoothscale(
            self.background, (self.parallax_width, self.parallax_height)
        )
        
    def create_background(self):
        """Create procedural background"""
        bg = pygame.Surface((self.width, self.height))
        
        if self.bg_type == "menu":
            # Blue gradient background for main menu
            self._draw_gradient(bg, (20, 30, 60), (30, 50, 100))
            self._add_stars(bg, count=100, color=(100, 150, 255))
            self._add_circles(bg, count=5, color=(50, 100, 200, 30))
        else:
            # Red gradient background for battle menu
            self._draw_gradient(bg, (60, 20, 30), (100, 30, 50))
            self._add_stars(bg, count=100, color=(255, 100, 100))
            self._add_circles(bg, count=5, color=(200, 50, 50, 30))
        
        return bg
    
    def _draw_gradient(self, surface, color1, color2):
        """Draw vertical gradient"""
        for y in range(self.height):
            ratio = y / self.height
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))
    
    def _add_stars(self, surface, count, color):
        """Add star-like particles"""
        for _ in range(count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            alpha = random.randint(100, 255)
            
            # Create temporary surface for alpha
            star_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            star_color = (*color[:3], alpha) if len(color) > 3 else (*color, alpha)
            pygame.draw.circle(star_surf, star_color, (size, size), size)
            surface.blit(star_surf, (x - size, y - size))
    
    def _add_circles(self, surface, count, color):
        """Add decorative circles"""
        temp_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for _ in range(count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            radius = random.randint(100, 300)
            
            # Draw circle with alpha
            if len(color) == 4:
                pygame.draw.circle(temp_surf, color, (x, y), radius)
            else:
                pygame.draw.circle(temp_surf, (*color, 30), (x, y), radius)
        
        surface.blit(temp_surf, (0, 0))
    
    def update_mouse_position(self, mouse_pos):
        """Update parallax based on mouse position"""
        # Calculate offset based on mouse position (normalized to -1 to 1)
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Maximum parallax offset
        max_offset = 50
        
        # Calculate target offset
        self.target_offset_x = ((mouse_pos[0] - center_x) / center_x) * max_offset
        self.target_offset_y = ((mouse_pos[1] - center_y) / center_y) * max_offset
    
    def update(self, dt):
        """Update parallax animation"""
        # Smooth interpolation
        self.offset_x += (self.target_offset_x - self.offset_x) * 5 * dt
        self.offset_y += (self.target_offset_y - self.offset_y) * 5 * dt
    
    def draw(self, screen):
        """Draw background with parallax effect"""
        # Calculate source rect for parallax
        src_x = int((self.parallax_width - self.width) / 2 - self.offset_x)
        src_y = int((self.parallax_height - self.height) / 2 - self.offset_y)
        
        # Ensure we don't go out of bounds
        src_x = max(0, min(src_x, self.parallax_width - self.width))
        src_y = max(0, min(src_y, self.parallax_height - self.height))
        
        # Blit the portion of parallax surface
        screen.blit(self.parallax_surface, (0, 0), 
                   pygame.Rect(src_x, src_y, self.width, self.height))


def load_or_create_background(width, height, bg_type="menu"):
    """Load background from file or create procedurally"""
    filename = f"assets/{bg_type}_bg.png"
    
    if os.path.exists(filename):
        try:
            bg = pygame.image.load(filename)
            bg = pygame.transform.smoothscale(bg, (width, height))
            return bg
        except:
            pass
    
    # Create procedural background if file doesn't exist
    return ParallaxBackground(width, height, bg_type).background
