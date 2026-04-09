import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Initialize the plot
fig, ax = plt.subplots(figsize=(12, 8))

# Define positions for blocks
positions = {
    "High-Level Portside": (1, 8),
    "High-Level Communication": (5, 8),
    "Mid-Level Shipside": (1, 6),
    "Mid-Level Communication": (5, 6),
    "Low-Level Shipside": (1, 4),
    "Low-Level Communication": (5, 4),
}

# Define the connections between blocks
connections = [
    ("High-Level Portside", "High-Level Communication"),
    ("High-Level Communication", "Mid-Level Communication"),
    ("Mid-Level Communication", "Mid-Level Shipside"),
    ("Mid-Level Shipside", "Low-Level Shipside"),
    ("Low-Level Communication", "Low-Level Shipside"),
]

# Draw rectangles for each block
for name, (x, y) in positions.items():
    ax.add_patch(patches.Rectangle((x, y), 3, 1, edgecolor="black", facecolor="lightblue"))
    ax.text(x + 1.5, y + 0.5, name, ha="center", va="center", fontsize=10, fontweight="bold")

# Draw connections
for start, end in connections:
    start_x, start_y = positions[start]
    end_x, end_y = positions[end]
    ax.annotate(
        "",
        xy=(end_x + 1.5, end_y + 1),
        xytext=(start_x + 1.5, start_y),
        arrowprops=dict(arrowstyle="->", color="black"),
    )

# Add labels for better understanding
ax.text(0.5, 9, "Inputs", fontsize=12, fontweight="bold")
ax.text(8, 1, "Outputs", fontsize=12, fontweight="bold")

# Set plot limits and aesthetics
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")
plt.title("Decision-Making Architecture: Block Diagram", fontsize=14, fontweight="bold")
plt.show()
