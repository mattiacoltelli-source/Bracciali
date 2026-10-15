"""Camere usate per i bake: tutte tranne quelle nel corridoio (z < 0): da fuori vedrebbero i muri attraverso la parete TV."""
def select(fr, extra_excl=()):
    return [n for n in sorted(fr.cams) if fr.cams[n]['C'][2] > 0.0 and n not in extra_excl]
