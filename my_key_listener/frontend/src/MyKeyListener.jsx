// my_key_listener/frontend/src/MyKeyListener.jsx
import React, { useEffect } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

const MyKeyListener = () => {
  useEffect(() => {
    const onKeyDown = (event) => {
      const target = event.target;

      // No molestar si escribe en inputs, textareas o campos editables
      const isEditable =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      if (isEditable) return;

      // Solo capturar ciertas teclas
      const allowedKeys = ["Delete", "Shift", "Escape", "ArrowUp", "ArrowDown"];
      if (!allowedKeys.includes(event.key)) return;

      // Enviar la tecla a Streamlit
      Streamlit.setComponentValue(event.key);
      console.log("Tecla detectada:", event.key);
    };

    document.addEventListener("keydown", onKeyDown);
    Streamlit.setFrameHeight();

    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  // No necesitas div con foco aquí
  return <div style={{ outline: "none" }}></div>;
};

export default withStreamlitConnection(MyKeyListener);
