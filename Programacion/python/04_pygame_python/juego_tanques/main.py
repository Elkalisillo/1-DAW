"""
BATALLA DE TANQUES - Unidad 2: Python + Pygame

Controles:
    W A S D        -> mover el tanque
    Ratón          -> apuntar la torreta
    Clic / ESPACIO -> disparar
    P / ESC        -> pausa
    M              -> silenciar / activar música

Conceptos del temario que se usan:
    - Inicio de pygame, ventana, Surface, colores, fill, blit, update
    - Eventos (QUIT, KEYDOWN, MOUSEBUTTONDOWN) y teclado continuo (get_pressed)
    - Sonido (mixer.Sound) y música de fondo (mixer.music)
    - Texto y fuentes (pygame.font)
    - Tiempo: Clock, FPS, movimiento con dt y temporizadores (set_timer)
    - Colisiones con Rect (colliderect, clipline)
    - Clases, encapsulamiento (atributos privados + @property)
    - Herencia y polimorfismo (Tanque -> Jugador / Enemigos, Obstaculo -> Muro / Barricada)
"""
import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------
TAM_CASILLA = 48
COLUMNAS, FILAS = 20, 14
ALTO_HUD = 48
ANCHO = COLUMNAS * TAM_CASILLA                 # 960
ALTO = FILAS * TAM_CASILLA + ALTO_HUD          # 720
FPS = 60

BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (220, 50, 50)
VERDE = (70, 200, 90)
AMARILLO = (250, 210, 70)
GRIS = (150, 150, 150)
FONDO_HUD = (28, 32, 28)

CARPETA = os.path.dirname(os.path.abspath(__file__))
CARPETA_IMAGENES = os.path.join(CARPETA, "imagenes")
CARPETA_SONIDOS = os.path.join(CARPETA, "sonidos")
ARCHIVO_RECORD = os.path.join(CARPETA, "record.txt")

# Mapa del nivel:  # = muro   B = barricada   J = jugador   E = aparición enemigos
MAPA = [
    "####################",
    "#E.......EE.......E#",
    "#..................#",
    "#..BBB...##...BBB..#",
    "#..#.....##.....#..#",
    "#..#..B......B..#..#",
    "#.....B..##..B.....#",
    "#BB......##......BB#",
    "#.....B......B.....#",
    "#..#..B..BB..B..#..#",
    "#..#............#..#",
    "#..BBB...J....BBB..#",
    "#..................#",
    "####################",
]

# Eventos personalizados (temporizadores)
EVENTO_APARICION = pygame.USEREVENT + 1


# ---------------------------------------------------------------------------
# CARGA DE RECURSOS (nunca dentro del bucle principal)
# ---------------------------------------------------------------------------
def cargar_imagen(nombre):
    return pygame.image.load(os.path.join(CARPETA_IMAGENES, nombre)).convert_alpha()


class SonidoMudo:
    """Se usa si el ordenador no tiene audio: tiene el mismo método play()."""
    def play(self):
        pass

    def set_volume(self, volumen):
        pass


def cargar_sonido(nombre, volumen=0.5):
    try:
        sonido = pygame.mixer.Sound(os.path.join(CARPETA_SONIDOS, nombre))
    except pygame.error:
        return SonidoMudo()
    sonido.set_volume(volumen)
    return sonido


class Recursos:
    """Agrupa todas las imágenes y sonidos para cargarlos una sola vez."""
    def __init__(self):
        self.tanques = {}
        for tipo in ("jugador", "enemigo", "rapido", "pesado"):
            self.tanques[tipo] = (cargar_imagen(f"tanque_{tipo}_cuerpo.png"),
                                  cargar_imagen(f"tanque_{tipo}_canon.png"))
        self.bala_jugador = cargar_imagen("bala_jugador.png")
        self.bala_enemigo = cargar_imagen("bala_enemigo.png")
        self.bala_pesada = cargar_imagen("bala_pesada.png")
        self.muro = cargar_imagen("muro.png")
        self.barricada = [cargar_imagen(f"barricada_{i}.png") for i in range(3)]
        self.suelo = [cargar_imagen("suelo_hierba.png"), cargar_imagen("suelo_tierra.png")]
        self.explosion = [cargar_imagen(f"explosion_{i}.png") for i in range(8)]
        self.botiquin = cargar_imagen("botiquin.png")
        self.mira = cargar_imagen("mira.png")

        self.snd_disparo = cargar_sonido("disparo.wav", 0.35)
        self.snd_explosion = cargar_sonido("explosion.wav", 0.6)
        self.snd_impacto = cargar_sonido("impacto.wav", 0.4)
        self.snd_recoger = cargar_sonido("recoger.wav", 0.5)
        self.snd_game_over = cargar_sonido("game_over.wav", 0.6)


