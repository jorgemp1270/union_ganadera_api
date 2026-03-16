#!/bin/bash

# LocalStack S3 initialization script
# This script creates the necessary S3 buckets and configures CORS for development

set -e

AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-test}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-test}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
LOCALSTACK_ENDPOINT=${LOCALSTACK_ENDPOINT:-http://localstack:4566}

echo "Starting LocalStack S3 initialization..."
echo "Endpoint: $LOCALSTACK_ENDPOINT"
echo "Region: $AWS_DEFAULT_REGION"

# Function to create bucket with retry logic
create_bucket() {
    local bucket_name=$1
    local max_retries=10
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if aws s3 mb "s3://$bucket_name" \
            --endpoint-url "$LOCALSTACK_ENDPOINT" \
            --region "$AWS_DEFAULT_REGION" \
            --no-verify-ssl \
            2>/dev/null; then
            echo "✓ Bucket '$bucket_name' created successfully"
            return 0
        else
            local status=$?
            # 254 means bucket already exists, which is OK
            if [ $status -eq 254 ]; then
                echo "✓ Bucket '$bucket_name' already exists"
                return 0
            fi
            
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                echo "  Attempt $retry_count/$max_retries failed, retrying in 2 seconds..."
                sleep 2
            fi
        fi
    done
    
    echo "✗ Failed to create bucket '$bucket_name' after $max_retries attempts"
    return 1
}

# Function to set public access
set_public_access() {
    local bucket_name=$1
    
    # Set public-read ACL
    aws s3api put-bucket-acl \
        --bucket "$bucket_name" \
        --acl public-read \
        --endpoint-url "$LOCALSTACK_ENDPOINT" \
        --region "$AWS_DEFAULT_REGION" \
        --no-verify-ssl \
        2>/dev/null || echo "  (Note: ACL setting not critical for local development)"
}

# Function to set CORS
set_cors() {
    local bucket_name=$1
    
    # Create CORS configuration JSON
    cat > /tmp/cors-config.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag", "x-amz-version-id"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF
    
    aws s3api put-bucket-cors \
        --bucket "$bucket_name" \
        --cors-configuration file:///tmp/cors-config.json \
        --endpoint-url "$LOCALSTACK_ENDPOINT" \
        --region "$AWS_DEFAULT_REGION" \
        --no-verify-ssl \
        2>/dev/null || echo "  (Note: CORS configuration may not be available in LocalStack)"
}

# Create the main bucket
echo ""
echo "Creating S3 bucket: documentos"
create_bucket "documentos"
set_public_access "documentos"
set_cors "documentos"

# Verify bucket exists
echo ""
echo "Verifying bucket creation..."
if aws s3 ls "s3://documentos" \
    --endpoint-url "$LOCALSTACK_ENDPOINT" \
    --region "$AWS_DEFAULT_REGION" \
    --no-verify-ssl \
    2>/dev/null; then
    echo "✓ Bucket 'documentos' is accessible"
else
    echo "✗ Warning: Could not verify bucket access"
fi

echo ""
echo "✓ LocalStack S3 initialization complete"
exit 0
