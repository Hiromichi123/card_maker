"""Enhanced menu button with triangle indicators and hover effects"""
import pygame
import math
from config import UI_SCALE, get_font

class MenuButton:
    def __init__(self, x, y, width, height, text,
                 color=(100, 150, 255),
                 hover_color=(130, 180, 255),
                 text_color=(255, 255, 255),
                 font_size=40,
                 on_click=None):

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.on_click = on_click
        
        # Animation variables
        self.hover_alpha = 0  # For fade in/out effect
        self.glow_intensity = 0  # For glow pulsing
        self.glow_time = 0  # Time counter for animation
        
        # Font
        scaled_font_size = max(12, int(font_size * UI_SCALE))
        self.font = get_font(scaled_font_size)
        
        # Pre-render text
        self.text_surface = self.font.render(text, True, text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        
        # Triangle size
        self.triangle_size = int(20 * UI_SCALE)
        
    def update_position(self, x, y, width=None, height=None):
        """Update button position"""
        if width is None:
            width = self.rect.width
        if height is None:
            height = self.rect.height
        self.rect = pygame.Rect(x, y, width, height)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        
    def handle_event(self, event):
        """Handle events"""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                if self.on_click:
                    self.on_click()
                return True
        return False
    
    def update(self, dt):
        """Update animations"""
        # Update hover fade
        if self.is_hovered:
            self.hover_alpha = min(255, self.hover_alpha + 1000 * dt)
            self.glow_time += dt
        else:
            self.hover_alpha = max(0, self.hover_alpha - 1000 * dt)
            self.glow_time = 0
        
        # Update glow pulsing (when hovered)
        if self.is_hovered:
            self.glow_intensity = (math.sin(self.glow_time * 8) + 1) / 2  # 0 to 1
        else:
            self.glow_intensity = 0
    
    def draw(self, screen):
        """Draw button with modern style"""
        # Draw glow effect when hovered
        if self.hover_alpha > 0:
            # Create glow surface
            glow_surf = pygame.Surface((self.rect.width + 40, self.rect.height + 40), pygame.SRCALPHA)
            
            # Multiple layers for glow effect
            for i in range(3):
                alpha = int((self.hover_alpha / 255) * (100 - i * 30) * (0.5 + self.glow_intensity * 0.5))
                glow_color = (*self.hover_color, alpha)
                
                offset = (i + 1) * 8
                glow_rect = pygame.Rect(offset, offset, 
                                       self.rect.width + 40 - offset * 2, 
                                       self.rect.height + 40 - offset * 2)
                pygame.draw.rect(glow_surf, glow_color, glow_rect, border_radius=5)
            
            screen.blit(glow_surf, (self.rect.x - 20, self.rect.y - 20))
        
        # Draw left triangle indicator
        left_triangle_points = [
            (self.rect.left - int(40 * UI_SCALE), self.rect.centery),
            (self.rect.left - int(20 * UI_SCALE), self.rect.centery - self.triangle_size // 2),
            (self.rect.left - int(20 * UI_SCALE), self.rect.centery + self.triangle_size // 2)
        ]
        
        # Draw right triangle indicator
        right_triangle_points = [
            (self.rect.right + int(40 * UI_SCALE), self.rect.centery),
            (self.rect.right + int(20 * UI_SCALE), self.rect.centery - self.triangle_size // 2),
            (self.rect.right + int(20 * UI_SCALE), self.rect.centery + self.triangle_size // 2)
        ]
        
        # Triangle color with alpha
        if self.is_hovered:
            tri_alpha = int(150 + self.glow_intensity * 105)
            tri_color = (*self.hover_color, tri_alpha)
        else:
            tri_alpha = 100
            tri_color = (*self.color, tri_alpha)
        
        # Create surface for triangles with alpha - only size needed for triangles
        tri_width = int(60 * UI_SCALE)
        tri_surf_left = pygame.Surface((tri_width, self.rect.height), pygame.SRCALPHA)
        tri_surf_right = pygame.Surface((tri_width, self.rect.height), pygame.SRCALPHA)
        
        # Adjust points for local surface coordinates
        left_local = [
            (int(20 * UI_SCALE), self.rect.height // 2),
            (int(40 * UI_SCALE), self.rect.height // 2 - self.triangle_size // 2),
            (int(40 * UI_SCALE), self.rect.height // 2 + self.triangle_size // 2)
        ]
        right_local = [
            (int(40 * UI_SCALE), self.rect.height // 2),
            (int(20 * UI_SCALE), self.rect.height // 2 - self.triangle_size // 2),
            (int(20 * UI_SCALE), self.rect.height // 2 + self.triangle_size // 2)
        ]
        
        pygame.draw.polygon(tri_surf_left, tri_color, left_local)
        pygame.draw.polygon(tri_surf_right, tri_color, right_local)
        
        screen.blit(tri_surf_left, (self.rect.left - tri_width, self.rect.top))
        screen.blit(tri_surf_right, (self.rect.right, self.rect.top))
        
        # Draw text with optional glow (simplified for performance)
        if self.is_hovered and self.glow_intensity > 0.5:
            # Draw simple text shadow for glow effect
            glow_text = self.font.render(self.text, True, self.hover_color)
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                glow_rect = self.text_rect.copy()
                glow_rect.x += offset[0] * 2
                glow_rect.y += offset[1] * 2
                glow_surf = glow_text.copy()
                glow_surf.set_alpha(int(100 * self.glow_intensity))
                screen.blit(glow_surf, glow_rect)
        
        # Draw main text
        screen.blit(self.text_surface, self.text_rect)
