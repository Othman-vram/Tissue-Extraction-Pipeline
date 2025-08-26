# Pipeline d'Extraction de Tissus Unifié

Un pipeline Python complet qui combine la conversion SVS, la génération de masques et l'extraction de tissus en un seul flux de travail automatisé.

## 🔬 Aperçu

Ce pipeline ne nécessite que deux entrées :
1. Un fichier `.svs` (image de lame entière)
2. Un fichier `.geojson` (annotations/masque de tissus)

Et produit un seul fichier **TIFF RGBA** avec les régions de tissus extraites et un arrière-plan transparent.

## 🚀 Étapes du Pipeline

1. **SVS → TIFF Pyramidal** : Convertit le fichier SVS d'entrée au format TIFF pyramidal
2. **Génération de Masque** : Crée un masque binaire pyramidal à partir des annotations GeoJSON
3. **Extraction de Tissus** : Extrait les régions de tissus en RGBA avec arrière-plan transparent

## 📦 Installation

### Option 1 : Conda (Recommandé)

```bash
# Créer et activer l'environnement
conda env create -f environment.yml
conda activate tissue-extraction-pipeline
```

### Option 2 : Pip

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Installer les dépendances système (Ubuntu/Debian)
sudo apt-get install libvips-dev openslide-tools

# Installer les dépendances système (macOS)
brew install vips openslide
```

### Option 3 : Docker

```bash
# Télécharger depuis Docker Hub
docker pull votre-username/tissue-extraction-pipeline

# Ou construire localement
docker build -t tissue-extraction-pipeline .
```

## 🎯 Utilisation

### Utilisation de Base

```bash
python unified_tissue_pipeline.py input.svs annotations.geojson output_tissue.tiff
```

### Utilisation Avancée

```bash
# Spécifier le répertoire temporaire et la compression
python unified_tissue_pipeline.py \
    tissue.svs \
    mask.geojson \
    extracted_tissue.tiff \
    --temp-dir ./temp \
    --compression lzw

# Nettoyer automatiquement les fichiers intermédiaires
python unified_tissue_pipeline.py \
    tissue.svs \
    mask.geojson \
    output.tiff \
    --no-keep-intermediates
```

### Utilisation avec Docker

```bash
# Utiliser l'image Docker Hub
docker run -v /chemin/vers/donnees:/app/input \
           -v /chemin/vers/sortie:/app/output \
           votre-username/tissue-extraction-pipeline \
           /app/input/tissue.svs \
           /app/input/mask.geojson \
           /app/output/result.tiff

# Ou avec docker-compose
docker-compose up
```

### Options de Ligne de Commande

- `--temp-dir <chemin>` : Répertoire pour les fichiers intermédiaires (défaut : temp système)
- `--no-keep-intermediates` : Supprimer les fichiers intermédiaires après completion
- `--compression <type>` : Type de compression de sortie (défaut : lzw)

## 📁 Fichiers de Sortie

### Sortie Finale
- **TIFF RGBA** : TIFF pyramidal avec tissus extraits
  - Régions de tissus : Opaques (alpha = 255)
  - Arrière-plan : Transparent (alpha = 0)
  - Préserve la structure pyramidale originale

### Fichiers Intermédiaires (pour débogage)
- `tissue_pyramidal.tiff` : SVS converti en TIFF pyramidal
- `mask_pyramidal.tiff` : Masque pyramidal généré

## 🎨 Fonctionnalités

- **Suivi de Progression** : Barres de progression en temps réel avec informations de timing
- **Sortie Console Enrichie** : Interface terminal belle avec mises à jour de statut
- **Gestion d'Erreurs** : Validation complète et rapport d'erreurs
- **Efficacité Mémoire** : Traite les grandes images en utilisant des structures pyramidales
- **Design Modulaire** : Séparation claire des étapes du pipeline
- **Support de Débogage** : Préserve les fichiers intermédiaires pour analyse
- **Compatibilité Windows** : Détection automatique des couleurs terminal

## 📊 Performance

Le pipeline affiche automatiquement :
- Temps de traitement pour chaque étape
- Comparaisons de taille de fichiers
- Ratios de compression
- Optimisation de l'utilisation mémoire

## 🔧 Détails Techniques

### Dépendances
- **pyvips** : Traitement d'images haute performance
- **openslide** : Support des formats d'images médicales
- **opencv** : Opérations de vision par ordinateur
- **shapely** : Opérations géométriques pour les masques
- **rich** : Interface terminal belle
- **tifffile** : Gestion du format TIFF

### Formats d'Images
- **Entrée** : SVS (Aperio), TIFF, autres formats supportés par OpenSlide
- **Masques** : GeoJSON avec géométries polygon/multipolygon
- **Sortie** : TIFF pyramidal avec canaux RGBA

### Gestion Mémoire
- Traite les images par tuiles pour gérer les gros fichiers
- Utilise des structures pyramidales pour optimiser l'utilisation mémoire
- Paramètres de cache configurables via variables d'environnement

## 🐳 Support Docker

### Docker Hub

L'image est disponible sur Docker Hub :

```bash
docker pull votre-username/tissue-extraction-pipeline:latest
```

### Construction Locale

```dockerfile
FROM continuumio/miniconda3

