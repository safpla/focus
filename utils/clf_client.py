import os
import sys
root_path = '/'.join(os.path.realpath(__file__).split('/')[:-2])
sys.path.insert(0, root_path)

import numpy as np
import tensorflow as tf

from grpc.beta import implementations
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2


def classify(sents, model_name, signature_name, hostport='192.168.31.188:7000'):
        hostport = hostport
        # grpc
        host, port = hostport.split(':')
        channel = implementations.insecure_channel(host, int(port))
        stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)
        # build request
        request = predict_pb2.PredictRequest()
        request.model_spec.name = model_name # ?
        request.model_spec.signature_name = signature_name # 是之前的mission
        request.inputs['input_plh'].CopyFrom(
            tf.contrib.util.make_tensor_proto(sents, dtype=tf.int32))
        request.inputs['dropout_keep_prob_mlp'].CopyFrom(
            tf.contrib.util.make_tensor_proto(1.0, dtype=tf.float32)) # 为什么是1？
        model_result = stub.Predict(request, 60.0)
        model_result = np.array(model_result.outputs['scores'].float_val)
        model_result = model_result.tolist()
        return model_result
