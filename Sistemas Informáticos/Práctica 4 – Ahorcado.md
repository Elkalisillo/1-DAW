---
tags: [python, juegos, portfolio]
---

# Práctica 4 – Ahorcado

## Descripción

Este programa es el clásico **juego del ahorcado** hecho en Python y se juega en la terminal. El ordenador elige una palabra al azar y el jugador tiene que adivinarla letra a letra. Cada fallo dibuja una parte más del muñeco. Si adivinas todas las letras antes de completar el dibujo, ganas. Si fallas 6 veces, pierdes.

Además, el juego tiene estos extras:
- Puedes elegir la **dificultad** (fácil, normal o difícil).
- **Dibuja el ahorcado** con `print()`.
- Muestra las **letras ya usadas**.
- **No deja repetir** letras.
- **Solo acepta una letra** (no palabras, números ni símbolos).

---

## Explicación del código

### 1. Importar `random` y las listas de palabras

Usamos el módulo `random` para elegir palabras al azar. Las palabras van en un diccionario, con una lista para cada dificultad:

```python
import random

palabras_por_dificultad = {
    "1": ["sol", "casa", "gato", "mesa", "libro"],
    "2": ["python", "juego", "codigo", "teclado", "raton"],
    "3": ["programacion", "ahorcado", "computadora", "algoritmo", "variable"],
}
```

### 2. El dibujo del ahorcado

`dibujo_ahorcado` es una lista con 7 dibujos, desde la horca vacía (0 fallos) hasta el muñeco completo (6 fallos). Se usan cadenas `r"""..."""` para que la barra `\` se muestre bien.

```python
dibujo_ahorcado = [
    r"""
       +---+
       |   |
           |
    ...
    """,
    # ... un dibujo por cada fallo
]
```

Para mostrar el dibujo que toca se hace `dibujo_ahorcado[6 - intentos]`: con 6 intentos se muestra el dibujo 0 y con 0 intentos, el 6.

### 3. Funciones

- `elegir_dificultad()` enseña un pequeño menú y repite la pregunta hasta que el usuario escriba 1, 2 o 3.
- `elegir_palabra(dificultad)` devuelve una palabra al azar de la lista de esa dificultad.

```python
def elegir_palabra(dificultad):
    return random.choice(palabras_por_dificultad[dificultad])
```

### 4. Variables

Al empezar cada partida se preparan las variables:

```python
palabra = elegir_palabra(dificultad)
letras_adivinadas = []   # letras que ha probado el jugador
intentos = 6             # fallos que le quedan
```

### 5. Bucle principal

Hay dos bucles:
- El **exterior** (`while True`) permite jugar varias partidas seguidas. Al final pregunta *"¿Quieres jugar de nuevo?"*.
- El **interior** (`while intentos > 0`) es la partida. Se repite mientras queden intentos.

En cada vuelta se construye la palabra oculta: si la letra se ha adivinado se muestra y, si no, se pone un `_`.

```python
palabra_mostrada = ""
for letra in palabra:
    if letra in letras_adivinadas:
        palabra_mostrada += letra + " "
    else:
        palabra_mostrada += "_ "
```

### 6. Pedir y comprobar letras

Se pide una letra y se pasa a minúscula. Antes de usarla se comprueba:
1. Que sea **una sola letra** (`len == 1` e `isalpha()`).
2. Que **no se haya usado** antes.

```python
letra_usuario = input("Adivina una letra: ").lower()

if len(letra_usuario) != 1 or not letra_usuario.isalpha():
    print("Por favor, ingresa solo una letra.")
    continue

if letra_usuario in letras_adivinadas:
    print("Ya has usado esa letra. Intenta con otra.")
    continue
```

Si es válida, se guarda y se mira si está en la palabra. Si no está, se resta un intento:

```python
letras_adivinadas.append(letra_usuario)

if letra_usuario in palabra:
    print("¡Correcto!")
else:
    intentos -= 1
    print("Fallaste. Intentos restantes:", intentos)
```

### 7. Victoria y derrota

- **Victoria:** si en la palabra mostrada ya no queda ningún `_`, el jugador ha acertado todas las letras. Se felicita al jugador y `break` termina la partida.

```python
if "_" not in palabra_mostrada:
    print("¡Felicidades! Has adivinado la palabra:", palabra)
    break
```

- **Derrota:** si los intentos llegan a 0, el `while` termina sin `break` y se ejecuta su `else`. Ahí se dibuja el muñeco completo y se dice cuál era la palabra.

```python
else:
    print(dibujo_ahorcado[6])
    print("¡Has perdido! La palabra era:", palabra)
```

---

## Pruebas

### Victoria

<!-- Añade aquí tu captura, por ejemplo: ![[imagenes/victoria.png]] -->

### Derrota

<!-- Añade aquí tu captura, por ejemplo: ![[imagenes/derrota.png]] -->

### Extras

#### Elegir dificultad

<!-- ![[imagenes/dificultad.png]] -->

#### Letras repetidas y letras usadas

<!-- ![[imagenes/repetida.png]] -->

#### Solo una letra

<!-- ![[imagenes/solo_una_letra.png]] -->

#### Dibujo del ahorcado

<!-- ![[imagenes/dibujo.png]] -->
