import tkinter as tk
import random
import math
import networkx as nx

# ==================== GLOBAL SETTINGS ==================== #
NUM_NODES = 15
NODE_RADIUS = 15
CANVAS_WIDTH = 700
CANVAS_HEIGHT = 500
UPDATE_INTERVAL_MS = 800  # BFS step interval in ms
DEFAULT_MAX_DIST = 120


class WSNRoutingDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("WSN Routing Protocol Visualization (Extended)")

        # ---------- Frame for Controls ----------
        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Start Button
        self.start_btn = tk.Button(
            self.controls_frame,
            text="Start BFS",
            command=self.start_simulation
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        # Stop Button
        self.stop_btn = tk.Button(
            self.controls_frame,
            text="Stop",
            command=self.stop_simulation,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Reset Button
        self.reset_btn = tk.Button(
            self.controls_frame,
            text="Reset",
            command=self.reset_simulation
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # Force Connected Checkbutton
        self.force_connected_var = tk.BooleanVar(value=False)
        self.force_connected_check = tk.Checkbutton(
            self.controls_frame,
            text="Force Connected Topology",
            variable=self.force_connected_var,
            command=self.toggle_force_connected
        )
        self.force_connected_check.pack(side=tk.LEFT, padx=10)

        # Max Distance Slider
        tk.Label(self.controls_frame, text="Max Dist:").pack(side=tk.LEFT, padx=(20, 2))
        self.dist_scale = tk.Scale(
            self.controls_frame, from_=50, to=300,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.update_max_dist
        )
        self.dist_scale.set(DEFAULT_MAX_DIST)
        self.dist_scale.pack(side=tk.LEFT)

        # ---------- Canvas for drawing network ----------
        self.canvas = tk.Canvas(
            self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Info Label
        self.info_label = tk.Label(
            self.root,
            text="Press 'Start BFS' to begin the routing demo."
        )
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # ---------- Graph and BFS Data Structures ----------
        self.G = nx.Graph()
        self.node_positions = {}
        self.node_ids = {}
        self.source = None
        self.destination = None

        # BFS Variables
        self.queue = []
        self.visited = set()
        self.predecessor = {}
        self.search_in_progress = False

        # Some default
        self.max_dist = DEFAULT_MAX_DIST

        # Initialize the network (possibly forcing connectivity)
        self.create_network(force_connected=self.force_connected_var.get())
        self.draw_network()

    # ==================================================================== #
    #                     NETWORK GENERATION & DRAW                        #
    # ==================================================================== #

    def create_network(self, force_connected=False):
        """
        Create a random network of NUM_NODES.
        If force_connected=True, keep regenerating until the graph is connected.
        """
        while True:
            self.G.clear()
            self.node_positions.clear()
            self.node_ids.clear()

            # 1) Add nodes with random positions
            for i in range(NUM_NODES):
                x = random.randint(NODE_RADIUS, CANVAS_WIDTH - NODE_RADIUS)
                y = random.randint(NODE_RADIUS, CANVAS_HEIGHT - NODE_RADIUS)
                self.G.add_node(i)
                self.node_positions[i] = (x, y)

            # 2) Add edges based on distance
            for i in range(NUM_NODES):
                for j in range(i + 1, NUM_NODES):
                    x1, y1 = self.node_positions[i]
                    x2, y2 = self.node_positions[j]
                    dist = math.dist((x1, y1), (x2, y2))
                    if dist <= self.max_dist:
                        self.G.add_edge(i, j)

            if not force_connected:
                break  # We don't care if it's connected; just break

            # If force_connected is True, check connectivity
            if nx.is_connected(self.G):
                break
            # Otherwise, loop again to regenerate

        # 3) Pick random source and destination
        self.source = random.choice(list(self.G.nodes()))
        # Ensure destination is different from source
        possible_targets = [n for n in self.G.nodes() if n != self.source]
        self.destination = random.choice(possible_targets)

    def draw_network(self):
        """Draw the network on the canvas."""
        self.canvas.delete("all")

        # Draw edges
        for (u, v) in self.G.edges():
            x1, y1 = self.node_positions[u]
            x2, y2 = self.node_positions[v]
            self.canvas.create_line(x1, y1, x2, y2, fill="gray", dash=(2, 2))

        # Draw nodes
        for node in self.G.nodes():
            x, y = self.node_positions[node]
            fill_color = "lightblue"
            outline_color = "black"

            # Color the source node
            if node == self.source:
                fill_color = "gold"
            # Color the destination node
            if node == self.destination:
                fill_color = "green"

            node_id = self.canvas.create_oval(
                x - NODE_RADIUS, y - NODE_RADIUS,
                x + NODE_RADIUS, y + NODE_RADIUS,
                fill=fill_color, outline=outline_color
            )
            # Write node ID
            self.canvas.create_text(x, y, text=str(node), fill="black")
            self.node_ids[node] = node_id

    # ==================================================================== #
    #                      SIMULATION (BFS) LOGIC                          #
    # ==================================================================== #

    def start_simulation(self):
        """Initialize BFS data structures and start the step-by-step BFS."""
        if self.search_in_progress:
            return  # Already in progress

        self.stop_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.DISABLED)
        self.search_in_progress = True
        self.info_label.config(
            text=f"Running BFS from {self.source} to {self.destination}..."
        )

        # Setup BFS
        self.queue = [self.source]
        self.visited = {self.source}
        self.predecessor = {}

        # Highlight source node as 'discovered'
        self.highlight_node(self.source, "orange")

        # Schedule the BFS step
        self.root.after(UPDATE_INTERVAL_MS, self.bfs_step)

    def bfs_step(self):
        """
        Perform one 'step' of BFS:
         - Dequeue one node
         - Explore its neighbors
         - If neighbor is not visited, mark visited, enqueue, set predecessor
         - If neighbor == destination, reconstruct path and finish
        """
        if not self.search_in_progress:
            return  # BFS was stopped

        if not self.queue:
            # No more nodes to explore, no path found
            self.info_label.config(
                text="No path found (disconnected subgraphs or BFS exhausted)."
            )
            self.search_in_progress = False
            self.stop_btn.config(state=tk.DISABLED)
            self.start_btn.config(state=tk.NORMAL)
            return

        current_node = self.queue.pop(0)

        for neighbor in self.G.neighbors(current_node):
            if neighbor not in self.visited:
                self.visited.add(neighbor)
                self.queue.append(neighbor)
                self.predecessor[neighbor] = current_node

                # Highlight discovered node
                self.highlight_node(neighbor, "orange")

                # Check if we've reached the destination
                if neighbor == self.destination:
                    self.search_in_progress = False
                    self.stop_btn.config(state=tk.DISABLED)
                    self.start_btn.config(state=tk.NORMAL)
                    # Build the path
                    self.build_path(neighbor)
                    return

        # Highlight the current node as 'processed'
        if current_node not in [self.source, self.destination]:
            self.highlight_node(current_node, "red")

        # Schedule next BFS step
        self.root.after(UPDATE_INTERVAL_MS, self.bfs_step)

    def build_path(self, node):
        """
        Reconstruct the path from source to destination by backtracking predecessors.
        """
        path_nodes = [node]
        while node in self.predecessor:
            node = self.predecessor[node]
            path_nodes.append(node)
        path_nodes.reverse()  # Now it goes source -> destination

        # Visually highlight the final path in green
        for idx in range(len(path_nodes) - 1):
            n1 = path_nodes[idx]
            n2 = path_nodes[idx + 1]
            self.highlight_node(n1, "limegreen")
            self.highlight_node(n2, "limegreen")

            # Optionally highlight edges as well
            x1, y1 = self.node_positions[n1]
            x2, y2 = self.node_positions[n2]
            self.canvas.create_line(x1, y1, x2, y2, fill="limegreen", width=2)

        self.info_label.config(text=f"Path found: {path_nodes}")

    def stop_simulation(self):
        """Stop (pause) BFS."""
        self.search_in_progress = False
        self.stop_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.info_label.config(text="BFS paused/stopped.")

    def reset_simulation(self):
        """Reset the network and BFS data structures."""
        self.stop_simulation()
        self.create_network(force_connected=self.force_connected_var.get())
        self.draw_network()
        self.info_label.config(
            text="Network reset. Press 'Start BFS' to run again."
        )

    # ==================================================================== #
    #                         HELPER FUNCTIONS                             #
    # ==================================================================== #

    def highlight_node(self, node, color):
        """
        Change the fill color of a node on the canvas.
        Useful for marking discovered (orange), processed (red), or final path (green).
        """
        node_id = self.node_ids[node]
        self.canvas.itemconfig(node_id, fill=color)

    def update_max_dist(self, event=None):
        """Callback for the slider to adjust max_dist dynamically."""
        self.max_dist = self.dist_scale.get()

    def toggle_force_connected(self):
        """Callback for the force-connected checkbox."""
        # Just re-generate a network using the new setting
        self.reset_simulation()


if __name__ == "__main__":
    root = tk.Tk()
    app = WSNRoutingDemo(root)
    root.mainloop()
