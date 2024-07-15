import React from "react";
import HeaderMenu from "../organisms/HeaderMenu/HeaderMenu";

function App() {
  return (
    <div className="App">
      <HeaderMenu />
      <div className="p-4">
        <h1 className="text-2xl font-bold">Excel-like Header Menu</h1>
        <p>ここにコンテンツを追加します。</p>
      </div>
    </div>
  );
}

export default App;
