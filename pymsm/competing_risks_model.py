# -- R source: https://github.com/JonathanSomer/covid-19-multi-state-model/blob/master/model/competing_risks_model.R --#

import stat
import numpy as np
import pandas as pd
from typing import List
from lifelines import CoxPHFitter
from pandas.api.types import is_numeric_dtype


class CompetingRisksModel:
    def __init__(
        self, failure_types: List = None, event_specific_models: List = None
    ) -> None:
        """
        Each element of "event_specific_models"is a dict
        with the following keys:
        1. coefficients
        2. unique_event_times
        3. baseline_hazard
        4. cumulative_baseline_hazard_function
        """
        self.failure_types = failure_types
        self.event_specific_models = event_specific_models

    @staticmethod
    def _assert_valid_dataset(
        df: pd.DataFrame,
        duration_col: str = None,
        event_col: str = None,
        cluster_col: str = None,
        weights_col: str = None,
    ):

        assert df[duration_col].count() == df[event_col].count()

        # t should be non-negative
        assert df[duration_col] >= 0

        # failure types should be integers from 0 to m, not necessarily consecutive
        failure_types = df[event_col].values
        assert all(isinstance(f, int) for f in failure_types)
        assert min(failure_types) >= 0

        # covariates should all be numerical
        covariate_cols = [
            col
            for col in df.columns
            if col not in [duration_col, event_col, cluster_col, weights_col]
        ]
        for col in covariate_cols:
            assert is_numeric_dtype(df[col])

    @staticmethod
    def _break_ties_by_adding_epsilon(
        t: np.ndarray, epsilon_min: float = 0.0, epsilon_max: float = 0.0001
    ):
        np.random.seed(42)
        eps = np.random.uniform(low=epsilon_min, high=epsilon_max, size=len(t))
        _, inverse, count = np.unique(
            t, return_inverse=True, return_counts=True, axis=0
        )
        non_unique_times_idx = np.where(count[inverse] > 1)[
            0
        ]  # find all indices where counts > 1
        # Add epsilon to all non-unique events, leave time zero as is
        t[((non_unique_times_idx) & (t != 0))] = (
            eps + t[((non_unique_times_idx) & (t != 0))]
        )
        return t

    @staticmethod
    def _fit_event_specific_model(
        type: int,
        df: pd.DataFrame,
        duration_col: str = "T",
        event_col: str = "E",
        cluster_col: str = None,
        weights_col: str = None,
        t_start_col: str = None,
        verbose: int = 1,
        **coxph_kwargs,
    ):
        # Treat all 'failure_types' except 'type' as censoring events
        is_event = df[event_col] == type

        if verbose >= 1:
            print(
                f">>> Fitting Transition to State: {type}, n events: {np.sum(is_event)}"
            )

        # TODO what is this:
        #     surv_object = if (is.null(t_start)) Surv(t, is_event) else Surv(t_start, t, is_event)

        cox_model = CoxPHFitter()
        cox_model.fit(
            df=df,
            duration_col=duration_col,
            event_col=event_col,
            weights_col=weights_col,
            cluster_col=cluster_col,
            **coxph_kwargs,
        )

        if verbose >= 2:
            cox_model.print_summary()

        return cox_model

    @staticmethod
    def _extract_necessary_attributes(cox_model):
        # TODO
        pass

    @staticmethod
    def _compute_cif_function(sample_covariates, failure_type):
        pass
        # TODO
        # cif_x = self._unique_event_times(failure_type)
        # cif_y = cumsum(self._hazard_at_unique_event_times(sample_covariates, failure_type)*self._survival_function(cif_x, sample_covariates))
        # return(stepfun(cif_x, c(0, cif_y)))

    @staticmethod
    def _hazard_at_unique_event_times(self, sample_covariates, failure_type):
        # the hazard is given by multiplying the baseline hazard (which has value per unique event time) by the partial hazard
        hazard = self._baseline_hazard(failure_type) * (
            self._partial_hazard(failure_type, sample_covariates)
        )
        assert len(hazard) == len(self._unique_event_times(failure_type))
        return hazard

    @staticmethod
    def _cumulative_baseline_hazard(cox_model: CoxPHFitter):
        return cox_model.baseline_cumulative_hazard_

    @staticmethod
    def _cumulative_baseline_hazard_step_function(cox_model: CoxPHFitter):
        # TODO
        # return(stepfun(coxph.detail(cox_model)$time,
        #            c(0,cumulative_baseline_hazard(cox_model))))
        pass

    def _baseline_hazard(self, failure_type):
        """
        the baseline hazard is given as a non-paramateric function, whose values are given at the times of observed events
        the cumulative hazard is the sum of hazards at times of events, the hazards are then the diffs 
        
        """
        return self.event_specific_models[failure_type].baseline_hazard

    
    def _extract_necessary_attributes(cox_model: CoxPHFitter):

        # TODO what is this?
        # cache all relevant model attributes in one method:
        # ALWAYS CACHE AN UNALTERED COX MODEL! THE COMPUTATION OF THE BASELINE HAZARD IS BASED ON THE COVARIATES!
        # if (0 %in% cox_model$coefficients) print(" ------ WARNING ------: Are you caching a modified cox model?")

        model = dict(
            coefficients=cox_model.params_,
            unique_event_times=cox_model.durations,
            baseline_hazard=cox_model.baseline_hazard_,
            cumulative_baseline_hazard_function=cox_model.baseline_cumulative_hazard_,
        )

        return model

    def _partial_hazard(self, failure_type, sample_covariates):
        # simply e^x_dot_beta for the chosen failure type's coefficients  
        coefs = self.event_specific_models[failure_type]['coefficients']
        x_dot_beta = sample_covariates * coefs
        return(np.exp(x_dot_beta))

    def _unique_event_times(self,failure_type):
        # uses a coxph function which returns unique times, regardless of the original fit which might have tied times. 
        return self.event_specific_models[failure_type]['unique_event_times'] 

    @staticmethod
    def _survival_function(time_passed, sample_covariates):
        # TODO
        pass

    def fit(
        self,
        df: pd.DataFrame,
        duration_col: str = "T",
        event_col: str = "E",
        cluster_col: str = None,
        weights_col: str = None,
        t_start_col: str = None,
        break_ties: bool = True,
        epsilon_min: float = 0.0,
        epsilon_max: float = 0.0001,
        verbose: int = 1,
    ):
        """
        Description:
        ------------------------------------------------------------------------------------------------------------
        This method fits a cox proportional hazards model for each failure type, treating others as censoring events.
        Tied event times are dealt with by adding an epsilon to tied event times.

        Arguments:
        ------------------------------------------------------------------------------------------------------------
        t : numeric vector
        A length n vector of positive times of events

        failure_types: numeric vector
        The event type corresponding to the time in vector t.
        Failure types are encoded as integers from 1 to m.
        Right-censoring events (the only kind of censoring supported) are encoded as 0.
        Thus, the failure type argument holds integers from 0 to m, where m is the number of distinct failure types

        covariates_X: numeric dataframe
        an n by #(covariates) numerical matrix
        All columns are used in the estimate.

        OPTIONAL:

        sample_ids:
        used inside the coxph model in order to identify subjects with repeating entries.

        t_start:
        A length n vector of positive start times, used in case of interval data.
        In that case: left=t_start, and right=t

        epsilon_min/max:
        epsilon is added to events with identical times to break ties.
        epsilon is sampled from a uniform distribution in the range (epsilon_min, epsilon_max)
        these values should be chosen so that they do not change the order of the events.
        """

        self._assert_valid_dataset(
            df, duration_col, event_col, cluster_col, weights_col
        )

        if break_ties:
            t = df[duration_col].copy()
            df[duration_col] = self._break_ties_by_adding_epsilon(
                t, epsilon_min, epsilon_max
            )

        failure_types = df[event_col].unique()
        failure_types = failure_types[failure_types > 0]
        for type in failure_types:
            cox_model = self._fit_event_specific_model(
                df,
                duration_col,
                event_col,
                cluster_col,
                weights_col,
                t_start_col,
                verbose,
            )
            self.event_specific_models[type] = self._extract_necessary_attributes(
                cox_model
            )

    def predict_CIF(self, predict_at_t, sample_covariates, failure_type, time_passed=0):
        """
        Description:
        ------------------------------------------------------------------------------------------------------------
        This method computes the failure-type-specific cumulative incidence function, given that 'time_passed' time
        has passed (default is 0)
        
        Arguments:
        ------------------------------------------------------------------------------------------------------------
        predict_at_t: numeric vector
          times at which the cif will be computed
        
        sample_covariates: numeric vector
          a numerical vector of same length as the covariate matrix the model was fit to.
        
        failure_type: integer
          integer corresponing to the failure type, as given when fitting the model
        
        time_passed: numeric
          compute the cif conditioned on the fact that this amount of time has already passed.
        
        Returns:
        ------------------------------------------------------------------------------------------------------------
        the predicted cumulative incidence values for the given sample_covariates at times predict_at_t.
        """
        cif_function = self._compute_cif_function(sample_covariates, failure_type)

        predictions = cif_function(predict_at_t)

        # re-normalize the probability to account for the time passed
        if time_passed > 0:
            predictions = (
                predictions - cif_function(time_passed)
            ) / self._survival_function(time_passed, sample_covariates)

        return predictions


if __name__ == "__main__":
    pass
