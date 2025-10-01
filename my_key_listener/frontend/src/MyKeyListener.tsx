// my_key_listener/frontend/src/MyKeyListener.tsx
import React, { useEffect, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

const MyKeyListener = () => {
  const divRef = useRef(null);

  useEffect(() => {
    const onKeyDown = (event) => {
      Streamlit.setComponentValue(event.key);
    };
    const divCurrent = divRef.current;
    // Poner foco para capturar teclado
    divCurrent?.focus();
    // Agregar listener
    divCurrent?.addEventListener("keydown", onKeyDown);
    // Ajustar iframe height
    Streamlit.setFrameHeight();

    // Forzar foco tras cada render (por dropdowns)
    const handleFocus = () => divCurrent?.focus();
    document.addEventListener("click", handleFocus);
    return () => {
      divCurrent?.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("click", handleFocus);
    };
  }, []);

  return <div ref={divRef} tabIndex={0} style={{ outline: "none" }}></div>;
};

export default withStreamlitConnection(MyKeyListener);
