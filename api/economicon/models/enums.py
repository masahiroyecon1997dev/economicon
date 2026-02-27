from enum import StrEnum


class DistributionType(StrEnum):
    UNIFORM = "uniform"
    EXPONENTIAL = "exponential"
    NORMAL = "normal"
    GAMMA = "gamma"
    BETA = "beta"
    WEIBULL = "weibull"
    LOGNORMAL = "lognormal"
    BINOMIAL = "binomial"
    BERNOULLI = "bernoulli"
    POISSON = "poisson"
    GEOMETRIC = "geometric"
    HYPERGEOMETRIC = "hypergeometric"
    NEGATIVE_BINOMIAL = "negative_binomial"
    FIXED = "fixed"


class TransformMethodType(StrEnum):
    LOG = "log"
    POWER = "power"
    ROOT = "root"


class RegressionMethodType(StrEnum):
    OLS = "ols"
    LOGIT = "logit"
    PROBIT = "probit"
    TOBIT = "tobit"
    FE = "fe"
    RE = "re"
    IV = "iv"
    FEIV = "feiv"
    LASSO = "lasso"
    RIDGE = "ridge"
    WLS = "wls"
    GLS = "gls"
    FGLS = "fgls"


class StandardErrorMethodType(StrEnum):
    NONROBUST = "nonrobust"
    ROBUST = "robust"
    HAC = "hac"
    CLUSTER = "cluster"


class MissingValueHandlingType(StrEnum):
    IGNORE = "ignore"
    REMOVE = "remove"
    ERROR = "error"


class ConfidenceIntervalStatisticsType(StrEnum):
    MEAN = "mean"
    MEDIAN = "median"
    PROPORTION = "proportion"
    VARIANCE = "variance"
    STD = "standard_deviation"


class DescriptiveStatisticType(StrEnum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    VARIANCE = "variance"
    STD_DEV = "std_dev"
    RANGE = "range"
    IQR = "iqr"


class JoinType(StrEnum):
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"


class FilterOperatorType(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "notEquals"
    GREATER_THAN = "greaterThan"
    LESS_THAN = "lessThan"
    GREATER_THAN_OR_EQUALS = "greaterThanOrEquals"
    LESS_THAN_OR_EQUALS = "lessThanOrEquals"
