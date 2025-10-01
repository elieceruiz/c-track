// my_key_listener/frontend/src/MyKeyListener.tsx
import React, { useEffect } from "react"
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib"

const MyKeyListener = () => {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      Streamlit.setComponentValue(e.key)  // devuelve la tecla
    }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [])

  return <div></div>  // Quitamos el texto y dejamos el div vacío
}

export default withStreamlitConnection(MyKeyListener)
