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
