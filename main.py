import tkinter as tk
from tkinter import filedialog

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

        rightFrame.place_forget()
        textFrame.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        textBox.pack(fill="both", expand=True)
        scrollbar.config(command=textBox.yview)

        with open(filePath, 'r') as f:
            code = f.read()
        textBox.delete("1.0", "end")
        textBox.insert("1.0", code)

        selectBtn.place_forget()
    else:
        rightLabel.config(text="Waiting for file...")


selectBtn = tk.Button(
    leftFrame,
    text="Select File",
    command=selectfile,
    bg="white",
    fg="black",
    font=("Arial", 12),
)

parseBtn = tk.Button(
    leftFrame,
    text="Parse File",
    command=selectfile,
    bg="white",
    fg="black",
    font=("Arial", 12),
)

diagramBtn = tk.Button(
    leftFrame,
    text="Show Diagram",
    command=selectfile,
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
