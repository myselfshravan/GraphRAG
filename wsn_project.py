import tkinter as tk
from tkinter import ttk
import random
import math
from tkinter import messagebox


# =========================================
# =           Node Class                 =
# =========================================

class Node:
    def __init__(self, node_id, x, y, energy=1.0):
        """
        Represents a sensor node in the WSN.

        :param node_id: Unique identifier for the node
        :param x: x-coordinate of the node
        :param y: y-coordinate of the node
        :param energy: Initial energy level
        """
        self.node_id = node_id
        self.x = x
        self.y = y
        self.energy = energy
        self.is_alive = True
        self.is_cluster_head = False
        self.cluster_id = None  # ID of the cluster this node belongs to
        self.radius = 5  # For drawing on canvas
        self.color = "green"  # Updated based on energy

    def distance_to(self, other):
        """Compute Euclidean distance to another node or (x,y) tuple."""
        if isinstance(other, Node):
            return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        elif isinstance(other, tuple):
            return math.sqrt((self.x - other[0]) ** 2 + (self.y - other[1]) ** 2)

    def update_energy(self, energy_consumed):
        """Reduce node's energy by a certain amount."""
        if self.is_alive:
            self.energy -= energy_consumed
            if self.energy <= 0:
                self.energy = 0
                self.is_alive = False

    def update_color_by_energy(self):
        """Change the node's color based on remaining energy."""
        if not self.is_alive:
            self.color = "gray"
        else:
            if self.energy > 0.6:
                self.color = "green"
            elif self.energy > 0.3:
                self.color = "yellow"
            else:
                self.color = "red"


# =========================================
# =           WSN Simulation             =
# =========================================

class WSNSimulation:
    def __init__(self, width=600, height=400, num_nodes=20,
                 cluster_head_prob=0.2, base_station=(300, 20)):
        """
        Manages the WSN simulation.

        :param width: Width of the simulation area
        :param height: Height of the simulation area
        :param num_nodes: Number of sensor nodes
        :param cluster_head_prob: Probability of a node becoming a cluster head (LEACH-like)
        :param base_station: Coordinates of the base station
        """
        self.width = width
        self.height = height
        self.num_nodes = num_nodes
        self.cluster_head_prob = cluster_head_prob
        self.base_station = base_station

        self.nodes = []
        self.round_count = 0
        self.is_running = False

        # For quick reference to cluster heads each round
        self.cluster_heads = []

        # Basic energy consumption parameters
        self.energy_tx = 0.01  # Energy per transmission
        self.energy_rx = 0.005  # Energy per reception
        self.energy_aggr = 0.002  # Energy for data aggregation at cluster head

        # Stop condition: fraction of dead nodes (e.g. 80% => 0.8)
        self.death_threshold = 0.8

    def deploy_nodes_randomly(self):
        """Randomly deploy nodes in the simulation area."""
        self.nodes = []
        for i in range(self.num_nodes):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            node = Node(node_id=i, x=x, y=y, energy=1.0)
            self.nodes.append(node)

    def select_cluster_heads(self):
        """
        Select cluster heads based on a simple probability approach (like LEACH).
        """
        self.cluster_heads = []
        for node in self.nodes:
            node.is_cluster_head = False
            node.cluster_id = None

            if node.is_alive:
                # Probability-based CH election
                if random.random() < self.cluster_head_prob:
                    node.is_cluster_head = True
                    self.cluster_heads.append(node.node_id)

    def assign_clusters(self):
        """
        Assign each non-CH node to the nearest cluster head.
        """
        for node in self.nodes:
            if not node.is_cluster_head and node.is_alive:
                min_dist = float('inf')
                best_ch_id = None
                for ch_id in self.cluster_heads:
                    ch_node = self.nodes[ch_id]
                    dist = node.distance_to(ch_node)
                    if dist < min_dist:
                        min_dist = dist
                        best_ch_id = ch_id
                node.cluster_id = best_ch_id

    def transmit_data(self):
        """
        Simulate data transmission and energy consumption.
        1) Each non-CH node sends to its cluster head
        2) Cluster heads aggregate and send data to base station
        """
        # Node -> CH
        for node in self.nodes:
            if node.is_alive and not node.is_cluster_head and node.cluster_id is not None:
                ch_node = self.nodes[node.cluster_id]
                node.update_energy(self.energy_tx)  # Transmission
                ch_node.update_energy(self.energy_rx)  # Reception

        # CH -> Base Station
        for ch_id in self.cluster_heads:
            ch_node = self.nodes[ch_id]
            if ch_node.is_alive:
                # Aggregation cost
                ch_node.update_energy(self.energy_aggr)
                # Transmission to base station (simplified)
                ch_node.update_energy(self.energy_tx)

    def update_node_states(self):
        """Update each node's color or status based on remaining energy."""
        for node in self.nodes:
            node.update_color_by_energy()

    def count_alive_nodes(self):
        """Return the number of alive nodes."""
        return sum(1 for node in self.nodes if node.is_alive)

    def run_round(self):
        """
        Perform one round of the simulation:
        1) Select cluster heads
        2) Assign clusters
        3) Transmit data
        4) Update states
        5) Check if we should stop
        """
        self.round_count += 1

        self.select_cluster_heads()
        self.assign_clusters()
        self.transmit_data()
        self.update_node_states()

    def reset_simulation(self):
        """Reset simulation state and redeploy nodes."""
        self.round_count = 0
        self.deploy_nodes_randomly()
        self.update_node_states()

    def should_stop(self):
        """
        Check the stopping condition.
        If fraction_dead >= self.death_threshold => we stop.
        """
        total_nodes = self.num_nodes
        alive_nodes = self.count_alive_nodes()
        fraction_dead = (total_nodes - alive_nodes) / total_nodes
        return (fraction_dead >= self.death_threshold)


