import tensorflow as tf
import numpy as np
from itertools import izip_longest
import h5py, thredds

graph = tf.Graph()
sess = tf.Session(graph=graph)

epochs = 10

f = h5py.File('cdip.hdf5')
master = thredds.HDF5Buoy(f, '100') # Torrey Pines
neighbor_buoys = ['106']
supplemental = [thredds.HDF5Buoy(f, k)
                for k in neighbor_buoys]

output_size = np.prod(f[master.station]['energy'].shape[1:])
input_size = output_size*len(neighbor_buoys)
state_size = input_size*10
batch_size = 1
slice_size = 10

with graph.as_default():
    cell_layer = tf.contrib.rnn.BasicLSTMCell(state_size, state_is_tuple=True)
    cell = tf.contrib.rnn.MultiRNNCell([cell_layer]*1)
    x  = tf.placeholder(tf.float32, shape=(batch_size, slice_size, input_size))
    y_ = tf.placeholder(tf.float32, shape=(batch_size, slice_size, output_size))
    outputs, states = tf.nn.dynamic_rnn(cell, x, dtype=tf.float32)

    W = tf.Variable(tf.random_uniform((state_size, output_size), -1.0, 1.0))
    b = tf.Variable(tf.random_uniform((1, 1, output_size), -1.0, 1.0))
    y = tf.tensordot(outputs, W, [[2], [0]]) + b

    loss = tf.reduce_mean(tf.square(y - y_))
    train = tf.train.AdamOptimizer().minimize(loss)
    
    sess.run(tf.global_variables_initializer())
    data = thredds.align_buoys(master, supplemental)
    print "Starting Training"
    for Q in izip_longest(*([iter(data)]*batch_size*slice_size)):
        X, Y_ = zip(*Q)
        r = sess.run([loss, train, y, y_], 
                     feed_dict={x:X.reshape((batch_size,
                                             slice_size,
                                             input_size)),
                                y_:Y_.reshape((batch_size, 
                                               slice_size,
                                               input_size))})
        print 'Loss: ', r[0]

