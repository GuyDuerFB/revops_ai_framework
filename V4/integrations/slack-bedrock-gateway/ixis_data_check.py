#!/usr/bin/env python3
"""
IXIS Data Check Script
Test script to check for IXIS data in the Firebolt data warehouse across multiple tables.
"""

import json
import sys
import os

# Add the query lambda path to import the function
sys.path.append('/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/tools/firebolt/query_lambda')

try:
    from lambda_function import query_fire
    print("✓ Successfully imported query_fire function")
except ImportError as e:
    print(f"✗ Failed to import query_fire: {e}")
    sys.exit(1)

def test_ixis_data():
    """
    Test queries to check for IXIS data in the specified tables.
    """
    print("=" * 60)
    print("IXIS DATA WAREHOUSE CHECK")
    print("=" * 60)
    
    # Test queries for each table
    test_queries = [
        {
            "name": "IXIS in opportunity_d table",
            "query": """
            SELECT 
                account_name,
                opportunity_name,
                opportunity_id,
                stage_name,
                close_date,
                amount,
                probability,
                created_date,
                owner_name
            FROM opportunity_d 
            WHERE UPPER(account_name) LIKE '%IXIS%' 
               OR UPPER(opportunity_name) LIKE '%IXIS%'
            ORDER BY created_date DESC
            LIMIT 20;
            """,
            "description": "Search for IXIS opportunities in the opportunity_d table"
        },
        {
            "name": "IXIS in gong_call_f table",
            "query": """
            SELECT 
                account_name,
                call_title,
                call_date,
                call_duration_minutes,
                host_name,
                attendees,
                opportunity_name,
                call_type,
                created_date
            FROM gong_call_f 
            WHERE UPPER(account_name) LIKE '%IXIS%' 
               OR UPPER(call_title) LIKE '%IXIS%'
               OR UPPER(attendees) LIKE '%IXIS%'
            ORDER BY call_date DESC
            LIMIT 20;
            """,
            "description": "Search for IXIS calls in the gong_call_f table"
        },
        {
            "name": "IXIS in salesforce_account_d table",
            "query": """
            SELECT 
                account_name,
                account_id,
                account_type,
                industry,
                account_owner,
                created_date,
                last_modified_date,
                parent_account_name,
                account_status
            FROM salesforce_account_d 
            WHERE UPPER(account_name) LIKE '%IXIS%' 
               OR UPPER(parent_account_name) LIKE '%IXIS%'
            ORDER BY last_modified_date DESC
            LIMIT 20;
            """,
            "description": "Search for IXIS accounts in the salesforce_account_d table"
        },
        {
            "name": "IXIS Data Summary Count",
            "query": """
            SELECT 
                'opportunity_d' as table_name,
                COUNT(*) as ixis_record_count
            FROM opportunity_d 
            WHERE UPPER(account_name) LIKE '%IXIS%' 
               OR UPPER(opportunity_name) LIKE '%IXIS%'
            
            UNION ALL
            
            SELECT 
                'gong_call_f' as table_name,
                COUNT(*) as ixis_record_count
            FROM gong_call_f 
            WHERE UPPER(account_name) LIKE '%IXIS%' 
               OR UPPER(call_title) LIKE '%IXIS%'
               OR UPPER(attendees) LIKE '%IXIS%'
            
            UNION ALL
            
            SELECT 
                'salesforce_account_d' as table_name,
                COUNT(*) as ixis_record_count
            FROM salesforce_account_d 
            WHERE UPPER(account_name) LIKE '%IXIS%' 
               OR UPPER(parent_account_name) LIKE '%IXIS%'
            
            ORDER BY ixis_record_count DESC;
            """,
            "description": "Get count of IXIS records in each table"
        }
    ]
    
    # Execute each test query
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 50)
        print(f"Description: {test['description']}")
        print(f"Query: {test['query'][:100]}...")
        
        try:
            # Execute the query using the imported function
            result = query_fire(query=test['query'])
            
            if result.get('success', False):
                print("✓ Query executed successfully")
                print(f"  Columns: {len(result.get('columns', []))}")
                print(f"  Rows: {result.get('row_count', 0)}")
                
                # Show column names
                if result.get('columns'):
                    column_names = [col['name'] for col in result['columns']]
                    print(f"  Column names: {', '.join(column_names)}")
                
                # Show some sample data
                if result.get('results') and len(result['results']) > 0:
                    print("  Sample data:")
                    for j, row in enumerate(result['results'][:3]):  # Show first 3 rows
                        print(f"    Row {j+1}: {row}")
                    
                    if len(result['results']) > 3:
                        print(f"    ... and {len(result['results']) - 3} more rows")
                else:
                    print("  No data returned")
                    
            else:
                print("✗ Query failed")
                print(f"  Error: {result.get('error', 'Unknown error')}")
                print(f"  Message: {result.get('message', 'No message')}")
                
        except Exception as e:
            print(f"✗ Exception occurred: {str(e)}")
        
        print()

def main():
    """
    Main function to run the IXIS data check
    """
    print("Starting IXIS data check...")
    print("This script will search for IXIS data in the Firebolt data warehouse.")
    print()
    
    # Check if we have the required environment variables
    required_env_vars = [
        'FIREBOLT_ACCOUNT_NAME',
        'FIREBOLT_ENGINE_NAME', 
        'FIREBOLT_DATABASE',
        'FIREBOLT_CREDENTIALS_SECRET'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables before running the script.")
        print("Example values:")
        print("  export FIREBOLT_ACCOUNT_NAME='your-account'")
        print("  export FIREBOLT_ENGINE_NAME='your-engine'")
        print("  export FIREBOLT_DATABASE='your-database'")
        print("  export FIREBOLT_CREDENTIALS_SECRET='firebolt-credentials'")
        return
    
    # Show current configuration
    print("Current Firebolt configuration:")
    print(f"  Account: {os.environ.get('FIREBOLT_ACCOUNT_NAME', 'not set')}")
    print(f"  Engine: {os.environ.get('FIREBOLT_ENGINE_NAME', 'not set')}")
    print(f"  Database: {os.environ.get('FIREBOLT_DATABASE', 'not set')}")
    print(f"  Credentials Secret: {os.environ.get('FIREBOLT_CREDENTIALS_SECRET', 'not set')}")
    print()
    
    # Run the tests
    test_ixis_data()
    
    print("=" * 60)
    print("IXIS DATA CHECK COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()