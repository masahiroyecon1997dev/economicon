from enum import Enum


class DistributionType(str, Enum):
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


class TransformMethodType(str, Enum):
    LOG = "log"
    POWER = "power"
    ROOT = "root"


class RegressionType(str, Enum):
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


class RegressionMethodType(str, Enum):
    OLS = "ols"
    WLS = "wls"
    GLS = "gls"
    GMM = "gmm"


class StandardErrorMethodType(str, Enum):
    NONROBUST = "nonrobust"
    HC0 = "hc0"
    HC1 = "hc1"
    HC2 = "hc2"
    HC3 = "hc3"
    HAC = "hac"
    CLUSTERED = "clustered"


class MissingValueHandlingType(str, Enum):
    IGNORE = "ignore"
    REMOVE = "remove"
    ERROR = "error"


class ConfidenceIntervalStatisticsType(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    PROPORTION = "proportion"
    VARIANCE = "variance"
    STD = "standard_deviation"


class DescriptiveStatisticType(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    VARIANCE = "variance"
    STD_DEV = "std_dev"
    RANGE = "range"
    IQR = "iqr"


class JoinType(str, Enum):
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"


class FilterOperatorType(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "notEquals"
    GREATER_THAN = "greaterThan"
    LESS_THAN = "lessThan"
    GREATER_THAN_OR_EQUALS = "greaterThanOrEquals"
    LESS_THAN_OR_EQUALS = "lessThanOrEquals"
