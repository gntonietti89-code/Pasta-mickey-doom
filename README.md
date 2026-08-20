# Papi Mickey: Pasillos del Poder

Shooter retro de primera persona inspirado en los FPS de los 90. El protagonista es Papi Mickey y debe despejar un laberinto de enemigos caricaturizados.

Los nombres de los enemigos son una parodia de figuras publicas chilenas y el juego no afirma representar sus rostros reales ni tiene afiliacion politica.

## Retratos PNG

El juego busca estos archivos en `assets/enemies/`:

- `boric.png`
- `bachelet.png`
- `pinera.png`
- `allende.png`
- `senador.png`

Debes aportar las imagenes y usarlas con los permisos correspondientes. Si falta alguna, el juego usa automaticamente el retrato geometrico de respaldo. Las imagenes se cargan al iniciar y las versiones redimensionadas se conservan en memoria durante cada fotograma para que Tkinter no las pierda.

## Ejecutar

Desde esta carpeta:

```powershell
py -3 -m pip install -r requirements.txt
py -3 main.py
```

## Controles

- `W` / `S`: avanzar y retroceder
- `A` / `D`: desplazamiento lateral
- Flechas izquierda/derecha: girar
- `Espacio`: lanzar un disparo arcade
- `Q` / `E`: cambiar entre armas encontradas
- `P`: pausar
- `R`: reiniciar

Tkinter suele venir incluido con Python para Windows; Pillow se instala con `requirements.txt`.

## Progresion

Cada nivel duplica la cantidad de enemigos: 2, 4, 8, etc. Los enemigos persiguen al jugador y se vuelven mas agresivos con cada nivel. Las armas aparecen dentro de los pasillos; acercate a una para recogerla y alterna el inventario con `Q` y `E`.
