def compare_files(file1_path, file2_path):
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        for line_number, (line1, line2) in enumerate(zip(file1, file2), start=1):
            if line1 != line2:
                print(f"Files are different starting at line {line_number}.")
                return

        # Check if one file has more lines than the other
        if any(file1) or any(file2):
            print(f"Files are different lengths starting at line {line_number+1}.")
        else:
            print("Files are the same.")

# Example usage:
#compare_files('result174.txt','result175.txt')