def angulo_desde_direccion(dx, dy):
    """Ángulo para pygame.transform.rotate sabiendo que los sprites miran hacia arriba."""
    return math.degrees(math.atan2(-dx, -dy))


# ---------------------------------------------------------------------------
# OBSTÁCULOS (herencia + polimorfismo)
# ---------------------------------------------------------------------------
class Obstaculo:
    def __init__(self, x, y, imagen):
        self.rect = pygame.Rect(x, y, TAM_CASILLA, TAM_CASILLA)
        self.imagen = imagen
        self.destruido = False

    def recibir_impacto(self, danio):
        """Cada tipo de obstáculo reacciona a su manera."""
        pass

    def dibujar(self, superficie):
        superficie.blit(self.imagen, self.rect)


class Muro(Obstaculo):
    """Indestructible: las balas rebotan sin hacerle nada."""
    def recibir_impacto(self, danio):
        pass


class Barricada(Obstaculo):
    """Cajas de madera que se rompen tras varios impactos."""
    VIDA_MAXIMA = 60

    def __init__(self, x, y, imagenes):
        super().__init__(x, y, imagenes[0])
        self.__imagenes = imagenes
        self.__vida = Barricada.VIDA_MAXIMA

    @property
    def vida(self):
        return self.__vida

    def recibir_impacto(self, danio):
        self.__vida -= danio
        if self.__vida <= 0:
            self.destruido = True
            return
        # Cambia el sprite según lo dañada que esté
        estado = int((1 - self.__vida / Barricada.VIDA_MAXIMA) * len(self.__imagenes))
        self.imagen = self.__imagenes[min(estado, len(self.__imagenes) - 1)]


# ---------------------------------------------------------------------------
# BALAS, EXPLOSIONES Y OBJETOS
# ---------------------------------------------------------------------------
class Bala:
    def __init__(self, x, y, dx, dy, velocidad, danio, imagen, del_jugador):
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.velocidad = velocidad
        self.danio = danio
        self.del_jugador = del_jugador
        self.imagen = pygame.transform.rotate(imagen, angulo_desde_direccion(dx, dy))
        tam = 10 if danio < 20 else 14
        self.rect = pygame.Rect(0, 0, tam, tam)
        self.rect.center = (round(x), round(y))
        self.activa = True

    def actualizar(self, dt):
        self.x += self.dx * self.velocidad * dt
        self.y += self.dy * self.velocidad * dt
        self.rect.center = (round(self.x), round(self.y))
        if not (0 <= self.x <= ANCHO and 0 <= self.y <= ALTO - ALTO_HUD):
            self.activa = False

    def dibujar(self, superficie):
        superficie.blit(self.imagen, self.imagen.get_rect(center=self.rect.center))


class Explosion:
    DURACION_FOTOGRAMA = 0.06

    def __init__(self, x, y, fotogramas, escala=1.0):
        if escala != 1.0:
            fotogramas = [pygame.transform.smoothscale_by(f, escala) for f in fotogramas]
        self.fotogramas = fotogramas
        self.x, self.y = x, y
        self.tiempo = 0
        self.terminada = False

    def actualizar(self, dt):
        self.tiempo += dt
        if self.tiempo >= self.DURACION_FOTOGRAMA * len(self.fotogramas):
            self.terminada = True

    def dibujar(self, superficie):
        indice = min(int(self.tiempo / self.DURACION_FOTOGRAMA), len(self.fotogramas) - 1)
        imagen = self.fotogramas[indice]
        superficie.blit(imagen, imagen.get_rect(center=(self.x, self.y)))


