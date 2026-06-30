import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# 1. Initialize data arrays
x_data = []
y_data = []

# 2. Set up the figure and axis
fig, ax = plt.subplots()
line, = ax.plot([], [], 'r-', lw=2)  # Returns a Line2D object

# 3. Configure window limits and labels
ax.set_xlim(0, 100)
ax.set_ylim(-1.5, 1.5)
ax.set_title("Continuously Updating Sine Wave")
ax.grid(True)

# 4. Define the update function called at each frame
def update(frame):
    # Simulate receiving new continuous data
    x_data.append(frame)
    y_data.append(np.sin(frame * 0.1))
    
    # Keep lists concise (scroll window horizontally)
    if len(x_data) > 100:
        ax.set_xlim(x_data[-100], x_data[-1])
    
    # Directly update line data
    line.set_data(x_data, y_data)
    
    return line,

# 5. Build and run the animation
# frames provides a continuous generator (0, 1, 2...)
# interval controls the delay between updates in milliseconds
ani = FuncAnimation(fig, update, frames=np.linspace(0, 200, 1000), 
                    interval=20, blit=True)

plt.show()