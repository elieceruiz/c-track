import React from "react";
import ReactDOM from "react-dom/client";
import MyKeyListener from "./MyKeyListener.jsx";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <MyKeyListener />
  </React.StrictMode>
);
