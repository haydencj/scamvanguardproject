from test_config import *

def test_ses_configuration():
    """Verify all SES configuration is correct"""

    print("\n=== Testing SES Configuration ===")

    # 1. Check domain verification
    domain_attrs = ses_client.get_identity_verification_attributes(
        Identities=[DOMAIN_NAME]
    )

    verification_status = domain_attrs['VerificationAttributes'].get(
        DOMAIN_NAME, {}
    ).get('VerificationStatus')

    assert verification_status == 'Success', f"Domain not verified: {verification_status}"
    print(f"✅ Domain {DOMAIN_NAME} verified")

    # 2. Check DKIM
    dkim_attrs = ses_client.get_identity_dkim_attributes(
        Identities=[DOMAIN_NAME]
    )

    dkim_enabled = dkim_attrs['DkimAttributes'].get(
        DOMAIN_NAME, {}
    ).get('DkimEnabled')

    assert dkim_enabled == True, "DKIM not enabled"
    dkim_verified = dkim_attrs['DkimAttributes'].get(
        DOMAIN_NAME, {}
    ).get('DkimVerificationStatus') == 'Success'

    if dkim_verified:
        print("✅ DKIM enabled and verified")
    else:
        print("⚠️  DKIM enabled but not yet verified (check DNS)")

    # 3. Check receipt rules
    try:
        rule_sets = ses_client.list_receipt_rule_sets()
        print(f"✅ Found {len(rule_sets.get('RuleSets', []))} rule sets")

        active_rule_set = ses_client.describe_active_receipt_rule_set()
        active_name = active_rule_set['Metadata']['Name']
        print(f"✅ Active rule set: {active_name}")

        # Check the rules in the active set
        rules = active_rule_set.get('Rules', [])
        scan_rule_found = False
        for rule in rules:
            if SCAN_EMAIL in rule.get('Recipients', []):
                scan_rule_found = True
                print(f"✅ Found rule for {SCAN_EMAIL}")

                # Verify S3 and Lambda actions
                has_s3_action = any(action.get('S3Action') for action in rule.get('Actions', []))
                has_lambda_action = any(action.get('LambdaAction') for action in rule.get('Actions', []))

                assert has_s3_action, "S3 action not configured in receipt rule"
                assert has_lambda_action, "Lambda action not configured in receipt rule"
                print("  ✓ S3 action configured")
                print("  ✓ Lambda action configured")

        assert scan_rule_found, f"No receipt rule found for {SCAN_EMAIL}"

    except ses_client.exceptions.RuleSetDoesNotExistException:
        print("❌ No active receipt rule set!")
        raise

    # 4. Check SNS feedback notifications
    notification_attrs = ses_client.get_identity_notification_attributes(
        Identities=[DOMAIN_NAME]
    )

    notifications = notification_attrs['NotificationAttributes'].get(
        DOMAIN_NAME, {}
    )

    bounce_topic = notifications.get('BounceTopic')
    complaint_topic = notifications.get('ComplaintTopic')

    assert bounce_topic, "Bounce topic not configured"
    assert complaint_topic, "Complaint topic not configured"
    print(f"✅ Bounce notifications: {bounce_topic.split(':')[-1]}")
    print(f"✅ Complaint notifications: {complaint_topic.split(':')[-1]}")

    # 5. Check configuration set (if using)
    try:
        config_sets = ses_client.list_configuration_sets()
        if config_sets['ConfigurationSets']:
            print(f"✅ Found {len(config_sets['ConfigurationSets'])} configuration sets")
    except:
        pass

    return True

def test_sending_statistics():
    """Check current sending statistics and reputation"""

    print("\n=== SES Sending Statistics ===")

    # Get sending quota
    quota = ses_client.get_send_quota()
    usage_percent = (quota['SentLast24Hours'] / quota['Max24HourSend']) * 100 if quota['Max24HourSend'] > 0 else 0

    print(f"\nSending Quota:")
    print(f"  Max send rate: {quota['MaxSendRate']} emails/second")
    print(f"  Max 24hr send: {quota['Max24HourSend']} emails")
    print(f"  Sent last 24hr: {quota['SentLast24Hours']} emails ({usage_percent:.1f}% used)")

    # Get reputation metrics
    stats = ses_client.get_send_statistics()
    if stats['SendDataPoints']:
        # Get last 7 days of data
        recent_data = sorted(stats['SendDataPoints'],
                           key=lambda x: x['Timestamp'],
                           reverse=True)[:7]

        total_sent = sum(dp['DeliveryAttempts'] for dp in recent_data)
        total_bounces = sum(dp['Bounces'] for dp in recent_data)
        total_complaints = sum(dp['Complaints'] for dp in recent_data)

        print(f"\nLast 7 Days Statistics:")
        print(f"  Total sent: {total_sent}")
        print(f"  Total bounces: {total_bounces}")
        print(f"  Total complaints: {total_complaints}")

        if total_sent > 0:
            bounce_rate = (total_bounces / total_sent) * 100
            complaint_rate = (total_complaints / total_sent) * 100

            # AWS thresholds: 5% bounce rate, 0.1% complaint rate
            bounce_status = "🟢 GOOD" if bounce_rate < 5 else "🔴 HIGH"
            complaint_status = "🟢 GOOD" if complaint_rate < 0.1 else "🔴 HIGH"

            print(f"\n  Bounce Rate: {bounce_rate:.2f}% {bounce_status}")
            print(f"  Complaint Rate: {complaint_rate:.3f}% {complaint_status}")

            if bounce_rate >= 5:
                print("  ⚠️  WARNING: Bounce rate exceeds AWS threshold (5%)")
            if complaint_rate >= 0.1:
                print("  ⚠️  WARNING: Complaint rate exceeds AWS threshold (0.1%)")
    else:
        print("\nNo sending statistics available yet")

    # Check if in sandbox
    # Note: There's no direct API to check sandbox status, but we can infer
    if quota['Max24HourSend'] == 200:
        print("\n⚠️  SES appears to be in sandbox mode (200 email limit)")
        print("   Production access required for higher limits")

    return True
