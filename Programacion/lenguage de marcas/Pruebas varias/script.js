let miObjeto1 = [
{
    nombre: "Juan",
    edad: 30,
    ciudad: "Madrid"
},
{
    nombre: "María",
    edad: 25,
    ciudad: "Barcelona"
},
{
    nombre: "Pedro",
    edad: 35,
    ciudad: "Valencia"
}];

for (let i = 0; i < miObjeto1.length; i++) {
    console.log("Nombre: " + miObjeto1[i].nombre);
    console.log("Edad: " + miObjeto1[i].edad);
    console.log("Ciudad: " + miObjeto1[i].ciudad);
    console.log("--------------------");
}