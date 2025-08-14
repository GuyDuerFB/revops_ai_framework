#!/bin/bash
# RevOps Webhook Gateway Load Testing Script
# Usage: ./webhook-load-test.sh [concurrent_requests] [total_requests]
# Example: ./webhook-load-test.sh 3 10

set -e

# Configuration
ENDPOINT="https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook"
CONCURRENT_REQUESTS=${1:-5}
TOTAL_REQUESTS=${2:-20}

echo "🔥 RevOps Webhook Gateway Load Test"
echo "==================================="
echo "📊 Configuration:"
echo "   Endpoint: $ENDPOINT"
echo "   Concurrent Requests: $CONCURRENT_REQUESTS"
echo "   Total Requests: $TOTAL_REQUESTS"
echo ""

# Set AWS profile
export AWS_PROFILE=FireboltSystemAdministrator-740202120544

# Create results directory
RESULTS_DIR="load-test-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"
echo "📁 Results will be saved to: $RESULTS_DIR"

# Start load test
START_TIME=$(date +%s)
TRACKING_IDS=()

echo "🚀 Starting load test..."
echo ""

for i in $(seq 1 $TOTAL_REQUESTS); do
  (
    REQUEST_START=$(date +%s.%3N)
    echo "📤 Sending request $i/$(echo $TOTAL_REQUESTS) (PID: $$)"
    
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}\n" \
      -X POST $ENDPOINT \
      -H "Content-Type: application/json" \
      -d "{
        \"query\": \"Load test query $i - $(date) - What are the key metrics for Q4 2024 sales performance analysis?\",
        \"source_system\": \"load_test\",
        \"source_process\": \"performance_validation_$i\",
        \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
      }")
    
    REQUEST_END=$(date +%s.%3N)
    REQUEST_DURATION=$(echo "$REQUEST_END - $REQUEST_START" | bc -l)
    
    # Parse response
    BODY=$(echo "$RESPONSE" | head -n -2)
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    CURL_TIME=$(echo "$RESPONSE" | grep "TIME_TOTAL:" | cut -d: -f2)
    
    if [ "$HTTP_CODE" -eq 200 ] && echo "$BODY" | grep -q '"success":true'; then
      TRACKING_ID=$(echo "$BODY" | grep -o '"tracking_id":"[^"]*"' | cut -d'"' -f4 || echo "NO_ID")
      STATUS="✅ SUCCESS"
    else
      TRACKING_ID="ERROR"
      STATUS="❌ FAILED"
    fi
    
    RESULT="Request $i: $STATUS | HTTP: $HTTP_CODE | Duration: ${REQUEST_DURATION}s | Tracking: $TRACKING_ID"
    echo "$RESULT"
    
    # Save detailed result
    echo "=== Request $i ===" >> "$RESULTS_DIR/request_$i.log"
    echo "Start Time: $REQUEST_START" >> "$RESULTS_DIR/request_$i.log"
    echo "End Time: $REQUEST_END" >> "$RESULTS_DIR/request_$i.log"
    echo "Duration: ${REQUEST_DURATION}s" >> "$RESULTS_DIR/request_$i.log"
    echo "HTTP Code: $HTTP_CODE" >> "$RESULTS_DIR/request_$i.log"
    echo "Curl Time: $CURL_TIME" >> "$RESULTS_DIR/request_$i.log"
    echo "Tracking ID: $TRACKING_ID" >> "$RESULTS_DIR/request_$i.log"
    echo "Response Body:" >> "$RESULTS_DIR/request_$i.log"
    echo "$BODY" >> "$RESULTS_DIR/request_$i.log"
    echo "" >> "$RESULTS_DIR/request_$i.log"
    
    # Add to summary
    echo "${REQUEST_DURATION},${HTTP_CODE},${TRACKING_ID}" >> "$RESULTS_DIR/summary.csv"
    
  ) &
  
  # Limit concurrent requests
  if (( i % CONCURRENT_REQUESTS == 0 )); then
    echo "⏱️  Waiting for batch to complete..."
    wait
  fi
done

# Wait for all background processes
wait

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo ""
echo "📊 Load Test Results"
echo "===================="
echo "⏱️  Total Duration: ${TOTAL_DURATION}s"
echo "📈 Requests per Second: $(echo "scale=2; $TOTAL_REQUESTS / $TOTAL_DURATION" | bc -l)"

# Analyze results
if [ -f "$RESULTS_DIR/summary.csv" ]; then
    SUCCESS_COUNT=$(grep -c ",200," "$RESULTS_DIR/summary.csv" || echo "0")
    TOTAL_COUNT=$(wc -l < "$RESULTS_DIR/summary.csv")
    SUCCESS_RATE=$(echo "scale=2; $SUCCESS_COUNT * 100 / $TOTAL_COUNT" | bc -l)
    
    echo "✅ Successful Requests: $SUCCESS_COUNT/$TOTAL_COUNT (${SUCCESS_RATE}%)"
    
    # Calculate average response time
    if [ "$SUCCESS_COUNT" -gt 0 ]; then
        AVG_TIME=$(awk -F',' '{sum+=$1; count++} END {printf "%.2f", sum/count}' "$RESULTS_DIR/summary.csv")
        echo "⚡ Average Response Time: ${AVG_TIME}s"
    fi
    
    # Show tracking IDs for monitoring
    echo ""
    echo "🔍 Tracking IDs for monitoring:"
    grep -o '"tracking_id":"[^"]*"' "$RESULTS_DIR"/*.log | cut -d'"' -f4 | head -5
    if [ "$TOTAL_REQUESTS" -gt 5 ]; then
        echo "   ... and $((TOTAL_REQUESTS - 5)) more (see $RESULTS_DIR/summary.csv)"
    fi
fi

echo ""
echo "📁 Detailed results saved to: $RESULTS_DIR/"
echo ""
echo "🔍 Monitoring Commands:"
echo "   Monitor processing: aws logs tail /aws/lambda/revops-webhook --follow"
echo "   Check queue status: aws sqs get-queue-attributes --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue --attribute-names ApproximateNumberOfMessages"
echo "   Search by tracking ID: aws logs filter-log-events --log-group-name '/aws/lambda/revops-webhook' --filter-pattern 'TRACKING_ID_HERE'"

echo ""
if [ "$SUCCESS_RATE" = "100.00" ]; then
    echo "🎉 Load test PASSED: All requests successful!"
else
    echo "⚠️  Load test completed with errors. Check logs for details."
fi