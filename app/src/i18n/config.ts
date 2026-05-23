import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// 言語jsonファイルのimport
import translation_en from "@/i18n/locales/en.json";
import translation_ja from "@/i18n/locales/ja.json";

const resources = {
    ja: {
      translation: translation_ja
    },
    en: {
      translation: translation_en
    }
  };

  i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "ja",
    interpolation: {
      escapeValue: false
    }
  });

  export default i18n;
