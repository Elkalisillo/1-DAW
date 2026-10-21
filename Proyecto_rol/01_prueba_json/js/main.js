// Conector 2: pedimos prestado el estado
import { estado } from './estado.js';

// Conector 3: ir a buscar el JSON y guardarlo en el estado
async function cargarDatos() {
  const respuesta = await fetch('datos/monstruos.json');
  const datos = await respuesta.json();
  estado.monstruos = datos.monstruos;   // copiamos la lista al estado
  mostrar();
}

// Conector 4: escribir en el HTML lo que hay en el estado
function mostrar() {
  const goblin = estado.monstruos[1];   // [0] = el primero de la lista
  document.querySelector('#info').textContent =
    goblin.nombre + ' tiene ' + goblin.pv + ' PV';
}

// Conector 4: reaccionar al botón
document.querySelector('#boton-atacar').addEventListener('click', () => {
  estado.monstruos[1].pv = estado.monstruos[1].pv - 3;  // cambiamos el ESTADO
  mostrar();                                            // y volvemos a dibujar
});

// Arrancar todo
cargarDatos();