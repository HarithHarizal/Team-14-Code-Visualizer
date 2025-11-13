import tkinter as tk
from tkinter import filedialog
import pygame
import pygame.gfxdraw
import networkx as nx
import math
import ast

code = ''

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












# Create main window
root = tk.Tk()
root.title("Source Code Visualizer")
root.geometry("1000x600")

# Right white frame
rightFrame = tk.Frame(root, bg="white")
rightFrame.pack(side="right", fill="both", expand=True)

rightLabel = tk.Label(
    rightFrame,
    text="Waiting for file...",
    bg="white",
    fg="gray",
    font=("Arial", 16),
)
rightLabel.place(relx=0.5, rely=0.5, anchor="center")

# Scrollable text display box
textFrame = tk.Frame(rightFrame, bg="white")
scrollbar = tk.Scrollbar(textFrame)
textBox = tk.Text(
    textFrame,
    wrap="word",
    yscrollcommand=scrollbar.set,
    bg="white",
    fg="black",
    font=("Consolas", 12),
)

# Left gray frame
leftFrame = tk.Frame(root, bg="#d3d3d3", width=250)
leftFrame.pack(side="left", fill="y")


# Setup Select Button
def selectfile():
    filePath = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
    if filePath:
        global code
        
        with open(filePath, 'r') as f:
            code = f.read()
    else:
        rightLabel.config(text="Waiting for file...")


def parsecode():
    global analyzedFunctions, class_to_funcs,classes
    
    # --- Parse file ---
    tree = ast.parse(code)

    # --- Assign parent references so we know which class a function belongs to ---
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    # --- Extract functions and classes ---
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    analyzedFunctions = {}
    class_to_funcs = {}

    # --- Analyze functions ---
    for func in functions:
        analyzer = analyzeFunction(func)
        analyzedFunctions[analyzer.name] = {
            'variables': analyzer.variables,
            'calls': set(analyzer.calls) if analyzer.calls else [],
            'returns': analyzer.returns
        }

        # Check if this function is inside a class (now parent exists)
        parent = getattr(func, "parent", None)
        if isinstance(parent, ast.ClassDef):
            class_to_funcs.setdefault(parent.name, []).append(analyzer.name)


def showdiagram():
    # --- Build graph ---
    G = nx.DiGraph()

    # Add all function nodes and edges
    for key, data in analyzedFunctions.items():
        G.add_node(key, type='function')
        for call in data['calls']:
            G.add_edge(key, call)

    # Add class nodes and edges to their internal functions
    for class_name, funcs in class_to_funcs.items():
        G.add_node(class_name, type='class')
        for func in funcs:
            if func in G:
                G.add_edge(class_name, func)

    # Add standalone classes (no functions)
    for cls in classes:
        if cls.name not in G:
            G.add_node(cls.name, type='class')

    # --- Layout ---
    isPlanar = nx.is_planar(G)
    pos = nx.planar_layout(G) if isPlanar else nx.circular_layout(G)

    # --- Normalize positions ---
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

    # --- Pygame setup ---
    pygame.init()
    WIDTH, HEIGHT = 900, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Code Graph Visualizer")
    clock = pygame.time.Clock()

    scaled_pos = normalize_positions(pos, WIDTH, HEIGHT)
    NODE_RADIUS = 25

    # --- Draw arrows ---
    def draw_arrow(screen, color, start, end, width=2, arrow_size=14, angle=25, node_radius=NODE_RADIUS):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ux, uy = dx / dist, dy / dist
        adjusted_end = (end[0] - ux * node_radius, end[1] - uy * node_radius)
        adjusted_start = (start[0] + ux * node_radius, start[1] + uy * node_radius)
        pygame.gfxdraw.line(screen, int(adjusted_start[0]), int(adjusted_start[1]),
                            int(adjusted_end[0]), int(adjusted_end[1]), color)
        base_x = adjusted_end[0] - arrow_size * ux
        base_y = adjusted_end[1] - arrow_size * uy
        def rotate(px, py, theta):
            return px * math.cos(theta) - py * math.sin(theta), px * math.sin(theta) + py * math.cos(theta)
        
        left_angle = math.radians(angle)
        right_angle = -math.radians(angle)
        left_dx, left_dy = rotate(-ux, -uy, left_angle)
        right_dx, right_dy = rotate(-ux, -uy, right_angle)
        left_pt = (base_x + left_dx * arrow_size, base_y + left_dy * arrow_size)
        right_pt = (base_x + right_dx * arrow_size, base_y + right_dy * arrow_size)
        
        pts = [(int(adjusted_end[0]), int(adjusted_end[1])),
            (int(left_pt[0]), int(left_pt[1])),
            (int(right_pt[0]), int(right_pt[1]))]
        pygame.gfxdraw.filled_polygon(screen, pts, color)
        pygame.gfxdraw.aapolygon(screen, pts, color)

    # --- Dragging setup ---
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

        screen.fill((255, 255, 255))

        # --- Draw edges ---
        for u, v in G.edges():
            draw_arrow(screen, (0, 0, 0), scaled_pos[u], scaled_pos[v])

        # --- Draw nodes ---
        for n, (x, y) in scaled_pos.items():
            node_type = G.nodes[n].get('type', 'function')
            color = (100, 150, 255) if node_type == 'function' else (255, 170, 60)
            
            if node_type == 'function':
                pygame.gfxdraw.filled_circle(screen, int(x), int(y), NODE_RADIUS, color)
                pygame.gfxdraw.aacircle(screen, int(x), int(y), NODE_RADIUS, color)
            else:
                pygame.gfxdraw.box(screen, (int(x)-NODE_RADIUS, int(y)-NODE_RADIUS, 60,45), color)

            font = pygame.font.SysFont(None, 22)
            label = font.render(str(n), True, (0, 0, 0))
            screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# Need to save file to access later
selectBtn = tk.Button(
    leftFrame,
    text="Select File",
    command=selectfile,
    bg="white",
    fg="black",
    font=("Arial", 12),
)

# Need to Parse file 
parseBtn = tk.Button(
    leftFrame,
    text="Parse File",
    command=parsecode,
    bg="white",
    fg="black",
    font=("Arial", 12),
)

# Create new window to show diagram
diagramBtn = tk.Button(
    leftFrame,
    text="Show Diagram",
    command=showdiagram,
    bg="white",
    fg="black",
    font=("Arial", 12),
)

selectBtn.pack(pady=20)
selectBtn.place(relx=0.5, rely=0.05, anchor="n")
parseBtn.pack(pady=20)
parseBtn.place(relx=0.5, rely=0.15, anchor = "n")
diagramBtn.pack(pady=20)
diagramBtn.place(relx=0.5, rely=0.25, anchor = "n")

root.mainloop()