import webbrowser

SITIOS = {
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "linkedin": "https://www.linkedin.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "netflix": "https://www.netflix.com",
    "twitch": "https://www.twitch.tv",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "amazon": "https://www.amazon.com",
    "mercado libre": "https://www.mercadolibre.com",
    "google maps": "https://www.google.com/maps",
    "drive": "https://drive.google.com",
}


def abrir_sitio(nombre):
    nombre_clean = nombre.lower().strip()
    for key, url in SITIOS.items():
        if key in nombre_clean or nombre_clean in key:
            webbrowser.open(url)
            return f"Abrí {key}"
    return None


def buscar_google(consulta):
    url = f"https://www.google.com/search?q={consulta.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Busqué {consulta} en Google"