class Botiquin:
    CURACION = 30
    DURACION = 10

    def __init__(self, x, y, imagen):
        self.imagen = imagen
        self.rect = imagen.get_rect(center=(x, y))
        self.tiempo = 0

    @property
    def caducado(self):
        return self.tiempo >= self.DURACION

    def actualizar(self, dt):
        self.tiempo += dt

    def dibujar(self, superficie):
        # Parpadea en los últimos 3 segundos
        if self.tiempo > self.DURACION - 3 and int(self.tiempo * 8) % 2 == 0:
            return
        flotar = math.sin(self.tiempo * 4) * 3
        superficie.blit(self.imagen, self.rect.move(0, flotar))


# ---------------------------------------------------------------------------
# TANQUES (clase base + clases hijas)
# ---------------------------------------------------------------------------
class Tanque:
    def __init__(self, x, y, imagenes, vida, velocidad, tam_hitbox, cadencia):
        self._img_cuerpo, self._img_canon = imagenes
        self.__vida = vida
        self.__vida_maxima = vida
        self.velocidad = velocidad
        self.cadencia = cadencia            # segundos entre disparos
        self._recarga = 0
        self._x, self._y = float(x), float(y)
        self.rect = pygame.Rect(0, 0, tam_hitbox, tam_hitbox)
        self.rect.center = (x, y)
        self.angulo_cuerpo = 0
        self.angulo_canon = 0
        self.tiempo_golpe = 0              # para el parpadeo al recibir daño

    # --- Encapsulamiento: la vida solo se cambia con métodos ---
    @property
    def vida(self):
        return self.__vida

    @property
    def vida_maxima(self):
        return self.__vida_maxima

    @property
    def esta_vivo(self):
        return self.__vida > 0

    def recibir_danio(self, cantidad):
        self.__vida = max(0, self.__vida - cantidad)
        self.tiempo_golpe = 0.15

    def curar(self, cantidad):
        self.__vida = min(self.__vida_maxima, self.__vida + cantidad)

    # --- Movimiento con colisiones (eje por eje para poder deslizar) ---
    def _mover(self, dx, dy, dt, obstaculos, otros_tanques):
        """Devuelve True si el tanque ha chocado con algo."""
        choque = False
        for eje in ("x", "y"):
            anterior = (self._x, self._y)
            if eje == "x":
                self._x += dx * self.velocidad * dt
            else:
                self._y += dy * self.velocidad * dt
            self.rect.center = (round(self._x), round(self._y))
            bloqueado = any(self.rect.colliderect(o.rect) for o in obstaculos)
            bloqueado = bloqueado or any(t is not self and self.rect.colliderect(t.rect)
                                         for t in otros_tanques)
            if bloqueado:
                self._x, self._y = anterior
                self.rect.center = (round(self._x), round(self._y))
                choque = True
        return choque

    def _crear_bala(self, angulo_extra=0, velocidad=520, danio=10, imagen=None, del_jugador=False):
        ang = math.radians(self.angulo_canon + angulo_extra)
        dx, dy = -math.sin(ang), -math.cos(ang)
        distancia = self._img_canon.get_width() * 0.48
        return Bala(self._x + dx * distancia, self._y + dy * distancia,
                    dx, dy, velocidad, danio, imagen, del_jugador)

    def puede_disparar(self):
        return self._recarga <= 0

    def disparar(self, recursos):
        """Cada tipo de tanque dispara de forma distinta (polimorfismo)."""
        return []

    def actualizar_tiempos(self, dt):
        self._recarga = max(0, self._recarga - dt)
        self.tiempo_golpe = max(0, self.tiempo_golpe - dt)

    def dibujar(self, superficie):
        if self.tiempo_golpe > 0 and int(self.tiempo_golpe * 40) % 2 == 0:
            return  # parpadeo al recibir daño
        cuerpo = pygame.transform.rotate(self._img_cuerpo, self.angulo_cuerpo)
        canon = pygame.transform.rotate(self._img_canon, self.angulo_canon)
        centro = self.rect.center
        superficie.blit(cuerpo, cuerpo.get_rect(center=centro))
        superficie.blit(canon, canon.get_rect(center=centro))

    def dibujar_barra_vida(self, superficie):
        ancho = self.rect.width
        x, y = self.rect.left, self.rect.top - 12
        proporcion = self.vida / self.vida_maxima
        pygame.draw.rect(superficie, (40, 0, 0), (x, y, ancho, 5))
        pygame.draw.rect(superficie, VERDE if proporcion > 0.4 else ROJO, (x, y, ancho * proporcion, 5))


