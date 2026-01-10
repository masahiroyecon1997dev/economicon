import type { checkInputType } from "../types/commonTypes";

export const checkRequired = (value: string): checkInputType => {
  if (value === "") {
    return { isError: true, message: "Error.Required" };
  }
  return { isError: false, message: "" };
};

export const checkStringLength = (
  value: string,
  length: number
): checkInputType => {
  if (value.length > length) {
    return { isError: true, message: "Error.MaxLength20" };
  }
  return { isError: false, message: "" };
};

export const checkNumber = (value: string): checkInputType => {
  const num = Number(value);
  if (isNaN(num)) {
    return { isError: true, message: "Error.Number" };
  }
  return { isError: false, message: "" };
};

export const checkInteger = (value: string): checkInputType => {
  const pattern = /^([1-9]\d*|0)$/;
  if (!pattern.test(value)) {
    return { isError: true, message: "Error.IntegerMore0" };
  }
  return { isError: false, message: "" };
};
