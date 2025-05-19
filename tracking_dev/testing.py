import cv2
import numpy as np
import os
import sys
import glob
from analysis import analysis

def test_single_image(image_path):
    """
    Teste la fonction analysis sur une seule image
    
    Args:
        image_path (str): Chemin vers l'image à tester
        
    Returns:
        None: Sauvegarde l'image résultante dans le dossier 'test_results'
    """
    # Vérifier si l'image existe
    if not os.path.exists(image_path):
        print(f"Erreur: L'image {image_path} n'existe pas")
        return
    
    # Créer le dossier de résultats s'il n'existe pas
    if not os.path.exists('test_results'):
        os.makedirs('test_results')
    
    # Charger l'image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Erreur: Impossible de charger l'image {image_path}")
        return
    
    # Appliquer l'analyse
    result_frame, detected_balls,  = analysis(frame)
    
    # Afficher les résultats
    print(f"Image: {image_path}")
    print(f"Balles rouges détectées: {len(detected_balls['red'])}")
    print(f"Positions balles rouges: {detected_balls['red']}")
    print(f"Balles bleues détectées: {len(detected_balls['blue'])}")
    print(f"Positions balles bleues: {detected_balls['blue']}")
    
    # Sauvegarder l'image résultante
    base_name = os.path.basename(image_path)
    result_path = os.path.join('test_results', f"result_{base_name}")
    cv2.imwrite(result_path, result_frame)
    print(f"Image résultante sauvegardée: {result_path}")
    
    return result_frame, detected_balls

def test_multiple_images(folder_path, extensions=['jpg', 'jpeg', 'png']):
    """
    Teste la fonction analysis sur toutes les images d'un dossier
    
    Args:
        folder_path (str): Chemin vers le dossier contenant les images
        extensions (list): Liste des extensions de fichiers à considérer
        
    Returns:
        None: Sauvegarde les images résultantes dans le dossier 'test_results'
    """
    # Vérifier si le dossier existe
    if not os.path.exists(folder_path):
        print(f"Erreur: Le dossier {folder_path} n'existe pas")
        return
    
    # Trouver toutes les images dans le dossier
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(folder_path, f"*.{ext}")))
    
    if not image_paths:
        print(f"Aucune image trouvée dans {folder_path}")
        return
    
    # Traiter chaque image
    for image_path in image_paths:
        test_single_image(image_path)

def show_results_interactive(image_path):
    """
    Affiche l'image originale et l'image résultante côte à côte
    
    Args:
        image_path (str): Chemin vers l'image à tester
        
    Returns:
        None
    """
    # Charger l'image
    original = cv2.imread(image_path)
    if original is None:
        print(f"Erreur: Impossible de charger l'image {image_path}")
        return
    
    # Appliquer l'analyse
    result_frame, detected_balls = analysis(original)
    
    # Redimensionner les images si elles sont trop grandes
    max_height = 800
    scale = min(1.0, max_height / original.shape[0])
    if scale < 1.0:
        width = int(original.shape[1] * scale)
        height = int(original.shape[0] * scale)
        original = cv2.resize(original, (width, height))
        result_frame = cv2.resize(result_frame, (width, height))
    
    # Afficher les images côte à côte
    combined = np.hstack((original, result_frame))
    cv2.imshow("Original | Résultat", combined)
    print("Appuyez sur 'q' pour quitter")
    
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python testing.py image.jpg              # Tester une seule image")
        print("  python testing.py --folder images/       # Tester toutes les images d'un dossier")
        print("  python testing.py --interactive image.jpg # Afficher résultat interactif")
        sys.exit(1)
    
    if sys.argv[1] == "--folder":
        if len(sys.argv) < 3:
            print("Erreur: Spécifiez un dossier")
            sys.exit(1)
        test_multiple_images(sys.argv[2])
    elif sys.argv[1] == "--interactive":
        if len(sys.argv) < 3:
            print("Erreur: Spécifiez une image")
            sys.exit(1)
        show_results_interactive(sys.argv[2])
    else:
        test_single_image(sys.argv[1])