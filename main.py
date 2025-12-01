import pygame
import pygame.gfxdraw
import pygame_gui
import tkinter as tk
from tkinter import filedialog
import networkx as nx
import math
import ast
import re

filePath = ''

filetypestext = ("png", "jpg", "tiff")

save_file_buttons = {}
name_input = None
enter_name = None

# File dialog setup
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

# Available Colors
ORANGE = (255, 100, 50)
BLUE = (100, 150, 255)
GREEN = (100, 200, 150)
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE2 = (0, 65, 140)

# Dragging nodes
dragging_node = None
offset_x, offset_y = 0, 0

def parse_file(file_name):
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


    with open(file_name, 'r') as file:
        sourceCode = file.read()
    tree = ast.parse(sourceCode, filename=file_name)

    # Assign parent references
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    # Extract functions and classes
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    analyzedFunctions = {}
    class_to_funcs = {}

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
    
    return analyzedFunctions, class_to_funcs, classes


def draw_graph(analyzedFunctions, class_to_funcs, classes):
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

    # Add classes by themselves
    for cls in classes:
        if cls.name not in G:
            G.add_node(cls.name, type='class')

    
    # Node layout
    pos = nx.nx_agraph.graphviz_layout(G, prog="neato",args="-Gstart=44")
 
    def scale_positions(pos):
        xs = [x for x, y in pos.values()]
        ys = [y for x, y in pos.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        scaled = {}
        for node, (x,y) in pos.items():
            nx = (x - min_x) / (max_x - min_x)
            ny = (y - min_y) / (max_y - min_y)
            
            sx = 50 + nx * 668
            sy = 50 + ny * 668
            
            scaled[node] = [sx, sy]
        
        return scaled
        
    scaled_pos = scale_positions(pos)

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
    
    return node_sizes, scaled_pos, box_intersection, G













# Pygame Setup
pygame.init()
pygame.display.set_caption('Code Visualizer')
screen = pygame.display.set_mode((1024, 768))
background = pygame.Surface((1024, 768))
background.fill(WHITE)
manager = pygame_gui.UIManager((1024, 768))
clock = pygame.time.Clock()

# Create a font
font1 = pygame.font.Font(None, 28)
font2 = pygame.font.Font(None, 18)

# Graph area
graph_box = pygame.Rect(256,0,768,768)
graph_surface = screen.subsurface(graph_box)

# Create UI buttons 
select_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(51,320,160,32), text='Select File', manager=manager)
parse_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(51,369,160,32), text='Parse File', manager=manager)
diagram_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(51,417,160,32), text='Show Diagram', manager=manager)
save_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(-500,-500, 160,32),text='Save Image',manager=manager)

# UI area creation
def make_ui():
    pygame.draw.rect(screen, BLUE2, (0,0,256,768))
    
# Text filed creation
name_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(-500, 252, 300, 25), manager=manager)
name_input.enable()
enter_name = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(-500, 252, 100, 25), text="Save", manager=manager)    
    
