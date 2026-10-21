using System;
using System.Drawing;
using System.Windows.Forms;

namespace MiPrograma
{
    // Creamos la ventana heredando de la clase 'Form' de Windows
    public class VentanaPrincipal : Form
    {
        // 1. Instanciamos tu clase Memory para que la ventana pueda usarla
        private Memory miMemoria = new Memory();

        // 2. Declaramos los botones para modificarlos más adelante
        private Button boton1;
        private Button boton2;

        public VentanaPrincipal()
        {
            // Configuración básica de la ventana
            this.Text = "Mi Panel de Control de Memoria";
            this.Size = new Size(720, 480); // Ancho: 720, Alto: 480 (puedes cambiar el 480)
            this.StartPosition = FormStartPosition.CenterScreen; // Centrar en pantalla
            this.FormBorderStyle = FormBorderStyle.FixedSingle; // Evita que el usuario la deforme

            // Inicializar los componentes
            InicializarComponentes();
        }

        private void InicializarComponentes()
        {
            // Configuración del BOTÓN 1
            boton1 = new Button();
            boton1.Text = "Acción Memoria 1";
            boton1.Size = new Size(150, 40);
            boton1.Location = new Point(50, 50); // Posición (X, Y) dentro de los 720px
            // Enlazamos el botón a un evento (el código que se ejecutará al pulsar)
            boton1.Click += Boton1_Click; 

            // Configuración del BOTÓN 2
            boton2 = new Button();
            boton2.Text = "Acción Memoria 2";
            boton2.Size = new Size(150, 40);
            boton2.Location = new Point(50, 110); 
            boton2.Click += Boton2_Click;

            // Agregamos los botones visualmente a la ventana
            this.Controls.Add(boton1);
            this.Controls.Add(boton2);
        }

        // ¿Qué pasa al hacer clic en el Botón 1?
        private void Boton1_Click(object sender, EventArgs e)
        {
            // Aquí puedes llamar a los métodos de tu clase Memory
            miMemoria.EjecutarAccion();
            MessageBox.Show($"¡Botón 1 pulsado! El valor en Memory es: {miMemoria.ValorEjemplo}");
        }

        // ¿Qué pasa al hacer clic en el Botón 2?
        private void Boton2_Click(object sender, EventArgs e)
        {
            // Código que modificarás más adelante
            MessageBox.Show("Has pulsado el Botón 2 (Pendiente de programar)");
        }
    }

    // El punto de entrada tradicional de la aplicación
    internal static class Program
    {
        [STAThread] // Obligatorio para aplicaciones visuales en Windows
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            
            // Arranca la aplicación mostrando nuestra ventana de 720px
            Application.Run(new VentanaPrincipal());
        }
    }
}