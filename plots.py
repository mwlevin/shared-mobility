import matplotlib.pyplot as plt

# Sample data
names = ['base scenario', 'scenario 1', 'scenario 2']  # replace with your names
x_values = ['base scenario', 'scenario 1', 'scenario 2']  # replace with your x values
y_values = [24039935.6, 22393005.14, 23907739.88]  # replace with your y values

# Create bar chart
plt.figure(figsize=(10, 6))
bar_width = 0.35

# Bar positions
index = range(len(names))
bar1 = plt.bar(index, x_values, bar_width, label='X Values')
bar2 = plt.bar([i + bar_width for i in index], y_values, bar_width, label='Y Values')

# Adding labels and title
plt.xlabel('Names')
plt.ylabel('TSTT (min)')
#plt.title('Bar Chart of X and Y Values')
plt.xticks([i + bar_width / 2 for i in index], names)
plt.legend()

# Show plot
plt.show()
