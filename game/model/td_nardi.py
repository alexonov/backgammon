from keras.layers import Dense
from keras.layers import Input
from keras.models import Sequential


INPUT_DIM = 24 * 3 + 2

model = Sequential(
    [
        Input(shape=(INPUT_DIM,)),
        Dense(units=40, activation='sigmoid'),
        Dense(units=20, activation='sigmoid'),
    ]
)