class TanqueJugador(Tanque):
    def __init__(self, x, y, recursos):
        super().__init__(x, y, recursos.tanques["jugador"], vida=100, velocidad=170,
                         tam_hitbox=40, cadencia=0.3)

    def actualizar(self, dt, teclas, raton, obstaculos, tanques):
        self.actualizar_tiempos(dt)
        dx = (teclas[pygame.K_d] - teclas[pygame.K_a])
        dy = (teclas[pygame.K_s] - teclas[pygame.K_w])
        if dx or dy:
            longitud = math.hypot(dx, dy)            # para que en diagonal no vaya más rápido
            dx, dy = dx / longitud, dy / longitud
            self.angulo_cuerpo = angulo_desde_direccion(dx, dy)
            self._mover(dx, dy, dt, obstaculos, tanques)
        # La torreta sigue al ratón
        mx, my = raton
        self.angulo_canon = angulo_desde_direccion(mx - self._x, my - self._y)

    def disparar(self, recursos):
        self._recarga = self.cadencia
        return [self._crear_bala(velocidad=600, danio=25, imagen=recursos.bala_jugador, del_jugador=True)]


class TanqueEnemigo(Tanque):
    """Enemigo normal: patrulla y dispara cuando ve al jugador."""
    PUNTOS = 100
    TIPO = "enemigo"

    def __init__(self, x, y, recursos, vida=50, velocidad=90, tam_hitbox=40, cadencia=1.6):
        super().__init__(x, y, recursos.tanques[self.TIPO], vida, velocidad, tam_hitbox, cadencia)
        self.dx, self.dy = 0, 1
        self.tiempo_cambio = 0
        self._recarga = random.uniform(0.5, cadencia)
        self.alcance = 420

    def _elegir_direccion(self, jugador):
        if random.random() < 0.55:
            # Ir hacia el jugador por el eje en el que esté más lejos
            vx, vy = jugador.rect.centerx - self._x, jugador.rect.centery - self._y
            if abs(vx) > abs(vy):
                self.dx, self.dy = (1 if vx > 0 else -1), 0
            else:
                self.dx, self.dy = 0, (1 if vy > 0 else -1)
        else:
            self.dx, self.dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.tiempo_cambio = random.uniform(1.0, 2.5)

    def ve_al_jugador(self, jugador, obstaculos):
        inicio, fin = self.rect.center, jugador.rect.center
        if math.dist(inicio, fin) > self.alcance:
            return False
        return not any(o.rect.clipline(inicio, fin) for o in obstaculos)

    def actualizar(self, dt, jugador, obstaculos, tanques):
        self.actualizar_tiempos(dt)
        self.tiempo_cambio -= dt
        if self.tiempo_cambio <= 0:
            self._elegir_direccion(jugador)
        if self._mover(self.dx, self.dy, dt, obstaculos, tanques):
            self._elegir_direccion(jugador)
        self.angulo_cuerpo = angulo_desde_direccion(self.dx, self.dy)
        self.angulo_canon = angulo_desde_direccion(jugador.rect.centerx - self._x,
                                                   jugador.rect.centery - self._y)

    def disparar(self, recursos):
        self._recarga = self.cadencia
        return [self._crear_bala(velocidad=380, danio=10, imagen=recursos.bala_enemigo)]


class TanqueRapido(TanqueEnemigo):
    """Pequeño, rápido y frágil. Dispara a menudo."""
    PUNTOS = 150
    TIPO = "rapido"

    def __init__(self, x, y, recursos):
        super().__init__(x, y, recursos, vida=30, velocidad=160, tam_hitbox=36, cadencia=0.9)

    def disparar(self, recursos):
        self._recarga = self.cadencia
        return [self._crear_bala(velocidad=460, danio=7, imagen=recursos.bala_enemigo)]


class TanquePesado(TanqueEnemigo):
    """Lento y muy resistente. Dispara tres balas en abanico."""
    PUNTOS = 300
    TIPO = "pesado"

    def __init__(self, x, y, recursos):
        super().__init__(x, y, recursos, vida=150, velocidad=55, tam_hitbox=46, cadencia=2.4)
        self.alcance = 520

    def disparar(self, recursos):
        self._recarga = self.cadencia
        return [self._crear_bala(angulo, velocidad=300, danio=20, imagen=recursos.bala_pesada)
                for angulo in (-15, 0, 15)]