def save_file():
    global save_file_buttons, name_input, enter_name
    
    # Create file dialog area
    file_dialog_box = pygame.Rect(192,192,640,384)
    file_dialog_surface = screen.subsurface(file_dialog_box)
    
    # pygame.draw.rect(file_dialog_surface, BLUE, (0,0,640,384))
    
    # Text setup
    text = font1.render("Enter File Name Then Select Extension", True, BLACK)
    text_area = text.get_rect(midtop=(file_dialog_surface.get_width()//2, 10))
    
    name_input.set_relative_position((file_dialog_surface.get_width()//2,252))
    enter_name.set_relative_position((file_dialog_surface.get_width()//2 + 300,252))
    
    
    #Button creation
    if len(save_file_buttons) != 3:
        for i in range(3):
            gapsize = 20
            height = 32
            width = (640 - (gapsize * 5)) // 3
            x = (gapsize * 2 + i * width)  + 192
            y = 588 - 192
            
            rect = pygame.Rect(x,y,width,height)
            save_file_buttons[filetypestext[i]] = pygame_gui.elements.UIButton(relative_rect=rect, text=filetypestext[i], manager=manager)
    
    file_dialog_surface.blit(text, text_area)
        
    
    
    
is_running = True
displayText = 0 # 0 = pre file selected, 1 = after file selected, 2 = after parse button pressed, anything else = no text display
savefile = False
while is_running:

    time_delta = clock.tick(60)/1000.0

    for event in pygame.event.get():
        
        if displayText >= 3:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                mx -= graph_box.x
                my -= graph_box.y
                
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
                mx -= graph_box.x
                my -= graph_box.y
                
                scaled_pos[dragging_node][0] = mx + offset_x
                scaled_pos[dragging_node][1] = my + offset_y

        if event.type == pygame.QUIT:

            is_running = False


        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            if event.ui_element == select_button:
                filePath = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
                if filePath:
                    displayText = 1
            elif event.ui_element == parse_button:
                if displayText == 1:
                    analyzedFunctions, class_to_funcs, classes = parse_file(filePath)
                    displayText = 2
            elif event.ui_element == diagram_button:
                if displayText == 2:
                    node_sizes, scaled_pos, box_intersection, G = draw_graph(analyzedFunctions, class_to_funcs, classes)
                    displayText = 3
            elif event.ui_element == save_button:
                if displayText >= 3 and save_button.get_relative_rect().topleft == (51,672):
                    savefile = not savefile     # Toggle between True and False when button pressed 
            elif event.ui_element == enter_name:
                name = name_input.get_text()
                if re.match(r".*\.(png|jpg|tiff|pdf|svg)$", name):
                    savefile = False
            else:
                for ext, button in save_file_buttons.items():
                    if event.ui_element == button:
                        name = name_input.get_text()
                        if not name:
                            name = "output"
                        name = name + "." + ext
                        name_input.set_text(name)   
            
        manager.process_events(event)

    manager.update(time_delta)

    screen.blit(background, (0, 0))
    
    # Display the correct helper text
    text = None
    match displayText:
        case 0:
            text = font1.render("Please Select a File", True, BLACK)
        case 1:
            text = font1.render("File Ready to Parse", True, BLACK)
        case 2:
            text = font1.render("Graph Ready to be Displayed", True, BLACK)

    if displayText < 3:
        graph_area = text.get_rect(center=graph_box.center)
        screen.blit(text, graph_area)
        
        
    if displayText >= 3:
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
        
        # Recompute node sizes each frame so font/text changes work
        node_sizes.clear()
        for n in scaled_pos:
            label = font2.render(str(n), True, (0, 0, 0))
            lw, lh = label.get_width(), label.get_height()
            pad_x = 40
            pad_y = 20
            w = lw + pad_x
            h = lh + pad_y
            node_sizes[n] = (w, h)
            

        screen.fill((255, 255, 255))

        for u, v in G.edges():
            draw_arrow(graph_surface, (0, 0, 0), scaled_pos[u], scaled_pos[v], node_sizes[v])

        for n, (x, y) in scaled_pos.items():
            node_type = G.nodes[n]['type'] if G.nodes[n] != {} else 0
            
            w, h = node_sizes[n]
            rect = pygame.Rect(x - w//2, y - h//2, w, h)

        
            if node_type:   # GREEN = Function  BLUE = Class    ORANGE = Predefined function from python
                if node_type == "function":
                    pygame.draw.rect(graph_surface, GREEN, rect, border_radius=8) 
                else:
                    pygame.draw.rect(graph_surface, BLUE, rect, border_radius=8) 
            else:
                pygame.draw.rect(graph_surface, ORANGE, rect, border_radius=8) 
        

            pygame.draw.rect(graph_surface, (0, 0, 0), rect, width=2, border_radius=8)

            label = font2.render(str(n), True, (255, 255, 255))
            graph_surface.blit(label, (x - label.get_width()//2, y - label.get_height()//2))
    
    if displayText == 3:
        save_button.set_relative_position((51, 672))
    else:
        save_button.set_relative_position((-500, -500))
    
    make_ui()
    
    if savefile:
        save_file()
    else:
        size = len(save_file_buttons)
        name_input.set_relative_position((-500,252))
        enter_name.set_relative_position((-500,252))
        for button in save_file_buttons.items():
            button[1].kill()
        save_file_buttons = {}
        if size:
            name = name_input.get_text()
            if name:
                pygame.image.save(graph_surface, name)
        
    manager.draw_ui(screen)
   
    pygame.display.update()