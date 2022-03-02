def test_msm():
    # Load data
    from pymsm.datasets import prep_rotterdam

    dataset, states_labels = prep_rotterdam()

    # Define terminal states
    terminal_states = [3]

    # Init MultistateModel
    from pymsm.multi_state_competing_risks_model import (
        MultiStateModel,
        default_update_covariates_function,
    )

    multi_state_model = MultiStateModel(
        dataset, terminal_states, default_update_covariates_function
    )

    # Fit to data
    multi_state_model.fit()

    # Run Monte-carlo simulation
    all_mcs = multi_state_model.run_monte_carlo_simulation(
        sample_covariates=dataset[0].covariates.values,
        origin_state=1,
        current_time=0,
        max_transitions=2,
        n_random_samples=3,
        print_paths=True,
    )


if __name__ == "__main__":
    test_msm()