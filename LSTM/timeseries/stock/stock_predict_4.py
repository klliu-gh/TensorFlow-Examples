# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 20:56:46 2018

@author: lankuohsing
"""

# In[]
import numpy as np
import tensorflow as tf
from tensorflow.contrib import rnn
import pandas as pd
import matplotlib as mpl
from tensorflow.contrib.learn.python.learn.estimators.estimator import SKCompat
from sklearn.preprocessing import MinMaxScaler
mpl.use('Agg')
from matplotlib import pyplot as plt
# In[]
import shutil
import os

model_path="Models/model_4"
if not os.path.exists(model_path):  ###判断文件是否存在，返回布尔值
   os.makedirs(model_path)
shutil.rmtree(model_path)
# In[]
#读取数据
f=open('dataset_2.csv')
df=pd.read_csv(f)     #读入股票数据
data=df.iloc[:,2:10].values  #取第3-10列
feature_range=(0,1)#归一化的范围
#data=data[::-1]
# In[]
#数据归一化
scaler = MinMaxScaler(copy=True)
scaled_data=scaler.fit_transform(data)

# In[]
learn = tf.contrib.learn
HIDDEN_SIZE = 10  # Lstm中隐藏节点的个数
NUM_LAYERS = 1  # LSTM的层数
TIMESTEPS = 10  # 循环神经网络的截断长度
TRAINING_STEPS = 10000  # 训练轮数
BATCH_SIZE = 32  # batch大小
input_size=7

# In[]
# 根据输入序列，切割出输入数据和标签。利用前面的TIMESTEPS项预测后面的一项
def generate_train_data(seq):
    X = []
    Y = []
    # 序列的第i项和后面的TIMESTEPS-1项合在一起作为输入;第i+TIMESTEPS项作为输出
    # 即用sin函数前面的TIMESTPES个点的信息，预测第i+TIMESTEPS个点的函数值
    for i in range(seq.shape[0]- TIMESTEPS):
        X.append(seq[i:i+TIMESTEPS,0:7].T)
        Y.append([seq[i+TIMESTEPS,7]])
    #X.shape:[seq.shape[0]- TIMESTEPS,7,TIMESTEPS]
    #Y.shape:[seq.shape[0]- TIMESTEPS,1,TIMESTEPS]
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)
def generate_test_data(seq):
    X = []
    Y = []
    # 序列的第i项和后面的TIMESTEPS-1项合在一起作为输入;第i+TIMESTEPS项作为输出
    # 即用sin函数前面的TIMESTPES个点的信息，预测第i+TIMESTEPS个点的函数值
    for i in range(seq.shape[0]- TIMESTEPS):
        X.append(seq[i:i+TIMESTEPS,0:7].T)
        Y.append([seq[i+TIMESTEPS,7]])
    #X.shape:[seq.shape[0]- TIMESTEPS,7,TIMESTEPS]
    #Y.shape:[seq.shape[0]- TIMESTEPS,1,TIMESTEPS]
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)
def LstmCell():
    lstm_cell = rnn.BasicLSTMCell(num_units=HIDDEN_SIZE,forget_bias=1.0,state_is_tuple=True)
    return lstm_cell

# 定义lstm模型
def lstm_model(X, y):
    cell = rnn.MultiRNNCell([LstmCell() for _ in range(NUM_LAYERS)])
    """
    print("X.shape:",X.shape)
    batch_size=tf.shape(X)[0]
    time_step=tf.shape(X)[1]
    print("time_step:",time_step)
    w_in=weights['in']
    b_in=biases['in']
    input=tf.reshape(X,[-1,input_size])  #需要将tensor转成2维进行计算，计算后的结果作为隐藏层的输入
    print("input.shape:",input.shape)
    print("w_in.shape:",w_in.shape)
    input_rnn=tf.matmul(input,w_in)+b_in
    input_rnn=tf.reshape(input_rnn,[-1,time_step,HIDDEN_SIZE])  #将tensor转成3维，作为lstm cell的输入
    cell=tf.nn.rnn_cell.BasicLSTMCell(HIDDEN_SIZE)
    init_state=cell.zero_state(batch_size,dtype=tf.float32)
    print(input_rnn.shape)
    """
    #X=tf.reshape(X,[-1,TIMESTEPS*input_size])
    #X=tf.split(X,TIMESTEPS,1)
    print(X[0].shape)
    outputs, _ = tf.nn.dynamic_rnn(cell, X, dtype=tf.float32)
    print("outputs.shape:",outputs.shape)
    output = tf.reshape(outputs[:,TIMESTEPS-1,:], [-1, HIDDEN_SIZE])

    # 通过无激活函数的全连接层计算线性回归，并将数据压缩成一维数组结构
    #注意，这里不用在最后加一层softmax层，因为不是分类问题
    predictions = tf.contrib.layers.fully_connected(output, 1, None)


    # 将predictions和labels调整统一的shape
    labels = tf.reshape(y, [-1])
    print(labels.shape)
    predictions = tf.reshape(predictions, [-1])
    print(predictions.shape)
    loss = tf.losses.mean_squared_error(predictions, labels)
    print(loss.shape)
    train_op = tf.contrib.layers.optimize_loss(loss, tf.contrib.framework.get_global_step(),
                                             optimizer="Adagrad",
                                             learning_rate=0.1)
    return predictions, loss, train_op

# In[]
X_train,Y_train=generate_train_data(scaled_data)
X_test,Y_test=generate_train_data(scaled_data)
#X=np.transpose(X,[0,2,1])

    # In[]
# 进行训练
# 封装之前定义的lstm
regressor = SKCompat(learn.Estimator(model_fn=lstm_model, model_dir=model_path))
# 生成数据
train_X, train_y = generate_train_data(scaled_data[0:5000,:])
train_X=np.transpose(train_X,[0,2,1])
#train_y=np.transpose(train_y,[0,2,1])
test_X, test_y = generate_test_data(scaled_data[5000:6000,:])
test_X=np.transpose(test_X,[0,2,1])
#test_y=np.transpose(test_y,[0,2,1])
# 拟合数据
# In[]
regressor.fit(train_X, train_y, batch_size=BATCH_SIZE, steps=TRAINING_STEPS)
# 计算预测值
# In[]
predicted = [[pred] for pred in regressor.predict(test_X)]
predicted=np.array(predicted)
test_y=np.reshape(test_y,predicted.shape)
# 计算MSE
rmse = np.sqrt(((predicted - test_y) ** 2).mean(axis=0))
print("Mean Square Error is:%f" % rmse[0])
# In[]
predicted=(predicted-feature_range[0])/(feature_range[1]-feature_range[0])\
*(scaler.data_max_[7]-scaler.data_min_[7])+scaler.data_min_[7]
test_y=(test_y-feature_range[0])/(feature_range[1]-feature_range[0])\
*(scaler.data_max_[7]-scaler.data_min_[7])+scaler.data_min_[7]
# In[]
acc=np.average(np.abs(predicted-test_y)/test_y)  #偏差程度
print("The accuracy of this predict:",acc)
# In[]
plot_test, = plt.plot(test_y, label='real_sin')
plot_predicted, = plt.plot(predicted, label='predicted')
plt.legend([plot_predicted, plot_test],['predicted', 'real_sin'])
x_start=0
x_end=100
y_start=2000
y_end=3000
plt.axis([x_start,x_end,y_start,y_end])
plt.show()