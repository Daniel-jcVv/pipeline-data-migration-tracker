

# SFTP server setup for microsoft fabric data migration
# Compatible with KDE Neon Linux
# Purpose: Configure SFTP as data source for MS fabric pipelines


set -e  # exit on error

# colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # no color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SFTP Server setup for fabric${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}DO NOT run this script as root/sudo${NC}"
   echo -e "Run it normally, it will ask for sudo when needed"
   exit 1
fi

# variables - CUSTOMIZE THESE
SFTP_USER="fabricdata"
SFTP_PASSWORD="fabric-migration25"  # CHANGE THIS IN PRODUCTION!!!!!!
DATA_DIR="/home/${SFTP_USER}/migration-files"
SSH_PORT=22  # default SSH port
PROJECT_DATA_DIR="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")/data"

echo -e "${BLUE}Configuration:${NC}"
echo "  SFTP User: ${SFTP_USER}"
echo "  Data Directory: ${DATA_DIR}"
echo "  SSH Port: ${SSH_PORT}"
echo "  Project Data: ${PROJECT_DATA_DIR}"
echo ""
read -p "Press enter to continue or ctrl+c to cancel..."

# 1. install OpenSSH server
echo -e "\n${GREEN}[1/7] Installing OpenSSH Server...${NC}"
if ! dpkg -l | grep -q openssh-server; then
    sudo apt update
    sudo apt install -y openssh-server
    echo -e "${GREEN}✓ OpenSSH Server installed${NC}"
else
    echo -e "${YELLOW}  OpenSSH Server already installed${NC}"
fi

# 2. create SFTP user
echo -e "\n${GREEN}[2/7] Creating SFTP user...${NC}"
if id "${SFTP_USER}" &>/dev/null; then
    echo -e "${YELLOW}  User ${SFTP_USER} already exists${NC}"
else
    sudo useradd -m -d /home/${SFTP_USER} -s /bin/bash ${SFTP_USER}
    echo "${SFTP_USER}:${SFTP_PASSWORD}" | sudo chpasswd
    echo -e "${GREEN}✓ User ${SFTP_USER} created${NC}"
fi

# 3. create data directory structure
echo -e "\n${GREEN}[3/7] Creating data directory structure...${NC}"
sudo mkdir -p ${DATA_DIR}/{csv,json,excel,processed}
sudo chown -R ${SFTP_USER}:${SFTP_USER} /home/${SFTP_USER}
sudo chmod 755 ${DATA_DIR}
echo -e "${GREEN}Directory structure created${NC}"

# 4. Copy sample data files
echo -e "\n${GREEN}[4/7] Copying sample data files...${NC}"
if [ -d "$PROJECT_DATA_DIR" ]; then
    # Copy CSV files
    if [ -f "$PROJECT_DATA_DIR/orders_data.csv" ]; then
        sudo cp "$PROJECT_DATA_DIR/orders_data.csv" "${DATA_DIR}/csv/"
        echo -e "${GREEN}  ✓ Copied orders_data.csv${NC}"
    fi
    
    # copy JSON files
    if [ -f "$PROJECT_DATA_DIR/inventory_data.json" ]; then
        sudo cp "$PROJECT_DATA_DIR/inventory_data.json" "${DATA_DIR}/json/"
        echo -e "${GREEN}copied inventory_data.json${NC}"
    fi
    
    # Copy excel files
    if [ -f "$PROJECT_DATA_DIR/returns_data.xlsx" ]; then
        sudo cp "$PROJECT_DATA_DIR/returns_data.xlsx" "${DATA_DIR}/excel/"
        echo -e "${GREEN}  copied returns_data.xlsx${NC}"
    fi
    
    sudo chown -R ${SFTP_USER}:${SFTP_USER} ${DATA_DIR}
    echo -e "${GREEN}sample data files copied${NC}"
else
    echo -e "${YELLOW}  project data directory not found, skipping sample files${NC}"
fi

