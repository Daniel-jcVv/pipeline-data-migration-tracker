#!/bin/bash

# This script confiures autentication for Microsoft Fabric on a Linux system.

echo "=========================================="
echo "Setting up Microsoft Fabric Authentication"

# 1. login interactively (open browser)
echo "1. Starting interactive login..."
az login

# 2. configure default tenant, workspace and lakehouse
echo "2. Configuring default tenant: $TENANT_ID"
az account set --tenant $TENANT_ID

# 3. Check active session
echo "3. Checking active session..."
az account show

echo "=========================================="
echo "Microsoft Fabric Authentication setup complete."
echo "now execute: python run_migration.py"
echo "=========================================="

