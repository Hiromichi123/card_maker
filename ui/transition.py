"""场景转场效果"""
import pygame


class Transition:
    """转场效果类"""
    def __init__(self):
        self.is_transitioning = False
        self.transition_alpha = 0
        self.transition_direction = 1  # 1 for fade out, -1 for fade in
        self.transition_speed = 800  # Alpha change per second
        self.on_complete = None
        
    def start_fade_out(self, on_complete=None):
        """开始淡出效果"""
        self.is_transitioning = True
        self.transition_alpha = 0
        self.transition_direction = 1
        self.on_complete = on_complete
    
    def start_fade_in(self, on_complete=None):
        """开始淡入效果"""
        self.is_transitioning = True
        self.transition_alpha = 255
        self.transition_direction = -1
        self.on_complete = on_complete
    
    def update(self, dt):
        """更新转场效果"""
        if not self.is_transitioning:
            return
        
        self.transition_alpha += self.transition_direction * self.transition_speed * dt
        
        # Clamp alpha
        if self.transition_direction > 0:
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.is_transitioning = False
                if self.on_complete:
                    self.on_complete()
        else:
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.is_transitioning = False
                if self.on_complete:
                    self.on_complete()
    
    def draw(self, screen):
        """绘制转场效果"""
        if self.transition_alpha > 0:
            fade_surface = pygame.Surface(screen.get_size())
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(int(self.transition_alpha))
            screen.blit(fade_surface, (0, 0))
    
    @staticmethod
    def fade_out(screen, duration=0.5, fps=60):
        """淡出效果（静态方法，用于向后兼容）"""
        clock = pygame.time.Clock()
        fade_surface = pygame.Surface(screen.get_size())
        fade_surface.fill((0, 0, 0))
        
        frames = int(duration * fps)
        for i in range(frames):
            alpha = int(255 * (i / frames))
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            clock.tick(fps)
    
    @staticmethod
    def fade_in(screen, duration=0.5, fps=60):
        """淡入效果（静态方法，用于向后兼容）"""
        clock = pygame.time.Clock()
        fade_surface = pygame.Surface(screen.get_size())
        fade_surface.fill((0, 0, 0))
        
        frames = int(duration * fps)
        for i in range(frames):
            alpha = int(255 * (1 - i / frames))
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            clock.tick(fps)
            