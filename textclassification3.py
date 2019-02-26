# TEXT CLASSIFICATION

import os, shutil
import numpy as np
import matplotlib.pyplot as plt
import csv
from groupTextMeanings import groupTextMeanings

import pandas as pd
import keras
from keras import preprocessing
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras import layers
from keras import Sequential
import pickle

def unison_shuffled_copies(a, b):
    assert len(a) == len(b)
    p = np.random.permutation(len(a))
    return a[p], b[p]

# Reading csv file, delimiter = ','

# DATAFRAME OF TRAINING SAMPLES
data_df = pd.read_csv('data/train.csv', delimiter = ',')
print(data_df.head())
print('------------------------------------------------')

# extract the description of the image, this is the texts sequence that will be used to train the model
texts = data_df['title']

# extract the category of the image, this is the target values to be predicted from the training set
targets = data_df['Category']

nb_categories = 58

training_samples = len(texts)
#Number of training samples found to be 666615
print('Number of training samples', training_samples)

print('Shape of data tensor', texts.shape)

# encode targets into vectors
targets = keras.utils.to_categorical(targets, nb_categories)
print('Shape of target tensor', targets.shape)

texts, targets = unison_shuffled_copies(texts, targets)

# MODEL LAYERS FOR DENSE MODEL
# defining the structure of the model
model = Sequential()
model.add(layers.LSTM(80, return_sequences=True, input_shape=(None, nb_categories)))
model.add(layers.LSTM(80))
#model.add(layers.Dropout(0.5))
model.add(layers.Dense(150, activation='relu'))
#model.add(layers.Dropout(0.5))
model.add(layers.Dense(nb_categories, activation='softmax'))

model.summary()

# compiling the model
model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = ['accuracy'])

if os.path.isfile("data/xtrain.pkl"):
    f = open("data/xtrain.pkl", "rb")
    ntexts = pickle.load(f)
    f.close()
else:
	encoder = groupTextMeanings()
	ntexts = []
	for i, t in enumerate(texts):
		words = t.split(" ")
		text_matrix = np.zeros((len(words), nb_categories))
		for j, w in enumerate(words):
			text_matrix[j] = np.reshape(np.asarray(encoder.valueOf(w)), (1, nb_categories))
		ntexts.append(text_matrix)
		print("Encoding: ", i+1, "/", training_samples, "\r", end='')
	f = open("data/xtrain.pkl", "wb")
	pickle.dump(ntexts, f)

x_train = ntexts[:600000]
y_train = targets[:600000]

x_val = ntexts[600000:]
y_val = targets[600000:]

def generator(x_train, y_train):
	i = -1
	while True:
		i += 1
		xshape = x_train[i].shape
		yield np.reshape(x_train[i], (1, xshape[0], nb_categories)), np.reshape(y_train[i], (1, nb_categories))

def val_generator(x_val, y_val):
	i = -1
	while True:
		i += 1
		xshape = x_val[i].shape
		yield np.reshape(x_val[i], (1, xshape[0], nb_categories)), np.reshape(y_val[i], (1, nb_categories))

nb_epochs = 10

# train the model
history = model.fit_generator(generator(x_train, y_train), epochs = nb_epochs, steps_per_epoch = 599999, verbose=1, validation_data=val_generator(x_val, y_val), validation_steps=66614)

print("Done training")
# DATAFRAM OF TEST DATA
test_df = pd.read_csv('data/test.csv')

print("Reading test data")

texts = test_df['title']
ids = test_df['itemid']

for i, t in enumerate(texts):
	words = t.split(" ")
	text_matrix = np.zeros((len(words), nb_categories))
	for j, w in enumerate(words):
		text_matrix[j] = np.reshape(np.asarray(encoder.valueOf(w)), (1, nb_categories))
	texts[i] = text_matrix

print("Predicting")
predictions = model.predict(texts)

print("Outputting")
i = 0
catNumber = np.zeros(predictions.shape[0])
for p in predictions:
	catNumber[i] = np.argmax(p)
	i += 1
output = np.hstack((ids.to_numpy().reshape((-1, 1)), catNumber.astype(int).reshape(-1, 1)))
np.savetxt("data/submission.csv", output, fmt="%i", delimiter=",", header="itemid,Category", comments="")

print("Done")

train_acc = history.history['acc']
train_loss = history.history['loss']

val_acc = history.history['val_acc']
val_loss = history.history['val_loss']

epoch_index = range(1, nb_epochs + 1)

plt.plot(epoch_index, train_acc, 'bo', label = 'Training Accuracy')
plt.plot(epoch_index, val_acc, 'b', label = 'Validation Accuracy')
plt.title('Training and Validation Accuracy')
plt.legend()

plt.figure()

plt.plot(epoch_index, train_loss, 'bo', label = 'Training Loss')
plt.plot(epoch_index, val_loss, 'b', label = 'Validation Loss')
plt.title('Training and Validation Loss')
plt.legend()

plt.show()