#!/bin/bash
# Reorganización rápida Fase 1

# Crear logs/
mkdir -p logs/pipeline logs/errors

# Mover migration.log
[ -f migration.log ] && mv migration.log logs/pipeline/

# Crear .gitkeep para carpetas vacías
touch logs/pipeline/.gitkeep logs/errors/.gitkeep
touch data/fabric-mock/.gitkeep

echo "✅ Estructura reorganizada"
echo ""
echo "Próximos pasos:"
echo "1. Actualizar run_pipeline.py: migration.log → logs/pipeline/migration.log"
echo "2. Ejecutar: python run_pipeline.py"
