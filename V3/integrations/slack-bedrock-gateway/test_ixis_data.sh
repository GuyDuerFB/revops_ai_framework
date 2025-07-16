#!/bin/bash

# IXIS Data Check Script
# This script tests the Firebolt Lambda function to search for IXIS data
# Usage: ./test_ixis_data.sh [lambda_function_name]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default Lambda function name
LAMBDA_FUNCTION_NAME="${1:-firebolt-query-lambda}"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}IXIS DATA CHECK - FIREBOLT LAMBDA${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed or not in PATH${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"
echo -e "${BLUE}Lambda Function: ${LAMBDA_FUNCTION_NAME}${NC}"
echo ""

# Test 1: IXIS Opportunities Check
echo -e "${YELLOW}Test 1: IXIS Opportunities Check${NC}"
echo "----------------------------------------"
QUERY1="SELECT account_name, opportunity_name, opportunity_id, stage_name, close_date, amount, probability, created_date, owner_name FROM opportunity_d WHERE UPPER(account_name) LIKE '%IXIS%' OR UPPER(opportunity_name) LIKE '%IXIS%' ORDER BY created_date DESC LIMIT 20;"

PAYLOAD1="{\"query\": \"${QUERY1}\"}"

echo "Query: ${QUERY1}"
echo ""

aws lambda invoke \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --payload "${PAYLOAD1}" \
    --cli-binary-format raw-in-base64-out \
    response1.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test 1 executed successfully${NC}"
    echo "Response preview:"
    jq -r '.success, .row_count, .columns[].name' response1.json 2>/dev/null || cat response1.json
else
    echo -e "${RED}❌ Test 1 failed${NC}"
fi

echo ""
echo "----------------------------------------"

# Test 2: IXIS Gong Calls Check
echo -e "${YELLOW}Test 2: IXIS Gong Calls Check${NC}"
echo "----------------------------------------"
QUERY2="SELECT account_name, call_title, call_date, call_duration_minutes, host_name, attendees, opportunity_name, call_type, created_date FROM gong_call_f WHERE UPPER(account_name) LIKE '%IXIS%' OR UPPER(call_title) LIKE '%IXIS%' OR UPPER(attendees) LIKE '%IXIS%' ORDER BY call_date DESC LIMIT 20;"

PAYLOAD2="{\"query\": \"${QUERY2}\"}"

echo "Query: ${QUERY2}"
echo ""

aws lambda invoke \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --payload "${PAYLOAD2}" \
    --cli-binary-format raw-in-base64-out \
    response2.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test 2 executed successfully${NC}"
    echo "Response preview:"
    jq -r '.success, .row_count, .columns[].name' response2.json 2>/dev/null || cat response2.json
else
    echo -e "${RED}❌ Test 2 failed${NC}"
fi

echo ""
echo "----------------------------------------"

# Test 3: IXIS Salesforce Accounts Check
echo -e "${YELLOW}Test 3: IXIS Salesforce Accounts Check${NC}"
echo "----------------------------------------"
QUERY3="SELECT account_name, account_id, account_type, industry, account_owner, created_date, last_modified_date, parent_account_name, account_status FROM salesforce_account_d WHERE UPPER(account_name) LIKE '%IXIS%' OR UPPER(parent_account_name) LIKE '%IXIS%' ORDER BY last_modified_date DESC LIMIT 20;"

PAYLOAD3="{\"query\": \"${QUERY3}\"}"

echo "Query: ${QUERY3}"
echo ""

aws lambda invoke \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --payload "${PAYLOAD3}" \
    --cli-binary-format raw-in-base64-out \
    response3.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test 3 executed successfully${NC}"
    echo "Response preview:"
    jq -r '.success, .row_count, .columns[].name' response3.json 2>/dev/null || cat response3.json
else
    echo -e "${RED}❌ Test 3 failed${NC}"
fi

echo ""
echo "----------------------------------------"

# Test 4: IXIS Record Count Summary
echo -e "${YELLOW}Test 4: IXIS Record Count Summary${NC}"
echo "----------------------------------------"
QUERY4="SELECT 'opportunity_d' as table_name, COUNT(*) as ixis_record_count FROM opportunity_d WHERE UPPER(account_name) LIKE '%IXIS%' OR UPPER(opportunity_name) LIKE '%IXIS%' UNION ALL SELECT 'gong_call_f' as table_name, COUNT(*) as ixis_record_count FROM gong_call_f WHERE UPPER(account_name) LIKE '%IXIS%' OR UPPER(call_title) LIKE '%IXIS%' OR UPPER(attendees) LIKE '%IXIS%' UNION ALL SELECT 'salesforce_account_d' as table_name, COUNT(*) as ixis_record_count FROM salesforce_account_d WHERE UPPER(account_name) LIKE '%IXIS%' OR UPPER(parent_account_name) LIKE '%IXIS%' ORDER BY ixis_record_count DESC;"

PAYLOAD4="{\"query\": \"${QUERY4}\"}"

echo "Query: ${QUERY4}"
echo ""

aws lambda invoke \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --payload "${PAYLOAD4}" \
    --cli-binary-format raw-in-base64-out \
    response4.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test 4 executed successfully${NC}"
    echo "Response preview:"
    jq -r '.success, .row_count, .results' response4.json 2>/dev/null || cat response4.json
else
    echo -e "${RED}❌ Test 4 failed${NC}"
fi

echo ""
echo "----------------------------------------"

# Summary
echo -e "${BLUE}SUMMARY${NC}"
echo "----------------------------------------"
echo "Response files created:"
echo "  - response1.json (Opportunities)"
echo "  - response2.json (Gong Calls)"
echo "  - response3.json (Salesforce Accounts)"
echo "  - response4.json (Count Summary)"
echo ""
echo "To view full responses:"
echo "  cat response1.json | jq ."
echo "  cat response2.json | jq ."
echo "  cat response3.json | jq ."
echo "  cat response4.json | jq ."
echo ""
echo -e "${GREEN}✅ IXIS data check completed!${NC}"