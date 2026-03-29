"""
surrogateModels
===============

This package contains an implementation of the hierarchical Kriging
multi-fidelity surrogate model by Han and Görtz (2012)
DOI: 10.2514/1.J051354
"""

import numpy as np
import scipy

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern


def normalize_points(pts: np.ndarray):
    """
    Scale the input space (list of points) to form a unit hypercube centered at origin

    :param pts: coordinates in the design space
    :type pts: np.ndarray, shape (n_sampling_points, n_design_variables)

    :return: scaled coordinates, scaling factors and biases
    :rtype: list[np.ndarray]
    """
    dv_min = np.min(pts, axis=0)
    dv_max = np.max(pts, axis=0)
    biases = (dv_min + dv_max) / 2
    scaling_factors = (dv_max - dv_min) / 2
    scaled_pts = (pts - biases) / scaling_factors
    return scaled_pts, scaling_factors, biases


class GaussianProcessRegression:
    """
    A wrapper around the Gaussian process regression models provided by scikit-learn.

    This class provides a wrapper around the Gaussian regression model generated with scikit-learn.
    The model's predictions can be accessed using GaussianProcessRegression.predict().

    :param lf_x: low fidelity sampling points
    :type lf_x: np.ndarray, shape (n_lf_samples, n_design_variables)
    :param lf_resp: low fidelity model responses corresponding to the sampling points
    :type lf_resp: np.ndarray, shape (n_lf_samples, 1)
    :param kernel: kernel to use for fitting the low-fidelity gaussian process. Must be one of {'RBF', 'Matern'}
    :type kernel: str, optional
    :param scale_input: normalize model inputs (default = False)
    :type scale_input: bool, optional
    :param scale_response: normalize model outputs (default = False)
    :type scale_input: bool, optional
    """

    def __init__(
        self,
        lf_x: np.ndarray,
        lf_resp: np.ndarray,
        kernel: str = "Matern",
        scale_input: bool = False,
        scale_response: bool = False,
    ):

        self.kernel = kernel
        self.scale_input = scale_input

        self.n_dv = lf_x.shape[1]

        if self.scale_input:
            self.x_scaled, self.scaling_factors, self.biases = normalize_points(lf_x)
        else:
            self.x_scaled = lf_x
            self.scaling_factors = np.ones(self.n_dv)
            self.biases = np.zeros(self.n_dv)

        # construct a gaussian process regression with an anisotropic kernel
        if kernel == "RBF":
            gp_kernel = RBF(length_scale=np.std(self.x_scaled, axis=0))
        elif kernel == "Matern":
            gp_kernel = Matern(
                length_scale=(self.x_scaled.max(axis=0) - self.x_scaled.min(axis=0)) / np.sqrt(len(self.x_scaled)),
                nu=2.5,
            )
        else:
            raise ValueError(f"{kernel} is not a valid gaussian process kernel. Must be either 'RBF' or 'Matern'.")
        self.gp = GaussianProcessRegressor(kernel=gp_kernel, normalize_y=scale_response, random_state=0).fit(
            self.x_scaled, lf_resp
        )

    def predict(self, points: np.ndarray):
        """
        Predict the response of the underlying true function using the Gaussian process regression model.

        :param points: points where the Gaussian Process regression model is to be evaluated
        :type points: np.ndarray, shape (n_points, n_design_variables)
        :return: predictions at the requested points
        :rtype: np.ndarray, shape (n_points, 1)
        """
        # check dimensions
        if len(points.shape) == 1:
            points = points.reshape(-1, 1)

        points_scaled = (points - self.biases) / self.scaling_factors
        return self.gp.predict(points_scaled)


