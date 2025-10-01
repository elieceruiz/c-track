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

    return () => divCurrent?.removeEventListener("keydown", onKeyDown);
  }, []);

  return <div ref={divRef} tabIndex={0} style={{ outline: "none" }}>
    Presiona una tecla...
  </div>;
};

export default withStreamlitConnection(MyKeyListener);
