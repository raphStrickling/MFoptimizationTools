import numpy as np

import dakota.interfacing as di


@np.vectorize
def himmelblau(x: float, y: float) -> float:
    """
    test function for testing the performance of optimization algorithms
    """
    return (x**2 + y - 11) ** 2 + (x + y**2 - 7) ** 2


@di.python_interface
def eval(batch_params, batch_results):
    """
    Evaluate the Himmelblau test function using Dakota's direct python interface

    Note: The direct interface is an optional component and must be enabled at compile time.
    """
    if not isinstance(batch_params, di.BatchParameters):
        raise ValueError(f"batch_params must be of type di.BatchParameters, but got {type(batch_params)}")
    if not isinstance(batch_results, di.BatchResults):
        raise ValueError(f"batch_params must be of type di.BatchParameters, but got {type(batch_params)}")

    # put parameters from batch_params into numpy array
    n_evaluations = len(batch_params)
    input_vars = np.zeros((n_evaluations, 2))
    for eval_idx in range(n_evaluations):
        input_vars[eval_idx, :] = np.array(list(batch_params[eval_idx].values()))

    # evaluate surrogate model at these points
    himmelblau_vals = himmelblau(input_vars[:, 0], input_vars[:, 1])

    # put himmelblau_vals into results file
    for eval_idx, result in enumerate(batch_results):
        result["obj_fn"].function = himmelblau_vals[eval_idx]

    return batch_results
