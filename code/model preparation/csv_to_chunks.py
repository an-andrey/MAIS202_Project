import pandas as pd
import os

#converting the large ratings.csv file into multiple chunks
batch_size = 100000

def split_csv(csv_file, batch_size):
    # Create a directory for the batch files
    output_dir = "MovieLensFinal/csv_batches"
    os.makedirs(output_dir, exist_ok=True)

    # Read the CSV in chunks
    chunk_iter = pd.read_csv(csv_file, chunksize=batch_size)
    
    batch_count = 0
    for chunk in chunk_iter:
        batch_count += 1
        # Save each chunk as a new CSV file
        chunk.to_csv(f"{output_dir}/batch_{batch_count}.csv", index=False)

split_csv("MovieLensFinal/ratings.csv", batch_size)