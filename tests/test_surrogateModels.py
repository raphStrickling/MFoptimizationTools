import pytest
import numpy as np
import pandas as pd

import optimizationTools as ot


# The high and low fidelity test functions are taken from
# Forrester, A. I. J., Sóbester, A., and Keane, A. J.,
# “Multi-Fidelity Optimization via Surrogate Modeling”
# Proceedings of the Royal Society A: Mathematical, Physical and Engineering Sciences,
# Vol. 463, No. 2088, 2007, pp. 3251–3269. doi:10.1098/rspa.2007.1900


def high_fidelity(x: float) -> float:
    return (6 * x - 2) ** 2 * np.sin(12 * x - 4)


def low_fidelity(x: float) -> float:
    return 0.5 * high_fidelity(x) + 10 * (x - 0.5) - 5


def test_hierarchical_kriging(test_root):
    # sample LF and HF functions
    lf_x = np.linspace(0, 1, 11)
    lf_resp = low_fidelity(lf_x)
    hf_x = np.array([0, 0.4, 0.6, 1])
    hf_resp = np.array([high_fidelity(x) for x in hf_x])

    # similar results regardless of input scaling expected
    for scale in [True, False]:
        hk_surrogate = ot.surrogateModels.hierarchicalKriging(lf_x, lf_resp, hf_x, hf_resp, scale_hf_input=scale)

        # test surrogate against reference
        df_reference = pd.read_csv(f"{test_root}/test_surrogateModels/reference_hierarch_kriging.csv")
        prediction = hk_surrogate.predict(df_reference.x.to_numpy())
        MSE = hk_surrogate.MSE(df_reference.x.to_numpy())  # mean square error estimation

        # test
        np.testing.assert_allclose(df_reference.prediction, prediction, rtol=1e-6, atol=1e-7)
        np.testing.assert_allclose(df_reference.MSE, MSE, rtol=1e-6, atol=1e-7)

    # alternative cubic_spline kernel
    with pytest.raises(ValueError):
        hk_surrogate = ot.surrogateModels.hierarchicalKriging(lf_x, lf_resp, hf_x, hf_resp, kernel="unsupported")
    with pytest.raises(ValueError):
        hk_surrogate = ot.surrogateModels.hierarchicalKriging(
            lf_x, lf_resp, hf_x, hf_resp, kernel="cubic_spline", scale_hf_input=False
        )

    hk_surrogate = ot.surrogateModels.hierarchicalKriging(lf_x, lf_resp, hf_x, hf_resp, kernel="cubic_spline")

    # test surrogate against reference
    df_reference = pd.read_csv(f"{test_root}/test_surrogateModels/reference_hierarch_kriging.csv")
    prediction = hk_surrogate.predict(df_reference.x.to_numpy())
    MSE = hk_surrogate.MSE(df_reference.x.to_numpy())  # mean square error estimation

    # test with looser tolerances: deviations expected here due to different kernel than reference
    np.testing.assert_allclose(df_reference.prediction, prediction, atol=0.1)
