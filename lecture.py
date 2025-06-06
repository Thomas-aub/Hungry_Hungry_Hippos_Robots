import re 
# "pseudo-code" lire un fichier et recuperer les distances et angles
def read_fichier(fichier):
    points = []

    with open(fichier, "r", encoding="utf-8") as f:
        for ligne in f:
            distances = re.search(r"point\s*:\s*(\d+)", ligne, re.IGNORECASE)
            angles = re.search(r"point\s*:\s*(\d+)", ligne, re.IGNORECASE)
            if distances and angles:
                distance = int(distances.group(1))
                angle = int(angles.group(1))
                points.append(distance, angle)

    print("Points récupérés :", points)
    return points