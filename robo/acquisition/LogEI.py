from scipy.stats import norm
import numpy as np
from robo import BayesianOptimizationError
from robo.acquisition.base import AcquisitionFunction


class LogEI(AcquisitionFunction):
    r"""

    :param model: A model that implements at least

                 - predict(X)
                 - getCurrentBestX().

    :param X_lower: Lower bounds for the search, its shape should be 1xD (D = dimension of search space)
    :type X_lower: np.ndarray (1,D)
    :param X_upper: Upper bounds for the search, its shape should be 1xD (D = dimension of search space)
    :type X_upper: np.ndarray (1,D)
    :param compute_incumbent: A python function that takes as input a model and returns a np.array as incumbent
    :param par: A parameter meant to control the balance between exploration and exploitation of the acquisition
                function. Empirical testing determines 0.01 to be a good value in most cases.

    """

    long_name = "Logarithm  of Expected Improvement"

    def __init__(self, model, X_lower, X_upper, compute_incumbent, par=0.01, **kwargs):
        self.model = model
        self.par = par
        self.X_lower = X_lower
        self.X_upper = X_upper
        self.compute_incumbent = compute_incumbent

    def __call__(self, X, derivative=False, **kwargs):

        """
        A call to the object returns the log(EI) and derivative values.

        :param X: The point at which the function is to be evaluated.
        :type X: np.ndarray (1,D)
        :param incumbent: The current incumbent
        :type incumbent: np.ndarray (1,D)
        :param derivative: This controls whether the derivative is to be returned.
        :type derivative: Boolean
        :return: The value of log(EI)
        :rtype: np.ndarray(1, 1)
        :raises BayesianOptimizationError: if X.shape[0] > 1. Only single X can be evaluated.
        """

        if derivative:
            raise BayesianOptimizationError(BayesianOptimizationError.NO_DERIVATIVE,
                                            "LogEI does not support derivative calculation until now")

        if len(X.shape) == 1:
            X = X[:, np.newaxis]

        if np.any(X < self.X_lower) or np.any(X > self.X_upper):
            return np.array([[- np.finfo(np.float).max]])
        m, v = self.model.predict(X)

        eta, _ = self.model.predict(np.array([self.compute_incumbent(self.model)]))

        f_min = eta - self.par

        s = np.sqrt(v)

        z = (f_min - m) / s

        log_ei = np.zeros((m.size, 1))
        for i in range(0, m.size):
            mu, sigma = m[i], s[i]

        #    par_s = self.par * sigma

            # Degenerate case 1: first term vanishes
            if np.any(abs(f_min - mu)) == 0:
                if sigma > 0:
                    log_ei[i] = np.log(sigma) + norm.logpdf(z[i])
                else:
                    log_ei[i] = -np.Infinity
            # Degenerate case 2: second term vanishes and first term has a special form.
            elif sigma == 0:
                if mu < np.any(f_min):
                    log_ei[i] = np.log(f_min - mu)
                else:
                    log_ei[i] = -np.Infinity
            # Normal case
            else:
                b = np.log(sigma) + norm.logpdf(z[i])
                # log(y+z) is tricky, we distinguish two cases:
                if np.any(f_min > mu):
                    # When y>0, z>0, we define a=ln(y), b=ln(z).
                    # Then y+z = exp[ max(a,b) + ln(1 + exp(-|b-a|)) ],
                    # and thus log(y+z) = max(a,b) + ln(1 + exp(-|b-a|))
                    a = np.log(f_min - mu) + norm.logcdf(z[i])

                    log_ei[i] = max(a, b) + np.log(1 + np.exp(-abs(b - a)))
                else:
                    # When y<0, z>0, we define a=ln(-y), b=ln(z), and it has to be true that b >= a in order to satisfy y+z>=0.
                    # Then y+z = exp[ b + ln(exp(b-a) -1) ],
                    # and thus log(y+z) = a + ln(exp(b-a) -1)
                    a = np.log(mu - f_min) + norm.logcdf(z[i])
                    if a >= b:
                        # a>b can only happen due to numerical inaccuracies or approximation errors
                        log_ei[i] = -np.Infinity
                    else:
                        log_ei[i] = b + np.log(1 - np.exp(a - b))

        return log_ei

    def plot(self, fig, minx, maxx, plot_attr={"color":"red"}, resolution=1000):

        ax = AcquisitionFunction.plot(self, fig, minx, maxx, plot_attr={"color":"red"}, resolution=1000)
        ax.set_ylim(-30, 0)
        return ax
