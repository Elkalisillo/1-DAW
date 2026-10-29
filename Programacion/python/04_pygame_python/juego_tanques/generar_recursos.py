"""
Genera todos los sprites (PNG) y sonidos (WAV) del juego de tanques.

Solo hace falta ejecutarlo una vez (o si quieres cambiar el aspecto):
    python3 generar_recursos.py

Las imágenes se guardan en la carpeta "imagenes" y los sonidos en "sonidos",
siguiendo la buena práctica del temario de tener carpetas para los recursos.
"""
import math
import os
import random
import struct
import wave

os.environ["SDL_VIDEODRIVER"] = "dummy"  # no necesitamos abrir ventana
import pygame

CARPETA = os.path.dirname(os.path.abspath(__file__))
CARPETA_IMAGENES = os.path.join(CARPETA, "imagenes")
CARPETA_SONIDOS = os.path.join(CARPETA, "sonidos")

pygame.init()
random.seed(7)


def oscurecer(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def guardar(superficie, nombre):
    pygame.image.save(superficie, os.path.join(CARPETA_IMAGENES, nombre))


# ---------------------------------------------------------------------------
# TANQUES (todos miran hacia ARRIBA; en el juego se rotan)
# ---------------------------------------------------------------------------
def crear_cuerpo_tanque(tam, color):
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    oruga = max(8, tam // 5)
    margen = tam // 14
    alto = tam - margen * 2
    # Orugas
    for x in (margen, tam - margen - oruga):
        pygame.draw.rect(s, (35, 35, 35), (x, margen, oruga, alto), border_radius=4)
        for y in range(margen + 3, margen + alto - 2, 5):
            pygame.draw.line(s, (80, 80, 80), (x + 1, y), (x + oruga - 2, y), 2)
        pygame.draw.rect(s, (15, 15, 15), (x, margen, oruga, alto), 1, border_radius=4)
    # Casco
    casco = pygame.Rect(margen + oruga - 2, margen + 4, tam - 2 * (margen + oruga) + 4, alto - 8)
    pygame.draw.rect(s, oscurecer(color, 0.6), casco, border_radius=6)
    pygame.draw.rect(s, color, casco.inflate(-6, -6), border_radius=5)
    # Detalles: escotilla trasera y luces
    pygame.draw.rect(s, oscurecer(color, 0.75), (casco.x + 6, casco.bottom - 10, casco.w - 12, 5), border_radius=2)
    pygame.draw.circle(s, (255, 230, 120), (casco.x + 6, casco.y + 6), 2)
    pygame.draw.circle(s, (255, 230, 120), (casco.right - 7, casco.y + 6), 2)
    return s


def crear_canon_tanque(tam, color, grosor_canon):
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    c = tam // 2
    largo = int(tam * 0.48)
    # Cañón
    canon = pygame.Rect(c - grosor_canon // 2, c - largo, grosor_canon, largo)
    pygame.draw.rect(s, oscurecer(color, 0.45), canon, border_radius=2)
    pygame.draw.rect(s, oscurecer(color, 0.8), canon.inflate(-2, -2), border_radius=2)
    pygame.draw.rect(s, (30, 30, 30), (canon.x - 1, canon.y, canon.w + 2, 5), border_radius=1)
    # Torreta
    radio = tam // 5
    pygame.draw.circle(s, oscurecer(color, 0.5), (c, c), radio + 2)
    pygame.draw.circle(s, oscurecer(color, 0.9), (c, c), radio)
    pygame.draw.circle(s, oscurecer(color, 1.2), (c - 2, c - 2), radio // 2)
    pygame.draw.circle(s, oscurecer(color, 0.5), (c, c), radio // 3)
    return s


TANQUES = {
    "jugador": (56, (70, 160, 70), 8),
    "enemigo": (56, (190, 60, 50), 8),
    "rapido": (48, (225, 170, 40), 6),
    "pesado": (70, (110, 90, 150), 12),
}


# ---------------------------------------------------------------------------
# BALAS
# ---------------------------------------------------------------------------
def crear_bala(color, ancho, alto):
    s = pygame.Surface((ancho + 4, alto + 4), pygame.SRCALPHA)
    brillo = pygame.Surface((ancho + 4, alto + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(brillo, (*color, 90), brillo.get_rect())
    s.blit(brillo, (0, 0))
    cuerpo = pygame.Rect(2, 2, ancho, alto)
    pygame.draw.ellipse(s, color, cuerpo)
    pygame.draw.ellipse(s, (255, 255, 230), cuerpo.inflate(-ancho // 2, -alto // 2))
    return s


# ---------------------------------------------------------------------------
# ESCENARIO
# ---------------------------------------------------------------------------
def crear_muro(tam):
    s = pygame.Surface((tam, tam))
    s.fill((70, 70, 78))
    fila = tam // 4
    for i in range(4):
        desplazamiento = 0 if i % 2 == 0 else tam // 4
        for x in range(-tam // 4 + desplazamiento, tam, tam // 2):
            ladrillo = pygame.Rect(x + 1, i * fila + 1, tam // 2 - 2, fila - 2)
            tono = random.randint(-12, 12)
            pygame.draw.rect(s, (125 + tono, 125 + tono, 135 + tono), ladrillo)
            pygame.draw.line(s, (165, 165, 175), ladrillo.topleft, ladrillo.topright)
    pygame.draw.rect(s, (40, 40, 45), s.get_rect(), 2)
    return s


def crear_barricada(tam, danio):
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    caja = pygame.Rect(3, 3, tam - 6, tam - 6)
    pygame.draw.rect(s, (110, 70, 35), caja)
    for y in range(caja.y, caja.bottom, 9):
        pygame.draw.line(s, (85, 52, 25), (caja.x, y), (caja.right - 1, y), 1)
    pygame.draw.rect(s, (70, 42, 20), caja, 4)
    pygame.draw.line(s, (70, 42, 20), caja.topleft, caja.bottomright, 5)
    pygame.draw.line(s, (70, 42, 20), caja.topright, caja.bottomleft, 5)
    # Grietas según el daño
    for _ in range(danio * 4):
        x = random.randint(caja.x + 4, caja.right - 4)
        y = random.randint(caja.y + 4, caja.bottom - 4)
        pygame.draw.line(s, (35, 20, 10), (x, y),
                         (x + random.randint(-9, 9), y + random.randint(-9, 9)), 2)
    if danio >= 2:
        pygame.draw.polygon(s, (0, 0, 0, 0), [(caja.right, caja.y), (caja.right - 14, caja.y),
                                              (caja.right, caja.y + 16)])
    return s


def crear_suelo(tam):
    s = pygame.Surface((tam, tam))
    s.fill((92, 112, 62))
    for _ in range(70):
        x, y = random.randint(0, tam - 1), random.randint(0, tam - 1)
        tono = random.randint(-18, 18)
        s.set_at((x, y), (92 + tono, 112 + tono, 62 + tono // 2))
    for _ in range(6):
        x, y = random.randint(2, tam - 3), random.randint(2, tam - 3)
        pygame.draw.line(s, (70, 95, 45), (x, y), (x + random.randint(-2, 2), y - 4), 1)
    return s


def crear_suelo_tierra(tam):
    s = pygame.Surface((tam, tam))
    s.fill((120, 98, 66))
    for _ in range(60):
        x, y = random.randint(0, tam - 1), random.randint(0, tam - 1)
        tono = random.randint(-20, 20)
        s.set_at((x, y), (120 + tono, 98 + tono, 66 + tono))
    for _ in range(4):
        pygame.draw.circle(s, (100, 82, 55), (random.randint(4, tam - 4), random.randint(4, tam - 4)), 2)
    return s


# ---------------------------------------------------------------------------
# EFECTOS Y OBJETOS
# ---------------------------------------------------------------------------
def crear_explosion(fotograma, total, tam):
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    c = tam // 2
    progreso = fotograma / (total - 1)
    radio = int(tam * 0.18 + tam * 0.3 * progreso)
    alfa = int(255 * (1 - progreso) ** 0.7)
    colores = [(255, 240, 160), (255, 170, 40), (220, 70, 20), (70, 60, 55)]
    rnd = random.Random(fotograma)
    for i, color in enumerate(reversed(colores)):
        r = int(radio * (1 - i * 0.22))
        if r <= 0:
            continue
        for _ in range(7):
            ox = rnd.randint(-radio // 3, radio // 3)
            oy = rnd.randint(-radio // 3, radio // 3)
            pygame.draw.circle(s, (*color, alfa), (c + ox, c + oy), max(2, r // 2 + rnd.randint(0, r // 3)))
    # Chispas
    for _ in range(10):
        ang = rnd.uniform(0, math.tau)
        dist = radio * (0.8 + progreso)
        x = c + math.cos(ang) * dist
        y = c + math.sin(ang) * dist
        pygame.draw.circle(s, (255, 220, 120, alfa), (int(x), int(y)), 2)
    return s


def crear_botiquin(tam):
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    pygame.draw.rect(s, (245, 245, 245), (2, 4, tam - 4, tam - 6), border_radius=5)
    pygame.draw.rect(s, (150, 150, 150), (2, 4, tam - 4, tam - 6), 2, border_radius=5)
    pygame.draw.rect(s, (120, 120, 120), (tam // 2 - 5, 0, 10, 6), 2, border_radius=2)
    g = tam // 6
    pygame.draw.rect(s, (220, 40, 40), (tam // 2 - g // 2, 9, g, tam - 16))
    pygame.draw.rect(s, (220, 40, 40), (7, tam // 2 - g // 2 + 2, tam - 14, g))
    return s


def crear_mira(tam):
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    c = tam // 2
    pygame.draw.circle(s, (255, 255, 255), (c, c), c - 3, 2)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pygame.draw.line(s, (255, 255, 255), (c + dx * 4, c + dy * 4), (c + dx * (c - 1), c + dy * (c - 1)), 2)
    pygame.draw.circle(s, (255, 60, 60), (c, c), 2)
    return s


# ---------------------------------------------------------------------------
# SONIDOS (se sintetizan con matemáticas y se guardan en WAV)
# ---------------------------------------------------------------------------
FRECUENCIA = 22050


def guardar_wav(nombre, muestras):
    with wave.open(os.path.join(CARPETA_SONIDOS, nombre), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(FRECUENCIA)
        datos = b"".join(struct.pack("<h", int(max(-1, min(1, m)) * 32000)) for m in muestras)
        f.writeframes(datos)


def sonido_disparo():
    n = int(FRECUENCIA * 0.18)
    rnd = random.Random(1)
    res = []
    for i in range(n):
        t = i / n
        env = (1 - t) ** 3
        frec = 220 - 160 * t
        tono = math.sin(2 * math.pi * frec * i / FRECUENCIA)
        res.append((tono * 0.6 + rnd.uniform(-1, 1) * 0.5) * env * 0.8)
    return res


def sonido_explosion():
    n = int(FRECUENCIA * 0.7)
    rnd = random.Random(2)
    res, filtrado = [], 0.0
    for i in range(n):
        t = i / n
        env = (1 - t) ** 2
        filtrado += (rnd.uniform(-1, 1) - filtrado) * (0.25 - 0.2 * t)
        grave = math.sin(2 * math.pi * (60 - 30 * t) * i / FRECUENCIA)
        res.append((filtrado * 2.2 + grave * 0.5) * env)
    return res


def sonido_impacto():
    n = int(FRECUENCIA * 0.1)
    rnd = random.Random(3)
    return [(rnd.uniform(-1, 1) * 0.4 + math.sin(i * 0.25) * 0.3) * (1 - i / n) ** 2 for i in range(n)]


def sonido_recoger():
    res = []
    for frec in (523, 659, 784, 1046):
        n = int(FRECUENCIA * 0.07)
        for i in range(n):
            onda = 1 if math.sin(2 * math.pi * frec * i / FRECUENCIA) > 0 else -1
            res.append(onda * 0.25 * (1 - i / n * 0.5))
    return res


def sonido_game_over():
    res = []
    for frec in (392, 330, 262, 196):
        n = int(FRECUENCIA * 0.28)
        for i in range(n):
            onda = 1 if math.sin(2 * math.pi * frec * i / FRECUENCIA) > 0 else -1
            res.append(onda * 0.22 * (1 - i / n))
    return res


def musica_fondo():
    """Bucle de 8 compases tipo 'chiptune' militar a 120 bpm."""
    negra = int(FRECUENCIA * 0.25)
    bajos = [110, 110, 131, 98] * 2           # La, La, Do, Sol
    melodia = [440, 0, 523, 494, 440, 0, 392, 0,
               440, 0, 523, 587, 659, 0, 587, 523]
    res = []
    paso = 0
    for compas in range(8):
        for golpe in range(8):  # corcheas
            frec_bajo = bajos[compas]
            frec_mel = melodia[paso % len(melodia)]
            paso += 1
            for i in range(negra // 2):
                t = i / (negra // 2)
                bajo = (1 if math.sin(2 * math.pi * frec_bajo * i / FRECUENCIA) > 0 else -1) * 0.18 * (1 - t * 0.6)
                mel = 0
                if frec_mel and compas % 2 == 1:
                    mel = (2 * abs(2 * ((frec_mel * i / FRECUENCIA) % 1) - 1) - 1) * 0.15 * (1 - t)
                caja = 0
                if golpe in (2, 6) and t < 0.3:
                    caja = random.uniform(-1, 1) * 0.2 * (1 - t / 0.3)
                res.append(bajo + mel + caja)
    return res


def main():
    os.makedirs(CARPETA_IMAGENES, exist_ok=True)
    os.makedirs(CARPETA_SONIDOS, exist_ok=True)

    for nombre, (tam, color, grosor) in TANQUES.items():
        guardar(crear_cuerpo_tanque(tam, color), f"tanque_{nombre}_cuerpo.png")
        guardar(crear_canon_tanque(tam, color, grosor), f"tanque_{nombre}_canon.png")

    guardar(crear_bala((120, 230, 255), 8, 16), "bala_jugador.png")
    guardar(crear_bala((255, 120, 60), 8, 16), "bala_enemigo.png")
    guardar(crear_bala((220, 120, 255), 12, 22), "bala_pesada.png")

    guardar(crear_muro(48), "muro.png")
    for danio in range(3):
        guardar(crear_barricada(48, danio), f"barricada_{danio}.png")
    guardar(crear_suelo(48), "suelo_hierba.png")
    guardar(crear_suelo_tierra(48), "suelo_tierra.png")

    for i in range(8):
        guardar(crear_explosion(i, 8, 96), f"explosion_{i}.png")
    guardar(crear_botiquin(32), "botiquin.png")
    guardar(crear_mira(28), "mira.png")

    guardar_wav("disparo.wav", sonido_disparo())
    guardar_wav("explosion.wav", sonido_explosion())
    guardar_wav("impacto.wav", sonido_impacto())
    guardar_wav("recoger.wav", sonido_recoger())
    guardar_wav("game_over.wav", sonido_game_over())
    guardar_wav("musica.wav", musica_fondo())
    print("Recursos generados en 'imagenes' y 'sonidos'.")


if __name__ == "__main__":
    main()
    pygame.quit()
