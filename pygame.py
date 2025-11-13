import pygame
import pygame.gfxdraw
import networkx as nx
import math

# --- Create a random graph ---
G = nx.erdos_renyi_graph(10, 0.3)
pos = nx.spring_layout(G, seed=42)

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smooth Network Graph with Draggable Nodes and Arrows")
clock = pygame.time.Clock()

# --- Normalize and scale layout positions ---
def normalize_positions(pos, width, height, margin=80):
    xs = [x for x, y in pos.values()]
    ys = [y for x, y in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    scaled = {}
    for node, (x, y) in pos.items():
        nx_ = (x - min_x) / (max_x - min_x)
        ny_ = (y - min_y) / (max_y - min_y)
        sx = margin + nx_ * (width - 2 * margin)
        sy = margin + ny_ * (height - 2 * margin)
        scaled[node] = [int(sx), int(sy)]  # store as list (mutable)
    return scaled

scaled_pos = normalize_positions(pos, WIDTH, HEIGHT)
NODE_RADIUS = 20

# --- Arrow drawing function ---
def draw_arrow(screen, color, start, end, width=2, arrow_size=14, angle=25, node_radius=NODE_RADIUS):
    """Draw a directed edge with an anti-aliased arrowhead."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return

    # Shorten the line to avoid overlapping node circles
    ux, uy = dx / dist, dy / dist
    adjusted_end = (end[0] - ux * node_radius, end[1] - uy * node_radius)
    adjusted_start = (start[0] + ux * node_radius, start[1] + uy * node_radius)

    # Draw anti-aliased line
    pygame.gfxdraw.line(screen, int(adjusted_start[0]), int(adjusted_start[1]),
                        int(adjusted_end[0]), int(adjusted_end[1]), color)

    # Arrowhead base
    base_x = adjusted_end[0] - arrow_size * ux
    base_y = adjusted_end[1] - arrow_size * uy

    # Rotate the direction vector for two arrow sides
    left_angle = math.radians(angle)
    right_angle = -math.radians(angle)

    def rotate(px, py, theta):
        return px * math.cos(theta) - py * math.sin(theta), px * math.sin(theta) + py * math.cos(theta)

    left_dx, left_dy = rotate(-ux, -uy, left_angle)
    right_dx, right_dy = rotate(-ux, -uy, right_angle)

    left_pt = (base_x + left_dx * arrow_size, base_y + left_dy * arrow_size)
    right_pt = (base_x + right_dx * arrow_size, base_y + right_dy * arrow_size)

    pts = [(int(adjusted_end[0]), int(adjusted_end[1])),
           (int(left_pt[0]), int(left_pt[1])),
           (int(right_pt[0]), int(right_pt[1]))]

    # Draw smooth arrowhead
    pygame.gfxdraw.filled_polygon(screen, pts, color)
    pygame.gfxdraw.aapolygon(screen, pts, color)

# --- Node dragging setup ---
dragging_node = None
offset_x, offset_y = 0, 0

# --- Main loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Check if user clicked a node
            for n, (x, y) in scaled_pos.items():
                if math.hypot(mx - x, my - y) <= NODE_RADIUS:
                    dragging_node = n
                    offset_x = x - mx
                    offset_y = y - my
                    break

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging_node = None

        elif event.type == pygame.MOUSEMOTION and dragging_node is not None:
            mx, my = pygame.mouse.get_pos()
            scaled_pos[dragging_node][0] = mx + offset_x
            scaled_pos[dragging_node][1] = my + offset_y

    # --- Drawing ---
    screen.fill((255, 255, 255))

    # Draw edges as arrows
    for u, v in G.edges():
        draw_arrow(screen, (0, 0, 0), scaled_pos[u], scaled_pos[v])

    # Draw smooth nodes
    for n, (x, y) in scaled_pos.items():
        pygame.gfxdraw.filled_circle(screen, int(x), int(y), NODE_RADIUS, (100, 150, 255))
        pygame.gfxdraw.aacircle(screen, int(x), int(y), NODE_RADIUS, (100, 150, 255))

        # Draw label
        font = pygame.font.SysFont(None, 24)
        label = font.render(str(n), True, (0, 0, 0))
        screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
