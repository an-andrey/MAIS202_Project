from surprise import Dataset, accuracy, Reader
import pickle
import os
from sklearn.model_selection import train_test_split
import pandas as pd

# SCRIPT IN ORDER TO TEST THE MODEL'S ACCURACY 
# MODEL NEEDS TO BE SAVED AS knn_model.pkl

test_data = pd.read_csv("MovieLensFinal/ratings_test.csv")

model_path = 'code/flask webapp/models/svd_model.pkl'
test_ratings = test_data.sample(frac=0.1, random_state=42)

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
