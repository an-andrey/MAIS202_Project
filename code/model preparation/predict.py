from surprise import Dataset, accuracy, Reader
import pickle
import os
from sklearn.model_selection import train_test_split
import pandas as pd

# SCRIPT IN ORDER TO TEST THE MODEL'S ACCURACY 
# MODEL NEEDS TO BE SAVED AS knn_model.pkl

ratings = pd.read_csv("MovieLens32M/ratings.csv")

model_path = 'knn_model.pkl'
train_ratings, test_ratings = train_test_split(ratings, test_size=0.95, random_state=42)
#only testing with 1.5 million data points
test_ratings = test_ratings[0:1500000]

# Check if the model file exists in the Colab environment
if os.path.exists(model_path):
    print("Loading model from local file.")
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
#if not, load the one in the github repo.
else:
    print("Model not found")


########################
# TESTING FROM SCRATCH #
########################

# # Predict the rating for a movie the new user hasn't seen
# error = 0
# count = 0
# for index,row in test_ratings.iterrows():
#   new_user_id = row['userId']
#   new_movie_id = row['movieId']
#   actual_rating = row['rating']
#   prediction = model.predict(new_user_id,new_movie_id)
#   error += round(abs(prediction.est - actual_rating)/5*100,2)
#   count += 1

# print(error/count)

##################
# USING SURPRISE #
##################

# Convert the test_ratings DataFrame to a Surprise dataset
reader = Reader(rating_scale=(1, 5))
test_data = Dataset.load_from_df(test_ratings[['userId', 'movieId', 'rating']], reader)

# Build the testset
testset = test_data.build_full_trainset().build_testset()

# Make predictions on the testing set
predictions = model.test(testset)

# Evaluate the model's performance
print(str(accuracy.rmse(predictions)).split()[1])
accuracy.mae(predictions)
