import math

while True:
    try:
        numero1 = float(input("Ingrese un número a sumar: "))
        break
    except ValueError:
        print("Por favor, ingrese un número entero válido.")

while True:
    try:
        numero2 = float(input("Ingrese otro número a sumar: "))
        break
    except ValueError:
        print("Por favor, ingrese un número entero válido.")

suma = math.fsum([numero1, numero2])

print("La suma es:", suma)