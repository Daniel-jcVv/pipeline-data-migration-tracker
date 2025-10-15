#!/bin/bash
# Crear Service Principal para Fabric

az login
SP=$(az ad sp create-for-rbac --name "fabric-migration-sp" --role "Storage Blob Data Contributor")

echo "Copia estas variables a .env:"
echo "AZURE_CLIENT_ID=$(echo $SP | jq -r '.appId')"
echo "AZURE_CLIENT_SECRET=$(echo $SP | jq -r '.password')"
echo "AZURE_TENANT_ID=$(echo $SP | jq -r '.tenant')"
echo ""
echo "Luego cambia en .env:"
echo "MOCK_FABRIC=false"
