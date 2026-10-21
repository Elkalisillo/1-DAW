# Pao 1 crear la variable con la frase
frase = "Me gusta programar en Python"
print(frase)

# Paso 2 poner la frase en mayusculas
print(frase.upper())

# Paso 3 calcular la longitod de la frase
print("La frase tiene", len(frase), "caracteres")

# Paso 4 concatenar la frase con otra frase
nombre = input("Introduce tu nombre: ")
apellido = input("Introduce tu apellido: ")
frase_completa = nombre + " " + apellido

print(frase_completa)

# Paso 5 dividir la frase en palabras
frase_dividida = frase.split()
print(frase_dividida)
print(frase_dividida[0])  # Imprime la primera palabra

# Paso 6 programa final
pNombre = input("Introduce tu nombre: ")
if len(pNombre) <= 2:
    print("AVISO!! El nombre es corto")
if pNombre == "":
    pNombre = "Nombre"
pApellido = input("Introduce tu apellido: ")
if len(pApellido) <= 2:
    print("AVISO!! El apellido es corto")
if pApellido == "":
    pApellido = "Apellido"
pCiudad = input("Introduce tu ciudad: ")
if len(pCiudad) <= 2:
    print("AVISO!! La ciudad es corta")
if pCiudad == "":
    pCiudad = "Ciudad"
print("Nombre: " + pNombre)
print("Apellido: " + pApellido)
print("Ciudad: " + pCiudad)
print("Mayusculas: " + pNombre.upper() + " " + pApellido.upper())
print("Minusculas: " + pNombre.lower() + " " + pApellido.lower())
print("Letras del nombre: " + str(len(pNombre)))
print ("Iniciales: " + pNombre.upper()[0] + "." + pApellido.upper()[0] + ".")
print("Hola " + pNombre + " " + pApellido + ", de " + pCiudad + ". " + "Tu usuario es: " + pNombre.lower()[0:3]  + pApellido.lower()[0:3] + str(len(pCiudad)))
print("Bienvenido " + pNombre + " " + pApellido + ", de " + pCiudad + ". Tu usuario es: " + pNombre.lower()[0:3]  + pApellido.lower()[0:3] + str(len(pCiudad)))