import tensorflow as tf
import numpy as np

def dehazeNet(data, input_maps):

    # read layer info
    layers = data['layers']
    layers = layers[0][0][0][0:-1]    # from the first to the last second layer
    current = input_maps
    network = {}
    data_dict = {}
    layer_num = 1
    for layer in layers:
        name = layer['name'][0][0][0]
        layer_type = layer['type'][0][0][0]
        if layer_type == 'conv':
            data_dict['conv' + str(layer_num)] = {}
            if name[:2] == 'fc':
                padding = 'VALID'
            else:
                padding = 'SAME'
            stride = layer['stride'][0][0][0]
            kernel, bias = layer['weights'][0][0][0]
            if len(kernel.shape) == 3:
                kernel = tf.expand_dims(tf.constant(kernel), 3)
            else:
                kernel = tf.constant(kernel)
            bias = np.squeeze(bias).reshape(-1)
            data_dict['conv' + str(layer_num)]['weight'] = kernel
            data_dict['conv' + str(layer_num)]['bias'] = bias
            data_dict['conv' + str(layer_num)]['stride'] = np.array([1, stride[0], stride[0], 1])
            conv = tf.nn.conv2d(current, kernel,
                                strides=(1, stride[0], stride[0], 1), padding=padding)
            current = tf.nn.bias_add(conv, bias)
            print name, 'stride:', stride, 'kernel size:', np.shape(kernel)
        elif layer_type == 'relu':
            current = tf.nn.relu(current)
            layer_num += 1
            print name + " " + layer_type
        elif layer_type == 'pool':
            stride = layer['stride'][0][0][0]
            pool = layer['pool'][0][0][0]
            current = tf.nn.max_pool(current, ksize=(1, pool[0], pool[1], 1),
                                     strides=(1, stride[0], stride[0], 1), padding='SAME')
            print name, 'stride:', stride
        elif layer_type == 'bnorm':
            epsilon = layer['epsilon'][0][0][0]
            scale, offset, _ = layer['weights'][0][0][0]
            scale = np.transpose(scale)[0]
            offset = np.transpose(offset)[0]
            axis = [0, 1, 2]
            mean, var = tf.nn.moments(current, axes=axis)
            print(mean.get_shape)
            print(var.get_shape)
            data_dict['conv' + str(layer_num)]['scale'] = scale
            data_dict['conv' + str(layer_num)]['offset'] = offset
            data_dict['conv' + str(layer_num)]['epsilon'] = epsilon
            scale = tf.constant(scale)
            offset = tf.constant(offset)
            current = tf.nn.batch_normalization(current, mean=mean, variance=var,
                                    offset=offset, scale=scale, variance_epsilon=epsilon)

            print name + " " + layer_type

        network[name] = current

    return network, data_dict