# =========================================
# =           Tkinter GUI                =
# =========================================

class WSNGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("WSN Energy-Efficient Routing")
        self.geometry("900x600")

        # Simulation area
        self.sim_width = 600
        self.sim_height = 400

        # Create simulation object
        self.sim = WSNSimulation(width=self.sim_width,
                                 height=self.sim_height,
                                 num_nodes=20,
                                 cluster_head_prob=0.2,
                                 base_station=(300, 20))

        # Create GUI elements
        self.create_widgets()

        # Deploy initial nodes
        self.sim.deploy_nodes_randomly()
        self.update_canvas()

        # Refresh rate in milliseconds (1 second = 1000 ms)
        self.refresh_rate = 1000
        self.after_id = None

    def create_widgets(self):
        """Create the main GUI components: controls, canvas, status labels."""
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Number of Nodes
        tk.Label(control_frame, text="Num Nodes:").pack(side=tk.LEFT)
        self.node_count_var = tk.IntVar(value=20)
        node_count_spin = tk.Spinbox(control_frame, from_=5, to=200, textvariable=self.node_count_var, width=5)
        node_count_spin.pack(side=tk.LEFT, padx=5)

        # Cluster Head Probability
        tk.Label(control_frame, text="CH Prob:").pack(side=tk.LEFT)
        self.ch_prob_var = tk.DoubleVar(value=0.2)
        ch_prob_scale = tk.Scale(control_frame, from_=0.0, to=1.0, resolution=0.01,
                                 orient=tk.HORIZONTAL, variable=self.ch_prob_var)
        ch_prob_scale.pack(side=tk.LEFT, padx=5)

        # Death Threshold (stop condition)
        tk.Label(control_frame, text="Stop if Fraction Dead >= ").pack(side=tk.LEFT)
        self.death_threshold_var = tk.DoubleVar(value=0.8)
        tk.Spinbox(control_frame, from_=0.1, to=1.0, increment=0.1,
                   textvariable=self.death_threshold_var, width=5).pack(side=tk.LEFT, padx=5)

        # Buttons
        start_button = tk.Button(control_frame, text="Start", command=self.start_simulation)
        start_button.pack(side=tk.LEFT, padx=5)

        stop_button = tk.Button(control_frame, text="Stop", command=self.stop_simulation)
        stop_button.pack(side=tk.LEFT, padx=5)

        reset_button = tk.Button(control_frame, text="Reset", command=self.reset_simulation)
        reset_button.pack(side=tk.LEFT, padx=5)

        # Canvas for visualization
        self.canvas = tk.Canvas(self, width=self.sim_width, height=self.sim_height, bg="white")
        self.canvas.pack(side=tk.TOP, pady=10)

        # Bottom frame for status labels
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Round count
        tk.Label(bottom_frame, text="Round:").pack(side=tk.LEFT)
        self.round_var = tk.StringVar(value="0")
        tk.Label(bottom_frame, textvariable=self.round_var, width=5).pack(side=tk.LEFT)

        # Alive nodes count
        tk.Label(bottom_frame, text="Alive Nodes:").pack(side=tk.LEFT)
        self.alive_var = tk.StringVar(value="0")
        tk.Label(bottom_frame, textvariable=self.alive_var, width=5).pack(side=tk.LEFT)

    def start_simulation(self):
        """Begin the simulation loop."""
        if not self.sim.is_running:
            self.sync_params()
            self.sim.is_running = True
            # Run first round and schedule next
            self.run_one_round()

    def stop_simulation(self):
        """Stop the simulation loop."""
        self.sim.is_running = False
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None

    def reset_simulation(self):
        """Reset the simulation and GUI to start fresh."""
        self.stop_simulation()
        self.sync_params()
        self.sim.reset_simulation()
        self.update_canvas()
        self.update_status()

    def sync_params(self):
        """Apply GUI parameters to the simulation object."""
        self.sim.num_nodes = self.node_count_var.get()
        self.sim.cluster_head_prob = self.ch_prob_var.get()
        self.sim.death_threshold = self.death_threshold_var.get()

    def run_one_round(self):
        """Perform a single simulation round, update GUI, and schedule the next round."""
        if not self.sim.is_running:
            return

        self.sim.run_round()
        self.update_canvas()
        self.update_status()

        # Check stopping condition
        if self.sim.should_stop():
            self.conclude_simulation()
        else:
            # Schedule next round
            self.after_id = self.after(self.refresh_rate, self.run_one_round)

    def conclude_simulation(self):
        """
        Stop the simulation and display a message indicating the final round.
        """
        self.stop_simulation()
        final_round = self.sim.round_count
        # Use messagebox.showinfo (or showwarning, showerror, etc.) for a pop-up dialog
        messagebox.showinfo(
            "Simulation Concluded",
            f"Simulation ended at round {final_round}. "
            f"Network reached the death threshold."
        )

    def update_canvas(self):
        """Redraw nodes and base station."""
        self.canvas.delete("all")

        # Draw base station
        bs_x, bs_y = self.sim.base_station
        bs_size = 8
        self.canvas.create_rectangle(bs_x - bs_size, bs_y - bs_size,
                                     bs_x + bs_size, bs_y + bs_size,
                                     fill="blue", outline="black")
        self.canvas.create_text(bs_x, bs_y - 15, text="BS", fill="blue")

        # Draw each node
        for node in self.sim.nodes:
            x, y = node.x, node.y
            r = node.radius
            color = node.color
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="black")

            # Highlight cluster heads
            if node.is_cluster_head and node.is_alive:
                self.canvas.create_oval(x - r * 2, y - r * 2, x + r * 2, y + r * 2, outline="orange", width=2)

            # Draw line from node -> cluster head if alive
            if node.cluster_id is not None and not node.is_cluster_head and node.is_alive:
                ch_node = self.sim.nodes[node.cluster_id]
                if ch_node.is_alive:
                    self.canvas.create_line(node.x, node.y, ch_node.x, ch_node.y, fill="gray", dash=(2, 4))

    def update_status(self):
        """Update round count and alive node count."""
        self.round_var.set(str(self.sim.round_count))
        self.alive_var.set(str(self.sim.count_alive_nodes()))


if __name__ == "__main__":
    app = WSNGUI()
    app.mainloop()
