import random

# Listas de palabras para cada nivel de dificultad
palabras_por_dificultad = {
    "1": ["sol", "casa", "gato", "mesa", "libro"],
    "2": ["python", "juego", "codigo", "teclado", "raton"],
    "3": ["programacion", "ahorcado", "computadora", "algoritmo", "variable"],
}

# Dibujos del ahorcado, uno por cada fallo (de 0 a 6)
# Se usan cadenas r"" para que la barra \ no de problemas
dibujo_ahorcado = [
    r"""
       +---+
       |   |
           |
           |
           |
           |
    """,
    r"""
       +---+
       |   |
       O   |
           |
           |
           |
    """,
    r"""
       +---+
       |   |
       O   |
       |   |
           |
           |
    """,
    r"""
       +---+
       |   |
       O   |
      /|   |
           |
           |
    """,
    r"""
       +---+
       |   |
       O   |
      /|\  |
           |
           |
    """,
    r"""
       +---+
       |   |
       O   |
      /|\  |
      /    |
           |
    """,
    r"""
       +---+
       |   |
       O   |
      /|\  |
      / \  |
           |
    """,
]


# Funcion para que el usuario elija la dificultad
def elegir_dificultad():
    print("Elige la dificultad:")
    print("1. Facil (palabras cortas)")
    print("2. Normal")
    print("3. Dificil (palabras largas)")
    opcion = input("Opcion: ")
    while opcion not in palabras_por_dificultad:
        opcion = input("Opcion no valida. Escribe 1, 2 o 3: ")
    return opcion


# Funcion para elegir una palabra aleatoria de la dificultad elegida
def elegir_palabra(dificultad):
    return random.choice(palabras_por_dificultad[dificultad])


# Bucle principal del juego
while True:
    print("¡Bienvenido al juego del Ahorcado!")
    dificultad = elegir_dificultad()
    palabra = elegir_palabra(dificultad)
    letras_adivinadas = []
    intentos = 6

    print("Tienes", intentos, "intentos para adivinar la palabra.")

    while intentos > 0:
        # Construimos la palabra oculta mostrando solo las letras acertadas
        palabra_mostrada = ""
        for letra in palabra:
            if letra in letras_adivinadas:
                palabra_mostrada += letra + " "
            else:
                palabra_mostrada += "_ "

        print(dibujo_ahorcado[6 - intentos])
        print(palabra_mostrada.strip())

        # Si ya no quedan guiones bajos, el jugador ha ganado
        if "_" not in palabra_mostrada:
            print("¡Felicidades! Has adivinado la palabra:", palabra)
            break

        print("Letras usadas:", ", ".join(letras_adivinadas))
        letra_usuario = input("Adivina una letra: ").lower()

        # Solo se permite una letra
        if len(letra_usuario) != 1 or not letra_usuario.isalpha():
            print("Por favor, ingresa solo una letra.")
            continue

        # No se permiten letras repetidas
        if letra_usuario in letras_adivinadas:
            print("Ya has usado esa letra. Intenta con otra.")
            continue

        letras_adivinadas.append(letra_usuario)

        if letra_usuario in palabra:
            print("¡Correcto!")
        else:
            intentos -= 1
            print("Fallaste. Intentos restantes:", intentos)

    # El else del while solo se ejecuta si se acaban los intentos (sin break)
    else:
        print(dibujo_ahorcado[6])
        print("¡Has perdido! La palabra era:", palabra)

    jugar_nuevamente = input("¿Quieres jugar de nuevo? (s/n): ").lower()
    if jugar_nuevamente != "s":
        break