# ---------------------------------------------------------------------------
# JUEGO
# ---------------------------------------------------------------------------
class Juego:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.hay_audio = True
        except pygame.error:
            self.hay_audio = False

        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Batalla de Tanques")
        self.reloj = pygame.time.Clock()
        self.recursos = Recursos()
        pygame.display.set_icon(self.recursos.tanques["jugador"][0])

        self.fuente_titulo = pygame.font.Font(None, 96)
        self.fuente_grande = pygame.font.Font(None, 56)
        self.fuente = pygame.font.Font(None, 32)
        self.fuente_peque = pygame.font.Font(None, 24)
        self.fuente_hud = pygame.font.Font(None, 28)

        self.mundo = pygame.Surface((ANCHO, ALTO - ALTO_HUD))  # aquí se dibuja el campo de batalla
        self.fondo = self._crear_fondo()
        self.record = self._leer_record()
        self.musica_activa = True
        self._iniciar_musica()

        self.estado = "menu"
        self.nueva_partida()
        pygame.time.set_timer(EVENTO_APARICION, 1100)

    # --- Preparación ---
    def _crear_fondo(self):
        fondo = pygame.Surface(self.mundo.get_size())
        aleatorio = random.Random(3)
        for fila in range(FILAS):
            for col in range(COLUMNAS):
                tierra = aleatorio.random() < 0.18
                fondo.blit(self.recursos.suelo[1 if tierra else 0], (col * TAM_CASILLA, fila * TAM_CASILLA))
        return fondo

    def _iniciar_musica(self):
        if not self.hay_audio:
            return
        try:
            pygame.mixer.music.load(os.path.join(CARPETA_SONIDOS, "musica.wav"))
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
        except pygame.error:
            self.hay_audio = False

    def _leer_record(self):
        try:
            with open(ARCHIVO_RECORD) as archivo:
                return int(archivo.read().strip() or 0)
        except (OSError, ValueError):
            return 0

    def _guardar_record(self):
        if self.puntos > self.record:
            self.record = self.puntos
            try:
                with open(ARCHIVO_RECORD, "w") as archivo:
                    archivo.write(str(self.record))
            except OSError:
                pass

    def nueva_partida(self):
        self.obstaculos = []
        self.puntos_aparicion = []
        inicio_jugador = (ANCHO // 2, (ALTO - ALTO_HUD) // 2)
        for fila, linea in enumerate(MAPA):
            for col, letra in enumerate(linea):
                x, y = col * TAM_CASILLA, fila * TAM_CASILLA
                centro = (x + TAM_CASILLA // 2, y + TAM_CASILLA // 2)
                if letra == "#":
                    self.obstaculos.append(Muro(x, y, self.recursos.muro))
                elif letra == "B":
                    self.obstaculos.append(Barricada(x, y, self.recursos.barricada))
                elif letra == "J":
                    inicio_jugador = centro
                elif letra == "E":
                    self.puntos_aparicion.append(centro)

        self.jugador = TanqueJugador(*inicio_jugador, self.recursos)
        self.enemigos = []
        self.balas = []
        self.explosiones = []
        self.botiquines = []
        self.puntos = 0
        self.oleada = 0
        self.cola_enemigos = []
        self.espera_oleada = 1.5
        self.tiempo_cartel = 0
        self.temblor = 0
        self.tiempo_partida = 0

    def _preparar_oleada(self):
        self.oleada += 1
        cantidad = 2 + self.oleada * 2
        tipos = [TanqueEnemigo]
        if self.oleada >= 2:
            tipos.append(TanqueRapido)
        if self.oleada >= 3:
            tipos.append(TanquePesado)
        self.cola_enemigos = [random.choice(tipos) for _ in range(cantidad)]
        if self.oleada % 5 == 0:
            self.cola_enemigos.append(TanquePesado)   # cada 5 oleadas, un pesado extra
        self.tiempo_cartel = 2.5

    def _aparecer_enemigo(self):
        if not self.cola_enemigos:
            return
        libres = []
        for punto in self.puntos_aparicion:
            zona = pygame.Rect(0, 0, 60, 60)
            zona.center = punto
            ocupado = any(zona.colliderect(t.rect) for t in self.enemigos + [self.jugador])
            if not ocupado:
                libres.append(punto)
        if libres:
            clase = self.cola_enemigos.pop(0)
            self.enemigos.append(clase(*random.choice(libres), self.recursos))

    # --- Bucle principal ---
    def ejecutar(self):
        while True:
            dt = min(self.reloj.tick(FPS) / 1000, 0.05)
            self.procesar_eventos()
            if self.estado == "jugando":
                self.actualizar(dt)
            elif self.estado == "game_over":
                for explosion in self.explosiones:   # la última explosión termina de animarse
                    explosion.actualizar(dt)
            self.dibujar()
            pygame.display.update()

    def procesar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.salir()

            elif evento.type == EVENTO_APARICION and self.estado == "jugando":
                self._aparecer_enemigo()

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_m:
                    self.alternar_musica()
                elif self.estado == "menu":
                    if evento.key == pygame.K_ESCAPE:
                        self.salir()
                    elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.nueva_partida()
                        self.estado = "jugando"
                elif self.estado == "jugando":
                    if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.estado = "pausa"
                        if self.hay_audio:
                            pygame.mixer.music.pause()
                elif self.estado == "pausa":
                    if evento.key in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
                        self.estado = "jugando"
                        if self.hay_audio:
                            pygame.mixer.music.unpause()
                    elif evento.key == pygame.K_q:
                        self.estado = "menu"
                        if self.hay_audio:
                            pygame.mixer.music.unpause()
                elif self.estado == "game_over":
                    if evento.key in (pygame.K_r, pygame.K_RETURN):
                        self.nueva_partida()
                        self.estado = "jugando"
                    elif evento.key == pygame.K_ESCAPE:
                        self.estado = "menu"

            elif evento.type == pygame.MOUSEBUTTONDOWN and self.estado == "menu":
                self.nueva_partida()
                self.estado = "jugando"

        pygame.mouse.set_visible(self.estado != "jugando")

    def alternar_musica(self):
        if not self.hay_audio:
            return
        self.musica_activa = not self.musica_activa
        pygame.mixer.music.set_volume(0.3 if self.musica_activa else 0)

    # --- Lógica del juego ---
    def actualizar(self, dt):
        self.tiempo_partida += dt
        self.temblor = max(0, self.temblor - dt)
        self.tiempo_cartel = max(0, self.tiempo_cartel - dt)
        todos_tanques = [self.jugador] + self.enemigos

        # Jugador
        teclas = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        self.jugador.actualizar(dt, teclas, (mx, my - ALTO_HUD), self.obstaculos, todos_tanques)
        quiere_disparar = teclas[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]
        if quiere_disparar and self.jugador.puede_disparar():
            self.balas += self.jugador.disparar(self.recursos)
            self.recursos.snd_disparo.play()

        # Enemigos (polimorfismo: cada tipo se mueve y dispara a su manera)
        for enemigo in self.enemigos:
            enemigo.actualizar(dt, self.jugador, self.obstaculos, todos_tanques)
            if enemigo.puede_disparar() and enemigo.ve_al_jugador(self.jugador, self.obstaculos):
                self.balas += enemigo.disparar(self.recursos)
                self.recursos.snd_disparo.play()

        # Balas
        for bala in self.balas:
            bala.actualizar(dt)
            self._comprobar_colisiones_bala(bala)
        self._balas_contra_balas()
        self.balas = [b for b in self.balas if b.activa]

        # Barricadas destruidas
        for obstaculo in self.obstaculos:
            if obstaculo.destruido:
                self.explosiones.append(Explosion(*obstaculo.rect.center, self.recursos.explosion, 0.7))
                self.recursos.snd_explosion.play()
        self.obstaculos = [o for o in self.obstaculos if not o.destruido]

        # Enemigos destruidos
        for enemigo in self.enemigos:
            if not enemigo.esta_vivo:
                self.puntos += enemigo.PUNTOS
                self.explosiones.append(Explosion(*enemigo.rect.center, self.recursos.explosion,
                                                  1.3 if isinstance(enemigo, TanquePesado) else 1.0))
                self.recursos.snd_explosion.play()
                self.temblor = 0.25
                if random.random() < 0.25:
                    self.botiquines.append(Botiquin(*enemigo.rect.center, self.recursos.botiquin))
        self.enemigos = [e for e in self.enemigos if e.esta_vivo]

        # Botiquines
        for botiquin in self.botiquines:
            botiquin.actualizar(dt)
            if botiquin.rect.colliderect(self.jugador.rect):
                self.jugador.curar(Botiquin.CURACION)
                self.recursos.snd_recoger.play()
                botiquin.tiempo = Botiquin.DURACION
        self.botiquines = [b for b in self.botiquines if not b.caducado]

        # Explosiones
        for explosion in self.explosiones:
            explosion.actualizar(dt)
        self.explosiones = [e for e in self.explosiones if not e.terminada]

        # Oleadas
        if not self.enemigos and not self.cola_enemigos:
            self.espera_oleada -= dt
            if self.espera_oleada <= 0:
                self._preparar_oleada()
                self.espera_oleada = 3

        # Derrota
        if not self.jugador.esta_vivo:
            self.explosiones.append(Explosion(*self.jugador.rect.center, self.recursos.explosion, 1.5))
            self.recursos.snd_explosion.play()
            self.recursos.snd_game_over.play()
            self._guardar_record()
            self.estado = "game_over"

    def _comprobar_colisiones_bala(self, bala):
        for obstaculo in self.obstaculos:
            if bala.rect.colliderect(obstaculo.rect):
                obstaculo.recibir_impacto(bala.danio)
                self._impacto(bala)
                return
        if bala.del_jugador:
            for enemigo in self.enemigos:
                if bala.rect.colliderect(enemigo.rect):
                    enemigo.recibir_danio(bala.danio)
                    self._impacto(bala)
                    return
        elif bala.rect.colliderect(self.jugador.rect):
            self.jugador.recibir_danio(bala.danio)
            self.temblor = 0.15
            self._impacto(bala)

    def _impacto(self, bala):
        bala.activa = False
        self.explosiones.append(Explosion(bala.x, bala.y, self.recursos.explosion, 0.35))
        self.recursos.snd_impacto.play()

    def _balas_contra_balas(self):
        """Las balas del jugador pueden destruir las balas enemigas."""
        balas_jugador = [b for b in self.balas if b.del_jugador and b.activa]
        balas_enemigas = [b for b in self.balas if not b.del_jugador and b.activa]
        for propia in balas_jugador:
            for enemiga in balas_enemigas:
                if enemiga.activa and propia.rect.colliderect(enemiga.rect):
                    self._impacto(propia)
                    self._impacto(enemiga)
                    break

    # --- Dibujo ---
    def dibujar(self):
        self.pantalla.fill(NEGRO)
        self.dibujar_mundo()
        desplazamiento = (0, 0)
        if self.temblor > 0:
            fuerza = int(self.temblor * 30)
            desplazamiento = (random.randint(-fuerza, fuerza), random.randint(-fuerza, fuerza))
        self.pantalla.blit(self.mundo, (desplazamiento[0], ALTO_HUD + desplazamiento[1]))
        self.dibujar_hud()

        if self.estado == "menu":
            self.dibujar_menu()
        elif self.estado == "pausa":
            self.dibujar_capa("PAUSA", ["P / ESC para continuar", "Q para volver al menú"])
        elif self.estado == "game_over":
            nuevo = " ¡NUEVO RÉCORD!" if self.puntos >= self.record and self.puntos > 0 else ""
            self.dibujar_capa("GAME OVER", [f"Puntos: {self.puntos}{nuevo}",
                                            f"Llegaste a la oleada {self.oleada}",
                                            "R / ENTER para jugar otra vez", "ESC para ir al menú"])
        elif self.estado == "jugando":
            mx, my = pygame.mouse.get_pos()
            self.pantalla.blit(self.recursos.mira, self.recursos.mira.get_rect(center=(mx, my)))

    def dibujar_mundo(self):
        self.mundo.blit(self.fondo, (0, 0))
        for obstaculo in self.obstaculos:
            obstaculo.dibujar(self.mundo)
        for botiquin in self.botiquines:
            botiquin.dibujar(self.mundo)
        if self.jugador.esta_vivo:
            self.jugador.dibujar(self.mundo)
        for enemigo in self.enemigos:
            enemigo.dibujar(self.mundo)
            enemigo.dibujar_barra_vida(self.mundo)
        for bala in self.balas:
            bala.dibujar(self.mundo)
        for explosion in self.explosiones:
            explosion.dibujar(self.mundo)

        if self.tiempo_cartel > 0 and self.estado == "jugando":
            self.texto_centrado(self.mundo, f"OLEADA {self.oleada}", self.fuente_grande, AMARILLO,
                                self.mundo.get_height() // 2 - 40, sombra=True)

    def dibujar_hud(self):
        pygame.draw.rect(self.pantalla, FONDO_HUD, (0, 0, ANCHO, ALTO_HUD))
        pygame.draw.line(self.pantalla, (70, 80, 70), (0, ALTO_HUD - 1), (ANCHO, ALTO_HUD - 1), 2)

        # Barra de vida del jugador
        self.pantalla.blit(self.fuente.render("VIDA", True, BLANCO), (16, 14))
        proporcion = self.jugador.vida / self.jugador.vida_maxima
        pygame.draw.rect(self.pantalla, (60, 20, 20), (80, 14, 200, 20), border_radius=4)
        color = VERDE if proporcion > 0.5 else AMARILLO if proporcion > 0.25 else ROJO
        pygame.draw.rect(self.pantalla, color, (80, 14, 200 * proporcion, 20), border_radius=4)
        pygame.draw.rect(self.pantalla, BLANCO, (80, 14, 200, 20), 2, border_radius=4)

        textos = [f"PUNTOS: {self.puntos}", f"OLEADA: {self.oleada}",
                  f"ENEMIGOS: {len(self.enemigos) + len(self.cola_enemigos)}"]
        x = 305
        for texto in textos:
            superficie = self.fuente_hud.render(texto, True, BLANCO)
            self.pantalla.blit(superficie, (x, 16))
            x += superficie.get_width() + 28
        record = self.fuente_hud.render(f"RÉCORD: {self.record}", True, AMARILLO)
        self.pantalla.blit(record, record.get_rect(topright=(ANCHO - 16, 16)))

    def texto_centrado(self, superficie, texto, fuente, color, y, sombra=False):
        if sombra:
            s = fuente.render(texto, True, NEGRO)
            superficie.blit(s, s.get_rect(center=(superficie.get_width() // 2 + 3, y + 3)))
        s = fuente.render(texto, True, color)
        superficie.blit(s, s.get_rect(center=(superficie.get_width() // 2, y)))

    def dibujar_capa(self, titulo, lineas):
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 160))
        self.pantalla.blit(capa, (0, 0))
        self.texto_centrado(self.pantalla, titulo, self.fuente_titulo, AMARILLO, ALTO // 2 - 90, sombra=True)
        for i, linea in enumerate(lineas):
            self.texto_centrado(self.pantalla, linea, self.fuente, BLANCO, ALTO // 2 + i * 38)

    def dibujar_menu(self):
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 175))
        self.pantalla.blit(capa, (0, 0))
        self.texto_centrado(self.pantalla, "BATALLA DE TANQUES", self.fuente_titulo, AMARILLO, 150, sombra=True)

        # Muestra los tipos de enemigo con sus sprites
        tipos = [("jugador", "Tú", "WASD + ratón"), ("enemigo", "Normal", "100 pts"),
                 ("rapido", "Rápido", "150 pts"), ("pesado", "Pesado", "300 pts")]
        for i, (tipo, nombre, info) in enumerate(tipos):
            x = ANCHO // 2 + (i - 1.5) * 170
            cuerpo, canon = self.recursos.tanques[tipo]
            self.pantalla.blit(cuerpo, cuerpo.get_rect(center=(x, 300)))
            self.pantalla.blit(canon, canon.get_rect(center=(x, 300)))
            for j, (t, color) in enumerate(((nombre, BLANCO), (info, GRIS))):
                s = self.fuente_peque.render(t, True, color)
                self.pantalla.blit(s, s.get_rect(center=(x, 352 + j * 22)))

        controles = ["WASD: mover    Ratón: apuntar    Clic / ESPACIO: disparar",
                     "Las barricadas de madera se rompen, los muros de piedra no",
                     "P: pausa    M: música on/off"]
        for i, linea in enumerate(controles):
            self.texto_centrado(self.pantalla, linea, self.fuente_peque, BLANCO, 450 + i * 28)
        if int(pygame.time.get_ticks() / 500) % 2 == 0:
            self.texto_centrado(self.pantalla, "Pulsa ENTER para empezar", self.fuente, AMARILLO, 580)
        self.texto_centrado(self.pantalla, f"Récord: {self.record}", self.fuente_peque, GRIS, 630)

    def salir(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Juego().ejecutar()
