import sys
import os
#sys.path.insert(0, '../')
import unittest
import errno
import numpy as np
import random
import GPy
from robo.models.GPyModel import GPyModel
from robo.acquisition.EI import EI

here = os.path.abspath(os.path.dirname(__file__))


class EITestCase1(unittest.TestCase):

    def setUp(self):
        self.x = np.array([[ 0.62971589], [ 0.63273273], [ 0.17867868], [ 0.17447447], [ 1.88558559]]);
        self.y = np.array([[-3.69925653], [-3.66221988], [-3.65560591], [-3.58907791], [-8.06925984]]);
        self.kernel = GPy.kern.RBF(input_dim=1, variance= 30.1646253727, lengthscale = 0.435343653946)    
        self.noise = 1e-10
        self.model = GPyModel(self.kernel, noise_variance=self.noise, optimize=False)
        self.model.train(self.x, self.y)
        self.bigger_noise = 1e2
        self.noise_model = GPyModel(self.kernel, noise_variance=self.bigger_noise, optimize=False)
        self.noise_model.train(self.x, self.y)

    def test(self):
        X_upper = np.array([ 2.1])
        X_lower = np.array([-2.1])
        ei_par_0 = EI(self.model, X_upper=X_upper, X_lower=X_lower,  par=0.0, derivative=True)
        ei_par_1 = EI(self.model, X_upper=X_upper, X_lower=X_lower,  par=1.0, derivative=True)
        ei_par_2 = EI(self.model, X_upper=X_upper, X_lower=X_lower,  par=2.0, derivative=True)
        x_values = [0.62971589] + [2.1 * random.random() - 2.1 for i in range(10)]
        out0 = np.array([ ei_par_0(np.array([[x]]), derivative=True) for x in x_values])
        value0 = out0[:,0]
        derivative0 = out0[:,1]
        
        out1 = np.array([ ei_par_1(np.array([[x]]), derivative=True) for x in x_values])
        value1 = out1[:,0]
        derivative1 = out1[:,1]
        
        out2 = np.array([ ei_par_2(np.array([[x]]), derivative=True) for x in x_values])
        value2 = out2[:,0]
        derivative2 = out2[:,1]
        assert(value0[0] <= 1e-5)
        assert(np.all(value0 >= value1))
        assert(np.all(value1 >= value2))
        assert(np.all(np.abs(derivative0) >= np.abs(derivative1)))
        assert(np.all(np.abs(derivative1) >= np.abs(derivative2)))
        ei_par_0.update(self.noise_model)
        out0_noise = np.array([ ei_par_0(np.array([[x]]), derivative=True) for x in x_values])
        value0_noise = out0[:,0]
        derivative0_noise = out0[:,1]
        assert(np.all(np.abs(value0_noise) >= np.abs(value0)))
        


if __name__=="__main__":
    unittest.main()
