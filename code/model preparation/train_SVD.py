from surprise import SVD, Dataset, Reader
from surprise.model_selection import KFold
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# Load the full dataset and split it for testing
ratings = pd.read_csv("train.csv")

# split_index = int(len(ratings) * 0.5)
# train_ratings = ratings.iloc[:split_index]  # First 50% for training
# test_ratings = ratings.iloc[split_index:]   # Last 50% for testing
train_ratings, test_ratings = train_test_split(ratings, test_size=0.5, random_state=22)

train_ratings.to_csv("train2.csv")
test_ratings.to_csv("test2.csv")

# Prepare the dataset for Surprise
reader = Reader(rating_scale=(1, 5))
train_data = Dataset.load_from_df(train_ratings[['userId', 'movieId', 'rating']], reader)

# Initialize SVD algorithm with default or custom parameters
algo = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02)

# Set up cross-validation with progress indication
kf = KFold(n_splits=5)
print("Cross-validation in progress:")
for i, (trainset, testset) in enumerate(tqdm(kf.split(train_data), total=5, desc="Folds")):
    algo.fit(trainset)
    predictions = algo.test(testset)
    # Here you could add evaluation metrics if desired (e.g., RMSE or MAE)

# Build the full training set and train the model
trainset = train_data.build_full_trainset()
algo.fit(trainset)

# Save the trained model with joblib
joblib.dump(algo, 'svd_model.joblib')

# Optional: verify the model save
try:
    test_load = joblib.load('svd_model.joblib')
    print("Model saved and verified successfully")
except Exception as e:
    print(f"Error verifying model save: {str(e)}")
