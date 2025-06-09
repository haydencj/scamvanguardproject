#!/usr/bin/env python3

import sys
import time
from datetime import datetime

# Import all test modules
from test_ses_config import test_ses_configuration, test_sending_statistics
from test_bounce_handling import test_sns_topics_exist, test_bounce_handler_lambda, test_complaint_handling
from test_rate_limiting import test_dynamodb_table_exists, test_rate_limit_enforcement
from test_e2e import test_complete_email_flow

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}")

def run_all_tests():
    """Run complete test suite"""
    print_header("ScamVanguard Production Readiness Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Define test groups
    test_groups = [
        {
            "name": "SES Configuration",
            "tests": [
                ("Domain Verification & DKIM", test_ses_configuration),
                ("Sending Statistics", test_sending_statistics)
            ]
        },
        {
            "name": "Bounce & Complaint Handling",
            "tests": [
                ("SNS Topics Setup", test_sns_topics_exist),
                ("Bounce Processing", test_bounce_handler_lambda),
                ("Complaint Processing", test_complaint_handling)
            ]
        },
        {
            "name": "Rate Limiting",
            "tests": [
                ("DynamoDB Setup", test_dynamodb_table_exists),
                ("Rate Limit Enforcement", test_rate_limit_enforcement)
            ]
        },
        {
            "name": "End-to-End Flow",
            "tests": [
                ("Complete Email Processing", test_complete_email_flow)
            ]
        }
    ]

    total_passed = 0
    total_failed = 0
    failed_tests = []

    for group in test_groups:
        print_header(f"Testing: {group['name']}")

        for test_name, test_func in group['tests']:
            print(f"\n🧪 {test_name}")
            print("-" * 50)

            try:
                test_func()
                total_passed += 1
                print(f"\n✅ {test_name} PASSED")
            except Exception as e:
                total_failed += 1
                failed_tests.append((test_name, str(e)))
                print(f"\n❌ {test_name} FAILED: {e}")

            # Small delay between tests
            time.sleep(1)

    # Print summary
    print_header("Test Summary")
    print(f"Total tests run: {total_passed + total_failed}")
    print(f"Passed: {total_passed} ✅")
    print(f"Failed: {total_failed} ❌")

    if failed_tests:
        print("\nFailed tests:")
        for test_name, error in failed_tests:
            print(f"  - {test_name}: {error}")

    print_header("Production Readiness Checklist")

    if total_failed == 0:
        print("🎉 All tests passed! Your system appears ready for SES production access.")
        print("\nNext steps:")
        print("1. Monitor your bounce/complaint rates for 24-48 hours")
        print("2. Process some real test emails")
        print("3. Document your test results")
        print("4. Submit SES production access request with this evidence")
        return 0
    else:
        print("⚠️  Some tests failed. Address these issues before requesting production access:")
        print("1. Fix all failing tests")
        print("2. Re-run the test suite")
        print("3. Ensure all metrics are being recorded")
        print("4. Verify bounce/complaint handling works correctly")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
