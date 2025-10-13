#!/bin/bash
#################################################
# AWS S3 Setup for Microsoft Fabric Migration
# Purpose: Configure AWS S3 bucket and upload data
#################################################

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AWS S3 Setup for Fabric Migration${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Variables - CUSTOMIZE THESE
BUCKET_NAME="fabric-migration-data-$(date +%s)"  # Unique bucket name
REGION="us-east-1"  # Change to your preferred region
PROJECT_DATA_DIR="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")/data"

echo -e "${BLUE}Configuration:${NC}"
echo "  Bucket Name: ${BUCKET_NAME}"
echo "  Region: ${REGION}"
echo "  Project Data: ${PROJECT_DATA_DIR}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    echo -e "${YELLOW}Installing AWS CLI...${NC}"
    
    # Install AWS CLI v2
    cd /tmp
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install --update
    rm -rf aws awscliv2.zip
    
    echo -e "${GREEN}✓ AWS CLI installed${NC}"
fi

# Check AWS CLI version
echo -e "\n${BLUE}AWS CLI Version:${NC}"
aws --version

# Configure AWS credentials
echo -e "\n${GREEN}[1/5] Configuring AWS Credentials...${NC}"
if [ ! -f ~/.aws/credentials ]; then
    echo -e "${YELLOW}AWS credentials not found. Please configure:${NC}"
    aws configure
    echo -e "${GREEN}✓ AWS credentials configured${NC}"
else
    echo -e "${YELLOW}AWS credentials already exist${NC}"
    read -p "Do you want to reconfigure? (y/N): " RECONFIGURE
    if [[ "$RECONFIGURE" =~ ^[Yy]$ ]]; then
        aws configure
    fi
fi

# Verify AWS credentials
echo -e "\n${GREEN}[2/5] Verifying AWS credentials...${NC}"
if aws sts get-caller-identity &> /dev/null; then
    echo -e "${GREEN}✓ AWS credentials verified${NC}"
    aws sts get-caller-identity
else
    echo -e "${RED}❌ AWS credentials verification failed${NC}"
    echo -e "${YELLOW}Please check your AWS Access Key and Secret Key${NC}"
    exit 1
fi

# Create S3 bucket
echo -e "\n${GREEN}[3/5] Creating S3 bucket...${NC}"
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    if [ "$REGION" == "us-east-1" ]; then
        aws s3 mb "s3://${BUCKET_NAME}"
    else
        aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}"
    fi
    echo -e "${GREEN}✓ Bucket created: ${BUCKET_NAME}${NC}"
else
    echo -e "${YELLOW}  Bucket already exists or name taken, using: ${BUCKET_NAME}${NC}"
fi

# Enable versioning (optional but recommended)
echo -e "\n${GREEN}[4/5] Enabling bucket versioning...${NC}"
aws s3api put-bucket-versioning \
    --bucket "${BUCKET_NAME}" \
    --versioning-configuration Status=Enabled
echo -e "${GREEN}✓ Versioning enabled${NC}"

# Upload data files
echo -e "\n${GREEN}[5/5] Uploading data files...${NC}"
if [ -d "$PROJECT_DATA_DIR" ]; then
    # Create folder structure in S3
    echo -e "${BLUE}Creating folder structure...${NC}"
    
    # Upload CSV files
    if [ -f "$PROJECT_DATA_DIR/orders_data.csv" ]; then
        aws s3 cp "$PROJECT_DATA_DIR/orders_data.csv" "s3://${BUCKET_NAME}/migration-data/csv/"
        echo -e "${GREEN}  ✓ Uploaded orders_data.csv${NC}"
    fi
    
    # Upload JSON files
    if [ -f "$PROJECT_DATA_DIR/inventory_data.json" ]; then
        aws s3 cp "$PROJECT_DATA_DIR/inventory_data.json" "s3://${BUCKET_NAME}/migration-data/json/"
        echo -e "${GREEN}  ✓ Uploaded inventory_data.json${NC}"
    fi
    
    # Upload Excel files (Note: Fabric may require conversion to CSV)
    if [ -f "$PROJECT_DATA_DIR/returns_data.xlsx" ]; then
        aws s3 cp "$PROJECT_DATA_DIR/returns_data.xlsx" "s3://${BUCKET_NAME}/migration-data/excel/"
        echo -e "${GREEN}  ✓ Uploaded returns_data.xlsx${NC}"
    fi
    
    echo -e "${GREEN}✓ All files uploaded${NC}"
