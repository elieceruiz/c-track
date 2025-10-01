#!/bin/bash
echo ">>> Entrando al frontend y construyendo React"
cd my_key_listener/frontend
npm install
npm run build
echo ">>> Build terminado, carpeta dist creada"
