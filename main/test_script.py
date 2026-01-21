element = """Date: Mon, 28 Apr 2025 08:02:50 +0000 (UTC)
From: HDFC Bank Alerts  <alerts@hdfcbank.net>
Subject: Missed Call from your HDFC Bank Relationship Manager - SOURISH
 CHATTERJEE"""

if len(element.strip()) > 0:
    print(element)
    key, value = element.split(':',1)
    print(key.strip())
    print(value.strip())
