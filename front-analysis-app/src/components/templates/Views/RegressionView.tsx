import { RegressionTab } from "../../organisms/Tab/RegressionTab";
import { MainViewLayout } from "../Layouts/MainViewLayout";

export const RegressionView = () => {

  return (
    <MainViewLayout
      maxWidth="6xl"
    >
      <RegressionTab />
    </MainViewLayout>
  );
};
