type ValidationResult = string | undefined;

export const validateTableName = (tableName: string): ValidationResult => {
  if (!tableName.trim()) {
    return "ValidationMessages.DataNameRequired";
  }
  return undefined;
};

export const validateNumRows = (numRows: number): ValidationResult => {
  if (numRows < 1) {
    return "ValidationMessages.NumRowsMoreThan0";
  }
  return undefined;
};

export const validateColumnName = (columnName: string): ValidationResult => {
  if (!columnName.trim()) {
    return "ValidationMessages.ColumnNameRequired";
  }
  return undefined;
};

export const validateDistributionParam = (
  distributionType: string,
  params: Record<string, number>,
): Record<string, string | undefined> | undefined => {
  switch (distributionType) {
    case "uniform":
      if (params["low"] >= params["high"]) {
        return {
          low: "ValidationMessages.UniformParamLowHigh",
          high: undefined,
        };
      }
      return undefined;
    case "exponential":
      if (Number(params["rate"]) <= 0) {
        return { rate: "ValidationMessages.ExponentialParamRate" };
      }
      return undefined;
    case "normal":
      if (params["deviation"] <= 0) {
        return { deviation: "ValidationMessages.NormalParamStdDeviation" };
      }
      return undefined;
    case "gamma": {
      let gammaResult = undefined as
        | Record<string, string | undefined>
        | undefined;
      if (params["shape"] <= 0) {
        gammaResult = {
          ...gammaResult,
          shape: "ValidationMessages.GammaParamShape",
        };
      }
      if (params["scale"] <= 0) {
        gammaResult = {
          ...gammaResult,
          scale: "ValidationMessages.GammaParamScale",
        };
      }
      return gammaResult;
    }
    case "beta": {
      let betaResult = undefined as
        | Record<string, string | undefined>
        | undefined;
      if (params["alpha"] <= 0) {
        betaResult = {
          ...betaResult,
          alpha: "ValidationMessages.BetaParamAlpha",
        };
      }
      if (params["beta"] <= 0) {
        betaResult = {
          ...betaResult,
          beta: "ValidationMessages.BetaParamBeta",
        };
      }
      return betaResult;
    }
    case "weibull": {
      let weibullResult = { shape: undefined, scale: undefined } as
        | Record<string, string | undefined>
        | undefined;
      if (params["shape"] <= 0) {
        weibullResult = {
          ...weibullResult,
          shape: "ValidationMessages.WeibullParamShape",
        };
      }
      if (params["scale"] <= 0) {
        weibullResult = {
          ...weibullResult,
          scale: "ValidationMessages.WeibullParamScale",
        };
      }
      return weibullResult;
    }
    case "lognormal":
      if (params["logSD"] <= 0) {
        return { logSD: "ValidationMessages.LognormalParamLogStdDeviation" };
      }
      return undefined;
    case "binomial": {
      let binomialErrors = undefined as
        | Record<string, string | undefined>
        | undefined;
      if (params["trials"] <= 0) {
        binomialErrors = {
          ...binomialErrors,
          trials: "ValidationMessages.BinomialParamTrials",
        };
      }
      if (params["probability"] < 0 || params["probability"] > 1) {
        binomialErrors = {
          ...binomialErrors,
          probability: "ValidationMessages.BinomialParamProbability",
        };
      }
      return binomialErrors;
    }
    case "bernoulli": {
      if (params["probability"] < 0 || params["probability"] > 1) {
        return { probability: "ValidationMessages.BernoulliParamProbability" };
      }
      return undefined;
    }
    case "poisson":
      if (params["lambda"] <= 0) {
        return { lambda: "ValidationMessages.PoissonParamLambda" };
      }
      return undefined;
    case "geometric":
      if (params["probability"] < 0 || params["probability"] > 1) {
        return { probability: "ValidationMessages.GeometricParamProbability" };
      }
      return undefined;
    case "hypergeometric": {
      let hypergeomErrors = undefined as
        | Record<string, string | undefined>
        | undefined;
      if (params["populationSize"] <= 0) {
        hypergeomErrors = {
          ...hypergeomErrors,
          populationSize: "ValidationMessages.HypergeometricParamValues",
        };
      }
      if (
        params["numberOfSuccesses"] < 0 ||
        params["numberOfSuccesses"] > params["populationSize"]
      ) {
        hypergeomErrors = {
          ...hypergeomErrors,
          numberOfSuccesses: "ValidationMessages.HypergeometricParamValues",
        };
      }
      if (
        params["sampleSize"] < 0 ||
        params["sampleSize"] > params["populationSize"]
      ) {
        hypergeomErrors = {
          ...hypergeomErrors,
          sampleSize: "ValidationMessages.HypergeometricParamValues",
        };
      }
      return hypergeomErrors;
    }
    default:
      return undefined;
  }
};