else
    echo -e "${YELLOW}  Project data directory not found${NC}"
    echo -e "${YELLOW}  You can upload files manually using:${NC}"
    echo -e "    aws s3 cp /path/to/file s3://${BUCKET_NAME}/migration-data/"
fi

# List uploaded files
echo -e "\n${BLUE}Files in S3 bucket:${NC}"
aws s3 ls "s3://${BUCKET_NAME}/migration-data/" --recursive

# Set bucket policy (optional - for more secure access)
echo -e "\n${YELLOW}Setting up bucket policy...${NC}"
cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "FabricReadAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "$(aws sts get-caller-identity --query Arn --output text)"
            },
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::${BUCKET_NAME}/*",
                "arn:aws:s3:::${BUCKET_NAME}"
            ]
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket "${BUCKET_NAME}" --policy file:///tmp/bucket-policy.json
rm /tmp/bucket-policy.json
echo -e "${GREEN}✓ Bucket policy applied${NC}"

# Display summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ AWS S3 Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Get AWS credentials for Fabric
AWS_ACCESS_KEY=$(aws configure get aws_access_key_id)
AWS_REGION=$(aws configure get region)

echo -e "${BLUE}Connection Details for Microsoft Fabric:${NC}"
echo -e "  Bucket Name: ${BUCKET_NAME}"
echo -e "  Region: ${AWS_REGION}"
echo -e "  Access Key ID: ${AWS_ACCESS_KEY}"
echo -e "  Secret Access Key: [Hidden - check ~/.aws/credentials]"
echo ""
echo -e "${BLUE}S3 URIs:${NC}"
echo -e "  Base URI: s3://${BUCKET_NAME}/migration-data/"
echo -e "  CSV: s3://${BUCKET_NAME}/migration-data/csv/"
echo -e "  JSON: s3://${BUCKET_NAME}/migration-data/json/"
echo -e "  Excel: s3://${BUCKET_NAME}/migration-data/excel/"
echo ""
echo -e "${BLUE}Connection String for Fabric (Amazon S3 Connector):${NC}"
echo -e "  https://${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com;AwsCredentials=${AWS_ACCESS_KEY},<YourSecretKey>"
echo ""
echo -e "${YELLOW}⚠️  Security Notes:${NC}"
echo -e "  1. Store credentials securely (use AWS Secrets Manager or Fabric Key Vault)"
echo -e "  2. Use IAM roles with least privilege"
echo -e "  3. Enable CloudTrail for audit logging"
echo -e "  4. Consider using AWS PrivateLink for private connectivity"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  List files: aws s3 ls s3://${BUCKET_NAME}/migration-data/ --recursive"
echo -e "  Upload file: aws s3 cp /local/file s3://${BUCKET_NAME}/migration-data/"
echo -e "  Download file: aws s3 cp s3://${BUCKET_NAME}/migration-data/file /local/"
echo -e "  Delete bucket: aws s3 rb s3://${BUCKET_NAME} --force"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Test S3 access: aws s3 ls s3://${BUCKET_NAME}/"
echo -e "  2. Configure Microsoft Fabric Amazon S3 connector"
echo -e "  3. See README-aws-s3.md for Fabric setup instructions"
echo ""

# Save connection details
cat > "$(dirname "$0")/s3-connection-details.txt" << EOF
AWS S3 Connection Details for Microsoft Fabric
================================================

Bucket Name: ${BUCKET_NAME}
Region: ${AWS_REGION}
Access Key ID: ${AWS_ACCESS_KEY}
Secret Access Key: [Check ~/.aws/credentials]

Connection String:
https://${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com;AwsCredentials=${AWS_ACCESS_KEY},<YourSecretKey>

S3 Paths:
- CSV files: s3://${BUCKET_NAME}/migration-data/csv/
- JSON files: s3://${BUCKET_NAME}/migration-data/json/
- Excel files: s3://${BUCKET_NAME}/migration-data/excel/

Created: $(date)
EOF

echo -e "${GREEN}✓ Connection details saved to: s3-connection-details.txt${NC}"
echo ""
