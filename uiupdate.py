import pygame
import pygame.gfxdraw
import networkx as nx
from PIL import Image, ImageDraw, ImageFont
import math
import ast
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import matplotlib.image as mpimg

file_name = "uiupdate.py"


class analyzeFunction(ast.NodeVisitor):
    def __init__(self, funcNode):
        self.name = funcNode.name
        self.variables = []
        self.calls = []
        self.returns = []
        self.visit(funcNode)

    def visit_Assign(self, node):
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        self.variables.extend(targets)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        self.generic_visit(node)

    def visit_Return(self, node):
        if node.value:
            self.returns.append(ast.dump(node.value))
        self.generic_visit(node)


# Load and parse
with open(file_name, 'r') as file:
    sourceCode = file.read()
tree = ast.parse(sourceCode, filename=file_name)

functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

analyzedFunctions = {}
for func in functions:
    analyzer = analyzeFunction(func)
    analyzedFunctions[analyzer.name] = {
        'variables': analyzer.variables,
        'calls': set(analyzer.calls) if analyzer.calls != [] else analyzer.calls,
        'returns': analyzer.returns}

G = nx.DiGraph()
edges = []
for key in analyzedFunctions:
    edges.append((key, ''))
    for call in analyzedFunctions[key]['calls']:
        if edges[-1][-1] == '':
            edges.pop()
        edges.append((key, call))

G.add_edges_from(edges)

pos = nx.spring_layout(G, seed=42)

pygame.init()
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Network Graph: node testing")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
img = Image.open('./pipeline.jpg')
img.save('testoutput.jpg')

# Normalize spring layout
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
        scaled[node] = [int(sx), int(sy)]
    return scaled

scaled_pos = normalize_positions(pos, WIDTH, HEIGHT)

# Dynamic node sizes stored here
node_sizes = {}


# Compute intersection of a line with a box of size w×h
def box_intersection(start, end, w, h):
    dx = end[0] - start[0]
    dy = end[1] - start[1]

    if dx == 0:
        return (end[0], end[1] - math.copysign(h/2, dy))

    slope = dy / dx

    if abs(slope) <= (h / w):
        x = end[0] - math.copysign(w/2, dx)
        y = start[1] + slope * (x - start[0])
    else:
        y = end[1] - math.copysign(h/2, dy)
        x = start[0] + (y - start[1]) / slope

    return (x, y)


def draw_arrow(screen, color, start, end, target_size):

    w, h = target_size
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return

    adjusted_end = box_intersection(start, end, w, h)
    adjusted_start = box_intersection(end, start, w, h)

    pygame.gfxdraw.line(
        screen,
        int(adjusted_start[0]), int(adjusted_start[1]),
        int(adjusted_end[0]), int(adjusted_end[1]),
        color
    )

    ux = dx / dist
    uy = dy / dist

    arrow_size = 14
    base_x = adjusted_end[0] - arrow_size * ux
    base_y = adjusted_end[1] - arrow_size * uy

    angle = math.radians(25)

    def rotate(px, py, theta):
        return px * math.cos(theta) - py * math.sin(theta), px * math.sin(theta) + py * math.cos(theta)

    left_dx, left_dy = rotate(-ux, -uy, angle)
    right_dx, right_dy = rotate(-ux, -uy, -angle)

    left_pt = (base_x + left_dx * arrow_size, base_y + left_dy * arrow_size)
    right_pt = (base_x + right_dx * arrow_size, base_y + right_dy * arrow_size)

    pts = [
        (int(adjusted_end[0]), int(adjusted_end[1])),
        (int(left_pt[0]), int(left_pt[1])),
        (int(right_pt[0]), int(right_pt[1]))
    ]

    pygame.gfxdraw.filled_polygon(screen, pts, color)
    pygame.gfxdraw.aapolygon(screen, pts, color)


dragging_node = None
offset_x, offset_y = 0, 0

running = True
while running:
    # Recompute node sizes each frame so font/text changes work
    node_sizes.clear()
    for n in scaled_pos:
        label = font.render(str(n), True, (0, 0, 0))
        lw, lh = label.get_width(), label.get_height()
        pad_x = 40
        pad_y = 20
        w = lw + pad_x
        h = lh + pad_y
        node_sizes[n] = (w, h)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            for n, (x, y) in scaled_pos.items():
                w, h = node_sizes[n]
                rect = pygame.Rect(x - w//2, y - h//2, w, h)
                if rect.collidepoint(mx, my):
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

    screen.fill((255, 255, 255))

    for u, v in G.edges():
        draw_arrow(screen, (0, 0, 0), scaled_pos[u], scaled_pos[v], node_sizes[v])

    for n, (x, y) in scaled_pos.items():
        w, h = node_sizes[n]
        rect = pygame.Rect(x - w//2, y - h//2, w, h)

      # (100, 200, 150) Is Green, but Original blue is (100, 150, 255)
      # I am thinking of having colors be variables instead of int values so its easier to change, and can involve some user customization. For the future.
        pygame.draw.rect(screen, (100, 200, 150), rect, border_radius=8) 
        pygame.draw.rect(screen, (0, 0, 0), rect, width=2, border_radius=8)

        label = font.render(str(n), True, (255, 255, 255))
        screen.blit(label, (x - label.get_width()//2, y - label.get_height()//2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
