from datetime import datetime
import pytz

tz = pytz.timezone("America/Argentina/Buenos_Aires")

STOIC_QUOTES = [
    {"author": "Marco Aurelio", "work": "Meditaciones", "text": "Al amanecer, dite a ti mismo: hoy me toparé con indiscretos, ingratos e insolentes. Pero nada de eso puede dañarme ni apartarme de lo correcto."},
    {"author": "Séneca", "work": "Cartas a Lucilio", "text": "No nos atrevemos a muchas cosas porque son difíciles; son difíciles porque no nos atrevemos."},
    {"author": "Epicteto", "work": "Enquiridión", "text": "No son las cosas las que atormentan a los hombres, sino los principios y las opiniones que los hombres se forman de ellas."},
    {"author": "Marco Aurelio", "work": "Meditaciones", "text": "No pierdas más tiempo discutiendo lo que debe ser un hombre bueno; sé uno de ellos."},
    {"author": "Séneca", "work": "De la brevedad de la vida", "text": "No tenemos poco tiempo, sino que perdemos mucho. La vida es suficientemente larga si se invierte bien."},
    {"author": "Epicteto", "work": "Disertaciones", "text": "Primero dite a ti mismo qué quieres ser; y luego haz lo que tengas que hacer."},
    {"author": "Marco Aurelio", "work": "Meditaciones", "text": "La mejor venganza es no ser como tu enemigo."}
]

BIBLE_VERSES = [
    {"ref": "Salmos 37:5", "text": "Encomienda al Señor tu camino; confía en Él, y Él actuará."},
    {"ref": "Proverbios 16:3", "text": "Pon en manos del Señor tus obras, y tus proyectos se cumplirán."},
    {"ref": "Filipenses 4:13", "text": "Todo lo puedo en Cristo que me fortalece."},
    {"ref": "Josué 1:9", "text": "Mira que te mando que te esfuerces y seas valiente; no temas ni desmayes, porque el Señor tu Dios estará contigo."},
    {"ref": "Romanos 12:2", "text": "No os conforméis a este siglo, sino transformaos por medio de la renovación de vuestro entendimiento."},
    {"ref": "Proverbios 27:17", "text": "Hierro con hierro se afila; y así el hombre aguza el rostro de su amigo."},
    {"ref": "Colosenses 3:23", "text": "Y todo lo que hagáis, hacedlo de corazón, como para el Señor y no para los hombres."}
]

def get_daily_wisdom():
    day_of_year = datetime.now(tz).timetuple().tm_yday
    quote = STOIC_QUOTES[day_of_year % len(STOIC_QUOTES)]
    verse = BIBLE_VERSES[day_of_year % len(BIBLE_VERSES)]
    return quote, verse