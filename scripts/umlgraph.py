from graphviz import Digraph
from pathlib import Path

# Create a directed graph for UML
uml = Digraph(format='png', graph_attr={"rankdir": "TB"})
uml.attr("node", shape="record")

# Add classes and their attributes/methods
uml.node("Main", """
Main |
+ window_width, window_height, slider_width, WHITE, GRAY, font |
+ create_robots(), button_clicked(), handle_events(), draw_slider()
""")

uml.node("Robot", """
Robot |
+ position, heading |
+ is_clicked(), get_rps_values(), set_rps_values(), move(), draw()
""")

uml.node("Pygame", """
Pygame |
+ display, event |
+ init(), quit(), draw(), flip()
""")

uml.node("Utils", """
Utils |
+ draw_button(), draw_slider(), draw_selected_rpm(), draw_noise_std_inputs()
""")

uml.node("Config", """
Config |
+ num_usvs, panel_height |
+ start_button, stop_button, add_robot_button, slider_rect
""")

# Define relationships
uml.edge("Main", "Robot", label="uses")
uml.edge("Main", "Pygame", label="interacts")
uml.edge("Main", "Utils", label="uses")
uml.edge("Main", "Config", label="uses")

# Render the UML diagram
uml_file_path = Path(__file__).resolve().parent / "uml_diagram"
uml.render(uml_file_path, cleanup=True)

uml_file_path
