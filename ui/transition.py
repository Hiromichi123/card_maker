"""
场景转场效果
"""
import pygame

class Transition:
    """转场效果类"""
    
    @staticmethod
    def fade_out(screen, duration=0.5, fps=60):
        """淡出效果"""
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
        """淡入效果"""
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