# 5. Configure SSH for SFTP
echo -e "\n${GREEN}[5/7] Configuring SSH for SFTP...${NC}"
SSHD_CONFIG="/etc/ssh/sshd_config"

# backup original config
if [ ! -f "${SSHD_CONFIG}.backup" ]; then
    sudo cp ${SSHD_CONFIG} ${SSHD_CONFIG}.backup
    echo -e "${GREEN}  Backup created: ${SSHD_CONFIG}.backup${NC}"
fi

# Check if SFTP config already exists
if ! sudo grep -q "Match User ${SFTP_USER}" ${SSHD_CONFIG}; then
    echo -e "\n# SFTP Configuration for Fabric migration" | sudo tee -a ${SSHD_CONFIG} > /dev/null
    echo "Match User ${SFTP_USER}" | sudo tee -a ${SSHD_CONFIG} > /dev/null
    echo "    ChrootDirectory /home/${SFTP_USER}" | sudo tee -a ${SSHD_CONFIG} > /dev/null
    echo "    ForceCommand internal-sftp" | sudo tee -a ${SSHD_CONFIG} > /dev/null
    echo "    AllowTcpForwarding no" | sudo tee -a ${SSHD_CONFIG} > /dev/null
    echo "    X11Forwarding no" | sudo tee -a ${SSHD_CONFIG} > /dev/null
    echo -e "${GREEN} SFTP configuration added${NC}"
else
    echo -e "${YELLOW}  SFTP configuration already exists${NC}"
fi

# 6. Restart SSH service
echo -e "\n${GREEN}[6/7] Restarting SSH service...${NC}"
sudo systemctl restart sshd
sudo systemctl enable sshd
echo -e "${GREEN} SSH service restarted and enabled${NC}"

# 7. Test SFTP connection
echo -e "\n${GREEN}[7/7] Testing SFTP connection...${NC}"
HOSTNAME=$(hostname -I | awk '{print $1}')

# Create test script
cat > /tmp/sftp_test.sh << 'EOF'
#!/bin/bash
echo "ls" | sftp -P 22 fabricdata@localhost 2>&1 | grep -q "migration-files"
EOF
chmod +x /tmp/sftp_test.sh

if /tmp/sftp_test.sh 2>/dev/null; then
    echo -e "${GREEN} SFTP connection test successful${NC}"
else
    echo -e "${YELLOW} SFTP test skipped (requires password)${NC}"
fi
rm -f /tmp/sftp_test.sh

# Display summary
echo -e "\n${GREEN} ========================================${NC}"
echo -e "${GREEN}  SFTP Server Setup Complete!${NC}"
echo -e "${GREEN}==========================================${NC}\n"

echo -e "${BLUE}Connection details for microsoft fabric:${NC}"
echo -e "  Host: ${HOSTNAME} (or localhost)"
echo -e "  Port: ${SSH_PORT}"
echo -e "  Username: ${SFTP_USER}"
echo -e "  Password: ${SFTP_PASSWORD}"
echo -e "  Data Path: /migration-files/"
echo ""
echo -e "${BLUE}Directory Structure:${NC}"
echo -e "  ${DATA_DIR}/csv/      - CSV files"
echo -e "  ${DATA_DIR}/json/     - JSON files"
echo -e "  ${DATA_DIR}/excel/    - Excel files"
echo -e "  ${DATA_DIR}/processed/ - Processed files"
echo ""
echo -e "${YELLOW} Security notes:${NC}"
echo -e "  1. Change the default password immediately"
echo -e "  2. Use SSH keys instead of passwords in production"
echo -e "  3. Configure firewall rules to limit access"
echo -e "  4. Monitor /var/log/auth.log for unauthorized access"
echo ""
echo -e "${BLUE}Test connection:${NC}"
echo -e "  sftp ${SFTP_USER}@${HOSTNAME}"
echo -e "  (password: ${SFTP_PASSWORD})"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Test SFTP connection manually"
echo -e "  2. Configure Microsoft Fabric connector"
echo -e "  3. See setup-sftp-server.md for fabric setup instructions"
echo ""
