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

  return <div>🎹 Presiona una tecla…</div>
}

export default withStreamlitConnection(MyKeyListener)