# Copier le fichier d'environnement
COPY environment.yml /app/
WORKDIR /app

# Créer l'environnement conda
RUN conda env create -f environment.yml

# Copier le script du pipeline
COPY unified_tissue_pipeline.py /app/

# Activer l'environnement et exécuter
SHELL ["conda", "run", "-n", "tissue-extraction-pipeline", "/bin/bash", "-c"]
ENTRYPOINT ["conda", "run", "-n", "tissue-extraction-pipeline", "python", "unified_tissue_pipeline.py"]
```

### Docker Compose

```bash
# Préparer vos fichiers
mkdir -p data/{input,output,temp}
cp tissue.svs data/input/
cp annotations.geojson data/input/

# Exécuter avec variables d'environnement
SVS_FILE=tissue.svs GEOJSON_FILE=annotations.geojson OUTPUT_FILE=result.tiff docker-compose up
```

## 🔍 Dépannage

### Problèmes Courants

1. **Erreurs mémoire** : Réduire la variable d'environnement `VIPS_CONCURRENCY`
2. **Erreurs OpenSlide** : S'assurer que les dépendances système sont installées
3. **Format GeoJSON** : Vérifier que le GeoJSON contient des features polygon valides
4. **Permissions de fichiers** : Vérifier l'accès lecture/écriture aux répertoires d'entrée/sortie
5. **Couleurs Windows** : Le pipeline détecte automatiquement le support des couleurs terminal

### Variables d'Environnement

```bash
export VIPS_CONCURRENCY=2          # Réduire pour les systèmes à faible mémoire
export VIPS_DISC_THRESHOLD=500mb   # Ajuster le seuil de cache disque
export OPENCV_IO_MAX_IMAGE_PIXELS=1073741824  # Taille max d'image
```

## 📝 Exemple de Flux de Travail

```bash
# 1. Préparer vos fichiers
ls -la
# input.svs          (image de lame entière)
# annotations.geojson (masque de tissus)

# 2. Exécuter le pipeline
python unified_tissue_pipeline.py input.svs annotations.geojson extracted_tissue.tiff

# 3. Vérifier les résultats
ls -la extracted_tissue.tiff
# TIFF RGBA avec arrière-plan transparent et tissus extraits
```

## 🎮 Sélection Interactive des Niveaux

Le pipeline offre une sélection interactive des niveaux pyramidaux :

```
🔍 SÉLECTION DE NIVEAUX
──────────────────────────────────────────────────
Niveaux Pyramidaux Disponibles :
• Niveaux de tissus : 11
• Niveaux de masque : 9
• Maximum traitable : 9
• Indices de niveaux : 0 à 8

Options de Sélection :
• Niveau unique : '0' ou '2'
• Niveaux multiples : '0,1,2' ou '1,3,5'
• Plage : '0-3' ou '2-5'
• Tous les niveaux : appuyer sur Entrée (défaut)
──────────────────────────────────────────────────

Entrer les niveaux pyramidaux à traiter (défaut : tous) : 5,6,7
```

## 🤝 Contribution

Ce pipeline combine et étend les fonctionnalités de plusieurs scripts spécialisés :
- Utilitaires de conversion SVS
- Génération de masques pyramidaux
- Extraction avancée de tissus

Lors de contributions, veuillez maintenir la structure modulaire et la gestion complète des erreurs.

## 📄 Licence

Ce projet s'appuie sur des outils d'imagerie médicale existants et suit leurs termes de licence respectifs.

## 🌟 Fonctionnalités Avancées

- **Détection Automatique de Terminal** : S'adapte aux capacités de couleur de votre terminal
- **Interface Multilingue** : Support français complet
- **Conteneurisation Complète** : Images Docker prêtes pour la production
- **Sélection Flexible de Niveaux** : Contrôle précis sur les niveaux pyramidaux à traiter
- **Optimisation Mémoire** : Gestion intelligente des ressources pour les grandes images