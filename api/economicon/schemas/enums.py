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
    HECKMAN = "heckman"


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


class DummyMode(StrEnum):
    SINGLE = "single"
    ALL_EXCEPT_BASE = "all_except_base"


class NullStrategy(StrEnum):
    EXCLUDE = "exclude"
    AS_CATEGORY = "as_category"
    ERROR = "error"


class RDDKernelType(StrEnum):
    TRIANGULAR = "triangular"
    EPANECHNIKOV = "epanechnikov"
    UNIFORM = "uniform"


class RDDBandwidthSelectType(StrEnum):
    MSERD = "mserd"
    MSETWO = "msetwo"
    MSESUM = "msesum"
    MSECOMB1 = "msecomb1"
    MSECOMB2 = "msecomb2"
    CERRD = "cerrd"
    CERTWO = "certwo"
    CERSUM = "cersum"
    CERCOMB1 = "cercomb1"
    CERCOMB2 = "cercomb2"


class RDDVceType(StrEnum):
    NN = "nn"
    HC1 = "hc1"
    HC3 = "hc3"
    CLUSTER = "cluster"
    NNCLUSTER = "nncluster"


class DescriptiveStatisticType(StrEnum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    VARIANCE = "variance"
    STD_DEV = "std_dev"
    RANGE = "range"
    IQR = "iqr"
    COUNT = "count"
    NULL_COUNT = "null_count"
    NULL_RATIO = "null_ratio"
    POPULATION_VARIANCE = "population_variance"


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


class LogicalOperatorType(StrEnum):
    AND = "and"
    OR = "or"


class CorrelationMethod(StrEnum):
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"


class MissingHandlingMethod(StrEnum):
    PAIRWISE = "pairwise"
    LISTWISE = "listwise"


class StatisticalTestType(StrEnum):
    T_TEST = "t-test"
    Z_TEST = "z-test"
    F_TEST = "f-test"


class AlternativeHypothesis(StrEnum):
    TWO_SIDED = "two-sided"
    LARGER = "larger"
    SMALLER = "smaller"
