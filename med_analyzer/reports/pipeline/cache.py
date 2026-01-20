"""
Cached resources that should only be built once
"""
from pathlib import Path
from .normalization import build_test_ontology

DATA_ROOT = Path("C:/medical_data")

# Build ontology ONCE when this module is imported
print("🔧 Building test ontology cache...")
annotation_files = list(DATA_ROOT.glob("*.json"))
ONTOLOGY = build_test_ontology(annotation_files)
print(f"✅ Cached {len(ONTOLOGY)} test types")

