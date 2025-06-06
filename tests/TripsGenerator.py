import random

# Function to generate asymmetric demand
def generate_asymmetric_demand(input_file, output_file, min_demand, max_demand):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        header = True
        origin_section = False
        
        for line in lines:
            if header:
                outfile.write(line)
                if line.strip() == "<END OF METADATA>":
                    header = False
                continue
            
            if line.startswith("Origin"):
                outfile.write(line)
                origin_section = True
                continue
            
            if origin_section:
                parts = line.strip().split()
                if len(parts) == 0:
                    origin_section = False
                    outfile.write("\n")
                    continue
                
                new_line = ""
                for i in range(0, len(parts), 3):
                    destination = parts[i]
                    demand = parts[i+2].rstrip(";")
                    if float(demand) != 0.0:
                        new_demand = random.randint(min_demand, max_demand)
                        new_line += f"    {destination} : {new_demand:.1f}; "
                    else:
                        new_line += f"    {destination} : {demand}; "
                    
                outfile.write(new_line + "\n")

# File paths
input_file = 'data/SiouxFalls/trips.txt'
output_file = 'data/SiouxFalls/asymmetric_trips.txt'

# Define the range for random demand
min_demand = 100
max_demand = 200

# Generate the asymmetric demand file
generate_asymmetric_demand(input_file, output_file, min_demand, max_demand)

print("Asymmetric demand file created successfully.")