class hierarchicalKriging:
    """
    A hierarchical Kriging surrogate model for multifidelity optimization.

    This class implements the hierarchical Kriging model by Han and Görtz (2012) (DOI: 10.2514/1.J051354).
    The general idea is that the low fidelity points are described using a standard Kriging model. The high fidelity
    points are then described with the low fidelity kriging as a trend function and an additional stationary random process Z

    .. math::
        Y(x) = \\beta_0 \\hat{y}_\\text{lf}(x) + Z(x)

    :param lf_x: low fidelity sampling points
    :type lf_x: np.ndarray, shape (n_lf_samples, n_design_variables)
    :param lf_resp: low fidelity model responses corresponding to the sampling points
    :type lf_resp: np.ndarray, shape (n_lf_samples, 1)
    :param hf_x: high fidelity sampling points
    :type hf_x: np.ndarray, shape (n_hf_samples, n_design_variables)
    :param hf_resp: high fidelity model responses corresponding to the sampling points
    :type hf_resp: np.ndarray, shape (n_hf_samples, 1)
    :param scale_hf_input: whether or not the high fidelity input should be scaled to a unit hypercube centered at origin. This may improve the convergence because of better conditioning of the two-point correlation matrix.
    :param kernel: specify the kernel to use for estimating the two-point correlation. Must be one of {'squared_exponential', 'cubic_spline'}. Default is 'squared_exponential'.
    :type kernel: str, optional
    :param lf_kernel: kernel to use for fitting the low-fidelity gaussian process. Must be one of {'RBF', 'Matern'}. Default is 'Matern'.
    :type lf_kernel: str, optional

    :ivar beta0: hierarchical Kriging parameter beta0
    :ivar theta_opt: hierarchical Kriging parameter theta

    :example: Constructing and using a hierarchical Kriging surrogate model

    .. code:: python

        >>> surrogate = ot.surrogateModels.hierarchicalKriging(lf_x, lf_resp, hf_x, hf_resp)
        >>> surrogate.predict(np.array([[0.2], [0.4]]))
        array([-0.24874606,  0.11477697])

    """

    def __init__(
        self,
        lf_x: np.ndarray,
        lf_resp: np.ndarray,
        hf_x: np.ndarray,
        hf_resp: np.ndarray,
        scale_hf_input: bool = True,
        kernel: str = "squared_exponential",
        lf_kernel: str = "Matern",
    ):
        # format inputs
        if len(lf_x.shape) == 1:
            lf_x = lf_x.reshape(-1, 1)
        self.lf_x = lf_x
        self.lf_resp = lf_resp.reshape(-1, 1)

        if len(hf_x.shape) == 1:
            hf_x = hf_x.reshape(-1, 1)
        self.hf_x = hf_x
        self.hf_resp = hf_resp.reshape(-1, 1)

        # number of design variables
        self.n_dv = hf_x.shape[1]
        self.n_hf_samples = hf_x.shape[0]

        # scale hf input
        if scale_hf_input:
            self.hf_x_scaled, self.hf_scaling_factors, self.hf_biases = normalize_points(self.hf_x)
        else:
            self.hf_x_scaled = self.hf_x
            self.hf_scaling_factors = np.ones(self.n_dv)
            self.hf_biases = np.zeros(self.n_dv)

        self.lf_model = GaussianProcessRegression(
            self.lf_x, self.lf_resp, kernel=lf_kernel, scale_input=True, scale_response=True
        )
        self.lf_prediction = self.lf_model.predict(self.hf_x).reshape(-1, 1)

        # set high-fidelity kernel
        if kernel == "squared_exponential":
            self.kernel = self.kernel_exp
        elif kernel == "cubic_spline":
            if not scale_hf_input:
                raise ValueError(
                    f"cubic_spline kernel only works with scaled HF input, but scale_hf_input={scale_hf_input}"
                )
            self.kernel = self.kernel_cubic_spline
        else:
            raise ValueError(f"kernel {kernel} not supported")

        # initialize data members
        # coefficients for hierarchical Kriging model
        self.beta0 = 0
        self.theta_opt = 0
        # correlation matrix estimated with kernel
        self.R = np.zeros((self.n_hf_samples, self.n_hf_samples), dtype=np.float64)
        # also store inverse correlation matrix since it is often required
        self.R_inv = np.zeros((self.n_hf_samples, self.n_hf_samples), dtype=np.float64)
        # scaled trend residual (hf samples - lf prediction) * beta0_HK
        self.trend_res = np.zeros((self.n_hf_samples, 1))

        # check model construction before evaluation
        self.constructed = False

        # construct upon initialization
        self.construct()

    def kernel_exp(self, x_i: np.ndarray, x_j: np.ndarray, theta: float, p_k: float = 2.0) -> float:
        """
        Squared exponential kernel for approximating a two point correlation. This is the default Gaussian Process Regression Kernel in Dakota.

        .. math::
            R(x_i, x_j) = \\text{exp} \\left( - \\sum_k^m \\theta |x_{i,k} - x_{j,k}|^{p_k} \\right)

        p_k is assumed to be constant for all k

        :param x_i: point in design space
        :type x_i: np.ndarray, shape (1, n_design_variables)
        :param x_j: point in the design space
        :type x_j: np.ndarray, shape (1, n_design_variables)
        :param theta: parameter of the Kriging model. This is tuned by an optimization algorithm
        :param p_k: degree of the exponential kernel (default = 2.0)
        :type p_k: float, optional
        :return: estimation of the two-point correlation
        """
        R_ij = np.exp(-np.sum(theta * np.abs(x_i - x_j) ** p_k))
        return R_ij

    def kernel_cubic_spline(self, x_i: np.ndarray, x_j: np.ndarray, theta: float) -> float:
        """
        Kernel for estimating the two-point correlation using a cubic spline.
        This formulation was used by Han and Görtz (2012) (DOI: 10.2514/1.J051354)
        For the test function that they used, the squared exponential kernel provides a better result

        :param x_i: point in design space
        :type x_i: np.ndarray, shape (1, n_design_variables)
        :param x_j: point in design space
        :type x_j: np.ndarray, shape (1, n_design_variables)
        :param theta: parameter of the Kriging model. This is tuned by an optimization algorithm
        :return: estimation of the two-point correlation
        """
        # spline assumes normalized x to be in [0, 1], but is in [-1, 1]
        x_i = (x_i + 1) / 2
        x_j = (x_j + 1) / 2
        xi = theta * np.abs(x_i - x_j)
        # Evaluate cubic spline
        R = np.where(xi <= 0.2, 1 - 15 * xi**2 + 30 * xi**3, np.where(xi < 1.0, 1.25 * (1 - xi) ** 3, 0.0))
        return np.prod(R)

    def calc_correlation_mat(self, theta: float) -> np.ndarray:
        """
        Calculate the two-point correlation matrix using the specified kernel

        :param theta: parameter of the Kriging model. This is tuned by an optimization algorithm
        :return: correlation matrix
        :rtype: np.ndarray, shape (n_design_variables, n_design_variables)
        """
        R = np.zeros((self.n_hf_samples, self.n_hf_samples))
        for i in range(self.n_hf_samples):
            for j in range(self.n_hf_samples):
                R[i, j] = self.kernel(self.hf_x_scaled[i], self.hf_x_scaled[j], theta)
        R_inv = np.linalg.inv(R)
        # for nu
        return R, R_inv

    def calc_correlation_vec(self, x: np.ndarray) -> np.ndarray:
        """
        calculate the two-point correlation vector of any point x with the high fidelity sampling points

        :param x: arbitrary point where the two-point correlations are evaluated
        :return: two-point correlation vector containing the correlations of x with the high fidelity sampling points
        :rtype: np.ndarray, shape (n_design_variables, 1)
        """
        r = np.zeros((self.n_hf_samples, 1))
        for i in range(self.n_hf_samples):
            r[i] = self.kernel(x, self.hf_x_scaled[i], self.theta_opt)
        return r

    def calc_beta0(self, R_inv: np.ndarray) -> float:
        """
        Calculate the hierarchical Kriging parameter beta0

        :param R_inv: inverse of the correlation matrix
        :type R_inv: np.ndarray, shape (n_design_variables, n_design_variables)
        """
        beta0 = (self.lf_prediction.transpose().dot(R_inv.dot(self.lf_prediction))) ** (
            -1
        ) * self.lf_prediction.transpose().dot(R_inv.dot(self.hf_resp))
        return beta0

    def calc_variance(self, trend_res: np.ndarray, R_inv: np.ndarray) -> float:
        """
        Calculate the variance for HK prediction

        :param trend_res: residual of the trend function (which is the low fidelity Kriging model)

            .. math::
                y_\\text{HF samples} - \\hat{y}_\\text{LF}(x_\\text{HF samples})

        :type trend_res: np.ndarray, shape(n_hf_sampling_points, 1)
        :param R_inv: inverse of the correlation matrix
        :type R_inv: np.ndarray, shape (n_design_variables, n_design_variables)
        :return: estimated variance
        """
        return 1 / self.n_hf_samples * trend_res.transpose().dot(R_inv.dot(trend_res))

    def calc_trend_residual(self, beta0: float) -> np.ndarray:
        """
        Calculate the residual of the trend function (= the low fidelity Kriging)

        .. math::
            y_\\text{HF samples} - \\hat{y}_{lf}(x_\\text{HF samples})

        :param beta0: parameter of the hierarchical Kriging model. This is implicitly tuned by the optimization algorithm that tunes theta
        :return: residual of the trend function
        :rtype: np.ndarray, shape (n_hf_sampling_points, 1)
        """
        trend_res = self.hf_resp - beta0 * self.lf_prediction
        return trend_res

    def store_coeffs(self, theta: float):
        """
        store optimal coefficients as data members of the class

        :param theta: parameter of the hierarchical Kriging model. This is tuned by an optimization algorithm
        """
        self.R, self.R_inv = self.calc_correlation_mat(theta)
        self.beta0 = self.calc_beta0(self.R_inv)
        self.trend_res = self.calc_trend_residual(self.beta0)

    def neg_log_likelihood(self, theta: float) -> float:
        """
        Negative logarithmic likelihood function that is minimized.

        For obtaining the hierarchical Kriging parameters theta and beta0, the likelihood function is maximized.
        For numerical reasons, the logarithmic likelihood function is maximized. For this maximization, the
        DIRECT algorithm is used (following the Kriging implementation in Dakota). As this algorithm only supports
        minimization, the negative logarithmic likelihood function is calculated here. The mathematical formulation is given
        by Han and Görtz (2012) (DOI: 10.2514/1.J051354):

        .. math::
            - \\text{ln}[L(\\theta)] = n \\text{ln}(\\sigma^2(\\theta)) - \\text{ln}(|R(\\theta)|)

        Note that minimization of this function yields an optimal theta and implicitly tunes the other parameter beta0.

        :param theta: parameter of the hierarchical Kriging model.
        """
        # neg log likelihood function
        R, R_inv = self.calc_correlation_mat(theta)
        beta0 = self.calc_beta0(R_inv)
        trend_res = self.calc_trend_residual(beta0)
        variance = self.calc_variance(trend_res, R_inv)
        return self.n_hf_samples * np.log(variance) + np.log(np.linalg.det(R))

    def construct(self):
        """
        This method constructs the hierarchical Kriging model by minimizing the :py:func:`neg_log_likelihood` function using the DIRECT algorithm.
        """
        # get bounds for DIRECT algorithm that is used for
        # obtaining the optimal theta (as calculated in Dakota)
        average_dist = ((np.max(self.hf_x_scaled) - np.min(self.hf_x_scaled)) / self.n_hf_samples) ** (1 / self.n_dv)
        Lk_min = average_dist / 4
        Lk_max = 8 * average_dist
        theta_min = 1 / (2 * Lk_max**2)
        theta_max = 1 / (2 * Lk_min**2)

        # run optimization using DIRECT algorithm
        result = scipy.optimize.direct(
            lambda theta: self.neg_log_likelihood(theta), bounds=scipy.optimize.Bounds(theta_min, theta_max)
        )
        # store optimal coefficients in class
        self.theta_opt = result.x
        self.store_coeffs(self.theta_opt)
        self.constructed = True

    def MSE(self, points: np.ndarray) -> np.ndarray:
        """
        Calculate the mean square error at given points

        :param points: vector of points where the mean square error is to be evaluated
        :type points: np.ndarray, shape (n_points, n_design_variables)
        :return: vector of mean square errors at the requested points
        :rtype: np.ndarray, shape (n_points, 1)
        """
        if not self.constructed:
            raise RuntimeError(
                "The hierarchicalKriging model has not been initialized. Run hierarchicalKriging.construct() first!"
            )
        if len(points.shape) == 1:
            points = points.reshape(-1, 1)

        mean_square_errs = np.zeros(len(points))
        for x_idx, x in enumerate(points):
            x_scaled = (x - self.hf_biases) / self.hf_scaling_factors
            r = self.calc_correlation_vec(x_scaled)
            variance = self.calc_variance(self.trend_res, self.R_inv)
            MSE = variance * (
                1
                - r.transpose().dot(self.R_inv.dot(r))
                + (r.transpose().dot(self.R_inv.dot(self.lf_prediction)) - self.lf_model.predict(np.array([x])))
                * (self.lf_prediction.transpose().dot(self.R_inv.dot(self.lf_prediction))) ** (-1)
                * (
                    r.transpose().dot(self.R_inv.dot(self.lf_prediction)) - self.lf_model.predict(np.array([x]))
                ).transpose()
            )
            mean_square_errs[x_idx] = MSE[0, 0]
        return mean_square_errs

    def predict(self, points: np.ndarray) -> np.ndarray:
        """
        Predict the response of the underlying true function using the hierarchical Kriging model.

        :param points: points where the hierarchical Kriging model is to be evaluated
        :type points: np.ndarray, shape (n_points, n_design_variables)
        :return: predictions at the requested points
        :rtype: np.ndarray, shape (n_points, 1)
        """
        if not self.constructed:
            raise RuntimeError(
                "The hierarchicalKriging model has not been initialized. Run hierarchicalKriging.construct() first!"
            )
        if len(points.shape) == 1:
            points = points.reshape(-1, 1)

        predictions = np.zeros(len(points))
        for x_idx, x in enumerate(points):
            x_scaled = (x - self.hf_biases) / self.hf_scaling_factors
            r = self.calc_correlation_vec(x_scaled)
            prediction = self.lf_model.predict(np.array([x])) * self.beta0 + r.transpose().dot(
                self.R_inv.dot(self.trend_res)
            )
            predictions[x_idx] = prediction[0, 0]

        return predictions
