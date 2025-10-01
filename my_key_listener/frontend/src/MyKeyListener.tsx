// my_key_listener/frontend/src/MyKeyListener.tsx
import React, { useEffect } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

const MyKeyListener: React.FC = () => {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;

      // Ignorar si el foco está en inputs, textareas o elementos editables
      const isEditable =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      if (isEditable) return;

      // Definir qué teclas escuchar
      const allowedKeys: string[] = [
        "Delete",
        "Shift",
        "Escape",
        "ArrowUp",
        "ArrowDown",
      ];

      if (!allowedKeys.includes(event.key)) return;

      // Enviar valor a Streamlit
      Streamlit.setComponentValue(event.key);
      console.log("Tecla detectada:", event.key);
    };

    document.addEventListener("keydown", onKeyDown);
    Streamlit.setFrameHeight();

    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  return <div style={{ outline: "none" }} />;
};

export default withStreamlitConnection(MyKeyListener);
