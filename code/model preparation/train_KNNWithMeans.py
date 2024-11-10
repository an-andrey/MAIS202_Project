from surprise import KNNWithMeans, Dataset, Reader
from surprise.model_selection import GridSearchCV, cross_validate
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

train_ratings, test_ratings = train_test_split(pd.read_csv("MovieLens32M/ratings.csv"),test_size=0.19,random_state=22)

test_ratings.to_csv("test_ratings_0.19.csv")
test_ratings.arra
reader = Reader(rating_scale=(1, 5))
train_data = Dataset.load_from_df(train_ratings[['userId', 'movieId', 'rating']], reader)
# Perform cross-validation on each chunk using the best parameters for RMSE
# If cell above was already ran:
# best_sim_options = gs.best_params['rmse']['sim_options']
# best_k = gs.best_params['rmse']['k']

#if by hand, use this:
best_sim_options = {'name': 'cosine', 'min_support': 1, 'user_based': False}
best_k = 80

algo = KNNWithMeans(sim_options=best_sim_options, k=best_k)
batch_size = 10000
# Perform batch processing for cross-validation
for i in range(0, len(train_ratings), batch_size):
    batch = train_ratings[i:i + batch_size]
    batch_data = Dataset.load_from_df(batch[['userId', 'movieId', 'rating']], reader)
    print(f"Cross-validation results for batch starting at index {i}:")
    cross_validate(algo, batch_data, measures=["rmse"], cv=5, verbose=True)

trainset = train_data.build_full_trainset()
algo.fit(trainset)

# Save the trained model with joblib
joblib.dump(algo, 'knn_model.joblib')

# Optional: verify the save worked
try:
    test_load = joblib.load('knn_model.joblib')
    print("Model saved and verified successfully")
except Exception as e:
    print(f"Error verifying model save: {str(e)}")