# my_key_listener/__init__.py
import os
import streamlit.components.v1 as components

_component_func = components.declare_component(
    "my_key_listener",
    path=os.path.join(os.path.dirname(__file__), "frontend", "dist")
)

def my_key_listener(default=None, key=None):
    return _component_func(default=default, key=key)
