import numpy as np
import pandas as pd

import optimizationTools as ot


def compare_predictions(surrogate: callable, df_reference: pd.DataFrame):
    x = np.linspace(-3.5, 3.5, 75)
    y = np.linspace(-3.5, 3.5, 75)
    X, Y = np.meshgrid(x, y)
    inputs = np.column_stack([X.ravel(), Y.ravel()])
    predictions = surrogate(inputs)
    np.testing.assert_allclose(predictions, df_reference["prediction"], rtol=1e-6)


def test_polynomial(test_root):
    poly = ot.surrogateTools.load_polynomial_surfpack(f"{test_root}/test_surrogateTools/surfpack_cubic_polynomial.alg")
    df_reference = pd.read_csv(f"{test_root}/test_surrogateTools/predictions_polynomial.csv")
    compare_predictions(poly, df_reference)


def test_gaussian_process(test_root):
    gp = ot.surrogateTools.load_gaussian_process_surfpack(
        f"{test_root}/test_surrogateTools/surfpack_gaussian_process.alg"
    )
    df_reference = pd.read_csv(f"{test_root}/test_surrogateTools/predictions_gaussian_process.csv")
    compare_predictions(gp, df_reference)
