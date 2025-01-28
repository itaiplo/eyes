import matplotlib.pyplot as plt

# Data for the first graph
x = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]
y1 = [88, 98, 97, 89, 89, 94, 98, 92, 97, 97, 97, 88, 91, 97, 87, 95]
y2 = [95, 98, 92, 99, 91, 99, 93, 94, 90, 92, 89, 92, 99, 98, 94, 97]

# Create the plot
plt.figure(figsize=(10, 6))

# Plot the first graph
plt.plot(x, y1, marker='o', label='Open eyes', linestyle='-', linewidth=2)
# Plot the second graph
plt.plot(x, y2, marker='o', label='Closed eyes', linestyle='-', linewidth=2)

# Add titles and labels
plt.title('Accuracy rate as a function of light quantity', fontsize=16)
plt.xlabel('Light [Lux]', fontsize=12)
plt.ylabel('Hit rate [%]', fontsize=12)

# Add a legend
plt.legend(fontsize=12)

# Show the grid
plt.grid(True, linestyle='--', alpha=0.7)

# Display the plot
plt.show()
