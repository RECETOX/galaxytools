#!/bin/bash
# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 input.csv"
    exit 1
fi
    
input_file="$1"
header=$(head -n 1 "$input_file")
num_columns=$(echo "$header" | awk -F, '{print NF}')
    
# Create a directory to store the output files
output_dir="split_columns"
mkdir -p "$output_dir"
    
# Split the CSV file into one file per column
for ((i=1; i<= num_columns; i++)); do
    column_name=$(echo "$header" | cut -d, -f$i)
    output_file="$output_dir/${column_name}.txt"
    tail -n +2 "$input_file" | cut -d, -f$i > "$output_file"
done
    
echo "Columns have been split into separate files in the '$output_dir' directory."