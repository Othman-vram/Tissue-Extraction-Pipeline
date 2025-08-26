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

### Option 3 : Creation d'un container Docker

```bash
# Télécharger depuis Docker Hub
git clone https://github.com/Othman-vram/Tissue-Extraction-Pipeline.git

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
docker run -it --rm \
    -v C:/chemin/complet/vers/vos/fichiers:/app \
    tissue-extraction-pipeline \
    <image_entière.svs> \
    <masque_tissu.geojson> \
    <tissu_extrait.tiff>
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
docker push othmanel7/tissue-extraction-pipeline:latest
```

### Construction Locale

```dockerfile
FROM continuumio/miniconda3:latest

LABEL maintainer="Tissue Extraction Pipeline"
LABEL description="Unified pipeline for tissue extraction from whole-slide images"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libglib2.0-dev \
    libvips-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    openslide-tools \
    && rm -rf /var/lib/apt/lists/*



COPY environment.yml /app/


RUN conda env create -f environment.yml && conda clean -afy


COPY unified_tissue_pipeline.py /app/
COPY README.md /app/


RUN mkdir -p /app/input /app/output /app/temp


ENV VIPS_CONCURRENCY=4
ENV VIPS_DISC_THRESHOLD=1gb
ENV OPENCV_IO_MAX_IMAGE_PIXELS=1073741824


ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "pipeline", "python", "/app/unified_tissue_pipeline.py"]

CMD ["--help"]
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
