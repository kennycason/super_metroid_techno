"""
CHAOS EFFECT - Mathematical Visual Madness
A celebration of computational beauty and chaos
"""

import pygame
import math
import random
import numpy as np


class ChaosEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
        
        # Particle system
        self.particles = []
        self.max_particles = 200
        
        # Fractal parameters
        self.fractal_depth = 0
        self.fractal_angle = 0
        
        # Strange attractor state
        self.attractor_points = []
        self.attractor_x = 0.1
        self.attractor_y = 0.0
        self.attractor_z = 0.0
        
        # Voronoi points
        self.voronoi_points = []
        self.regenerate_voronoi()
        
        # Lissajous parameters
        self.lissajous_a = 3
        self.lissajous_b = 4
        self.lissajous_delta = 0
        
        # Kaleidoscope
        self.kaleidoscope_segments = 8
        
        # Initialize particles
        self.spawn_particles(50)
    
    def spawn_particles(self, count):
        """Spawn new particles"""
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                particle = {
                    'x': random.uniform(0, self.width),
                    'y': random.uniform(0, self.height),
                    'vx': random.uniform(-3, 3),
                    'vy': random.uniform(-3, 3),
                    'size': random.uniform(2, 8),
                    'hue': random.uniform(0, 360),
                    'life': 1.0,
                    'decay': random.uniform(0.003, 0.01)
                }
                self.particles.append(particle)
    
    def regenerate_voronoi(self):
        """Generate new Voronoi points"""
        self.voronoi_points = []
        for _ in range(12):
            self.voronoi_points.append({
                'x': random.uniform(0, self.width),
                'y': random.uniform(0, self.height),
                'hue': random.uniform(0, 360),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2)
            })
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def update(self):
        """Update all chaos systems"""
        self.time += 1
        
        # Update particles with attraction/repulsion
        center_x = self.width / 2
        center_y = self.height / 2
        
        for particle in self.particles[:]:
            # Apply attraction to center with oscillation
            dx = center_x - particle['x']
            dy = center_y - particle['y']
            dist = math.sqrt(dx * dx + dy * dy) + 0.1
            
            # Oscillating force field
            force = math.sin(self.time * 0.05 + dist * 0.02) * 0.5
            particle['vx'] += (dx / dist) * force
            particle['vy'] += (dy / dist) * force
            
            # Rotational force
            angle = math.atan2(dy, dx) + math.pi / 2
            particle['vx'] += math.cos(angle) * 0.3
            particle['vy'] += math.sin(angle) * 0.3
            
            # Apply velocity with damping
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vx'] *= 0.98
            particle['vy'] *= 0.98
            
            # Wrap around screen
            particle['x'] %= self.width
            particle['y'] %= self.height
            
            # Color cycle
            particle['hue'] = (particle['hue'] + 1) % 360
            
            # Life decay
            particle['life'] -= particle['decay']
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Spawn new particles
        if len(self.particles) < self.max_particles and self.time % 3 == 0:
            self.spawn_particles(2)
        
        # Update strange attractor (Lorenz system)
        dt = 0.01
        sigma = 10.0
        rho = 28.0
        beta = 8.0 / 3.0
        
        dx = sigma * (self.attractor_y - self.attractor_x) * dt
        dy = (self.attractor_x * (rho - self.attractor_z) - self.attractor_y) * dt
        dz = (self.attractor_x * self.attractor_y - beta * self.attractor_z) * dt
        
        self.attractor_x += dx
        self.attractor_y += dy
        self.attractor_z += dz
        
        # Map to screen coordinates
        screen_x = int(self.width / 2 + self.attractor_x * 10)
        screen_y = int(self.height / 2 + self.attractor_y * 10)
        
        self.attractor_points.append((screen_x, screen_y))
        if len(self.attractor_points) > 500:
            self.attractor_points.pop(0)
        
        # Update Voronoi points
        for point in self.voronoi_points:
            point['x'] += point['vx']
            point['y'] += point['vy']
            
            # Bounce off edges
            if point['x'] < 0 or point['x'] > self.width:
                point['vx'] *= -1
            if point['y'] < 0 or point['y'] > self.height:
                point['vy'] *= -1
            
            point['x'] = max(0, min(self.width, point['x']))
            point['y'] = max(0, min(self.height, point['y']))
            
            point['hue'] = (point['hue'] + 0.5) % 360
        
        # Update fractal parameters
        self.fractal_angle += 0.02
        self.fractal_depth = int(3 + 2 * math.sin(self.time * 0.01))
        
        # Update Lissajous parameters
        self.lissajous_delta += 0.02
    
    def draw(self, surface):
        """Draw all chaos effects"""
        # Create layers for different effects
        
        # Layer 1: Voronoi diagram (background)
        self.draw_voronoi(surface)
        
        # Layer 2: Geometric patterns
        self.draw_geometric_chaos(surface)
        
        # Layer 3: Strange attractor
        self.draw_strange_attractor(surface)
        
        # Layer 4: Particles
        self.draw_particles(surface)
        
        # Layer 5: Fractals
        self.draw_fractals(surface)
        
        # Layer 6: Lissajous curves
        self.draw_lissajous(surface)
        
        # Layer 7: Kaleidoscope overlay
        if self.time % 60 < 30:  # Alternate
            self.draw_kaleidoscope(surface)
    
    def draw_voronoi(self, surface):
        """Draw animated Voronoi diagram"""
        # Sample points to create Voronoi cells
        step = 20
        for x in range(0, self.width, step):
            for y in range(0, self.height, step):
                # Find closest Voronoi point
                min_dist = float('inf')
                closest_point = None
                
                for point in self.voronoi_points:
                    dx = x - point['x']
                    dy = y - point['y']
                    dist = dx * dx + dy * dy
                    if dist < min_dist:
                        min_dist = dist
                        closest_point = point
                
                if closest_point:
                    # Color based on distance and hue
                    intensity = min(1.0, min_dist / 50000)
                    color = self.hsv_to_rgb(closest_point['hue'], 0.6, 0.3 + intensity * 0.3)
                    pygame.draw.rect(surface, color, (x, y, step, step))
    
    def draw_particles(self, surface):
        """Draw particle system"""
        for particle in self.particles:
            color = self.hsv_to_rgb(particle['hue'], 1.0, particle['life'])
            size = int(particle['size'] * particle['life'])
            if size > 0:
                pygame.draw.circle(surface, color, 
                                 (int(particle['x']), int(particle['y'])), size)
                
                # Draw trails
                trail_x = int(particle['x'] - particle['vx'] * 3)
                trail_y = int(particle['y'] - particle['vy'] * 3)
                pygame.draw.line(surface, color, 
                               (int(particle['x']), int(particle['y'])),
                               (trail_x, trail_y), 2)
    
    def draw_strange_attractor(self, surface):
        """Draw Lorenz strange attractor"""
        if len(self.attractor_points) > 1:
            for i in range(len(self.attractor_points) - 1):
                hue = (i * 2 + self.time) % 360
                color = self.hsv_to_rgb(hue, 0.8, 0.8)
                alpha = int(255 * (i / len(self.attractor_points)))
                
                try:
                    pygame.draw.line(surface, color, 
                                   self.attractor_points[i], 
                                   self.attractor_points[i + 1], 2)
                except:
                    pass
    
    def draw_fractals(self, surface):
        """Draw recursive fractal patterns"""
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Sierpinski-like pattern
        self.draw_recursive_triangle(surface, center_x, center_y, 
                                    150, self.fractal_angle, self.fractal_depth)
    
    def draw_recursive_triangle(self, surface, x, y, size, angle, depth):
        """Draw recursive triangular pattern"""
        if depth <= 0 or size < 5:
            return
        
        hue = (depth * 60 + self.time * 2) % 360
        color = self.hsv_to_rgb(hue, 0.8, 0.9)
        
        # Draw triangle points
        points = []
        for i in range(3):
            angle_rad = angle + i * (2 * math.pi / 3)
            px = x + math.cos(angle_rad) * size
            py = y + math.sin(angle_rad) * size
            points.append((px, py))
        
        if len(points) == 3:
            pygame.draw.polygon(surface, color, points, 2)
        
        # Recurse
        for px, py in points:
            self.draw_recursive_triangle(surface, px, py, size * 0.5, 
                                        angle + 0.1, depth - 1)
    
    def draw_lissajous(self, surface):
        """Draw Lissajous curves"""
        points = []
        for t in range(0, 360, 2):
            t_rad = math.radians(t)
            x = self.width / 2 + 150 * math.sin(self.lissajous_a * t_rad + self.lissajous_delta)
            y = self.height / 2 + 150 * math.sin(self.lissajous_b * t_rad)
            points.append((x, y))
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                hue = (i * 2 + self.time) % 360
                color = self.hsv_to_rgb(hue, 0.9, 0.7)
                pygame.draw.line(surface, color, points[i], points[i + 1], 3)
    
    def draw_geometric_chaos(self, surface):
        """Draw chaotic geometric patterns"""
        # Rotating squares/diamonds
        center_x = self.width / 2
        center_y = self.height / 2
        
        for i in range(8):
            angle = self.time * 0.02 + i * math.pi / 4
            distance = 100 + 50 * math.sin(self.time * 0.03 + i)
            
            x = center_x + math.cos(angle) * distance
            y = center_y + math.sin(angle) * distance
            
            size = 30 + 20 * math.sin(self.time * 0.05 + i)
            rotation = self.time * 0.05 + i
            
            hue = (i * 45 + self.time) % 360
            color = self.hsv_to_rgb(hue, 0.9, 0.8)
            
            # Draw rotated square
            points = []
            for j in range(4):
                corner_angle = rotation + j * math.pi / 2
                px = x + math.cos(corner_angle) * size
                py = y + math.sin(corner_angle) * size
                points.append((px, py))
            
            pygame.draw.polygon(surface, color, points, 2)
    
    def draw_kaleidoscope(self, surface):
        """Draw kaleidoscope effect"""
        # This is just adding some radial symmetry overlays
        center_x = self.width / 2
        center_y = self.height / 2
        
        for seg in range(self.kaleidoscope_segments):
            angle = seg * (2 * math.pi / self.kaleidoscope_segments)
            
            # Draw radial lines with oscillating length
            length = 200 + 100 * math.sin(self.time * 0.03 + seg)
            end_x = center_x + math.cos(angle + self.time * 0.01) * length
            end_y = center_y + math.sin(angle + self.time * 0.01) * length
            
            hue = (seg * (360 / self.kaleidoscope_segments) + self.time * 2) % 360
            color = self.hsv_to_rgb(hue, 0.8, 0.6)
            
            pygame.draw.line(surface, color, (center_x, center_y), 
                           (end_x, end_y), 4)
            
            # Draw circles at endpoints
            pygame.draw.circle(surface, color, (int(end_x), int(end_y)), 
                             int(10 + 5 * math.sin(self.time * 0.1)))

