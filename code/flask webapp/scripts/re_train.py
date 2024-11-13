import pandas as pd
from surprise import Dataset, Reader, SVD
import pickle
import os
import shutil
from datetime import datetime
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

def retrain_svd_model(ratings_df, model_path='code/flask webapp/models/svd_model.pkl', backup_dir='code/flask webapp/backups'):
    # Ensure the backup directory exists
    os.makedirs(backup_dir, exist_ok=True)
    
    # Load data into scikit-surprise
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings_df[['userId', 'movieId', 'rating']], reader)
    
    print("fitting started")
    start = time.time()
    # Train the SVD model
    trainset = data.build_full_trainset()
    model = SVD()
    model.fit(trainset)
    print(f"fitting ended in {time.time()-start} seconds")
    
    # Check if the current model exists
    if os.path.exists(model_path):
        # Create a timestamped backup filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(backup_dir, f'svd_model_{timestamp}.pkl')
        
        # Move the current model to the backup folder
        shutil.move(model_path, backup_path)
        print(f"Model backed up to {backup_path}")
        
    # Save the trained model using pickle
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {model_path}")

async def async_retrain_svd_model(ratings_df, model_path='code/flask webapp/models/svd_model.pkl', backup_dir='code/flask webapp/backups'):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, retrain_svd_model, ratings_df, model_path, backup_dir)