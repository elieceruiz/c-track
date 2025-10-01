// my_key_listener/frontend/src/MyKeyListener.jsx
import React, { useEffect, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

const MyKeyListener = () => {
  const divRef = useRef(null);

  useEffect(() => {
    const onKeyDown = (event) => {
      Streamlit.setComponentValue(event.key);
      console.log("Tecla detectada:", event.key); // Debug en consola
    };
    const divCurrent = divRef.current;
    // Poner foco para capturar teclado
    divCurrent?.focus();
    // Agregar listener
    divCurrent?.addEventListener("keydown", onKeyDown);
    // Ajustar iframe height
    Streamlit.setFrameHeight();

    // Forzar foco tras clics o toques
    const handleFocus = () => {
      divCurrent?.focus();
      console.log("Foco forzado al div"); // Debug en consola
    };
    document.addEventListener("click", handleFocus);
    document.addEventListener("touchstart", handleFocus); // Soporte móvil

    return () => {
      divCurrent?.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("click", handleFocus);
      document.removeEventListener("touchstart", handleFocus);
    };
  }, []);

  return <div ref={divRef} tabIndex={0} style={{ outline: "none" }}></div>;
};

export default withStreamlitConnection(MyKeyListener);
