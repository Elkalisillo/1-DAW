// Conector 2: pedimos prestado el estado
import { estado } from './estado.js';

// Habilidades del héroe que se está creando (aún no guardado)
let habilidadesNuevas = [];

// Conector 3: ir a buscar el JSON y guardarlo en el estado
async function cargarDatos() {
  const respuesta = await fetch('datos/monstruos.json');
  const datos = await respuesta.json();
  estado.monstruos = datos.monstruos;
  estado.heroes = datos.heroes || [];   // por si el JSON aún no tiene héroes
  mostrar();
}

// Conector 4: escribir en el HTML lo que hay en el estado
function mostrar() {
  // Monstruo
  const goblin = estado.monstruos[0];   // [0] = el primero de la lista (Goblin)
  document.querySelector('#info').textContent =
    goblin.nombre + ' tiene ' + goblin.pv + ' PV';

  // Lista de héroes, cada habilidad es un botón que ataca al monstruo
  const lista = document.querySelector('#lista-heroes');
  lista.innerHTML = '';
  estado.heroes.forEach((heroe) => {
    const li = document.createElement('li');
    li.textContent = heroe.nombre + ' (' + heroe.clase + ') - ' + heroe.pv + ' PV ';

    heroe.habilidades.forEach((hab) => {
      const boton = document.createElement('button');
      boton.textContent = hab.nombre + ' (' + hab.danio + ')';
      boton.addEventListener('click', () => {
        goblin.pv = Math.max(0, goblin.pv - hab.danio);  // cambiamos el ESTADO
        mostrar();                                       // y volvemos a dibujar
      });
      li.append(boton);
    });

    lista.append(li);
  });

  // Habilidades pendientes del formulario
  const pendientes = document.querySelector('#habilidades-pendientes');
  pendientes.innerHTML = '';
  habilidadesNuevas.forEach((hab) => {
    const li = document.createElement('li');
    li.textContent = hab.nombre + ' - ' + hab.danio + ' de daño';
    pendientes.append(li);
  });
}

// Conector 4: botón de atacar del principio
document.querySelector('#boton-atacar').addEventListener('click', () => {
  const goblin = estado.monstruos[0];
  goblin.pv = Math.max(0, goblin.pv - 3);
  mostrar();
});

// Añadir una habilidad a la lista temporal
document.querySelector('#boton-add-habilidad').addEventListener('click', () => {
  const inputNombre = document.querySelector('#hab-nombre');
  const inputDanio = document.querySelector('#hab-danio');

  if (inputNombre.value.trim() === '') return;   // sin nombre no se añade

  habilidadesNuevas.push({
    nombre: inputNombre.value.trim(),
    danio: Number(inputDanio.value)              // los inputs dan texto: lo pasamos a número
  });

  inputNombre.value = '';
  mostrar();
});

// Crear el héroe, enviarlo al servidor (que lo guarda en el JSON) y meterlo en el estado
document.querySelector('#form-heroe').addEventListener('submit', async (evento) => {
  evento.preventDefault();   // evita que la página se recargue

  const nuevoHeroe = {
    nombre: document.querySelector('#heroe-nombre').value.trim(),
    clase: document.querySelector('#heroe-clase').value,
    pv: Number(document.querySelector('#heroe-pv').value),
    habilidades: habilidadesNuevas
  };

  // Conector 5: mandar el héroe al servidor para que lo escriba en monstruos.json
  const respuesta = await fetch('/api/heroes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(nuevoHeroe)
  });

  if (!respuesta.ok) {
    alert('No se pudo guardar el héroe');
    return;
  }

  estado.heroes.push(nuevoHeroe);   // también al estado, para verlo sin recargar

  habilidadesNuevas = [];           // empezamos de cero para el siguiente
  evento.target.reset();
  mostrar();
});

// Arrancar todo
cargarDatos();