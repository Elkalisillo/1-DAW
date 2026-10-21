'''
Esto es un comentario de varias líneas
Me llamo Jesús y estoy aprendiendo Python
Esto es una calculadora
'''
#Se inicia el programa mostrando un menú de opciones al usuario
print("=== CALCULADORA EN PYTHON ===")
print("1. Suma")
print("2. Resta")
print("3. Multiplicación")
print("4. División")
print("5. Division entera")
print("6. Resto de la división")
print("7. Potencia")


#Guardamos la opción seleccionada por el usuario y los dos números a operar
selMenu = int(input("Selecciona una opción: "))
selNum1 = float(input("Ingresa el primer número: "))
selNum2 = float(input("Ingresa el segundo número: "))

#Usamos un match para evaluar la opción seleccionada por el usuario
match selMenu:
    case 1:
        print("El resultado de la suma es: ", selNum1 + selNum2)
    case 2:
        print("El resultado de la resta es: ", selNum1 - selNum2)
    case 3:
        print("El resultado de la multiplicación es: ", selNum1 * selNum2)
    case 4:
        if selNum2 != 0:
            print("El resultado de la división es: ", selNum1 / selNum2)
        else:
            print("Error: No se puede dividir entre cero.")
    case 5:
        if selNum2 != 0:
            print("El resultado de la división entera es: ", selNum1 // selNum2)
        else:
            print("Error: No se puede dividir entre cero.")
    case 6:
        if selNum2 != 0:
            print("El resultado del resto de la división es: ", selNum1 % selNum2)
        else:
            print("Error: No se puede dividir entre cero.")
    case 7:
        print("El resultado de la potencia es: ", selNum1 ** selNum2)
    case _:
        print("Opción no válida.")