# Movie Recommendation Model

Movie recommendation model project made as part of the Accelerated Introduction to Machine Learning offered by Mcgill's Artificial Intelligence Society.

## Project Overview

A `Flask` webapp with that leverages a trained collaborative-filtering model implemented using `scikit-suprise` package with the using of the [MovieLens 100K](https://grouplens.org/datasets/movielens/) dataset in order to make movie recommendations. (Still in development!)

## Loading the Model

1. First upload the model saved under `/code/knn_model.pkl` to your Colab Notebook

2. Unpickle the model using the `pickle` package:

   ```python
   import pickle

   with open('knn_model.pkl', 'rb') as file:
       model = pickle.load(file)

   # Now you can use the model to make predictions
   ```

   > Note that the `pickle` package is already included with Python

### Acknowledgments

Thank you for the instructors and TPM's of McGill's Artificial Intelligence Society for offering this opportunity and for the support.
