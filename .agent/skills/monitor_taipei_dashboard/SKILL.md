---
name: Monitor Taipei City Dashboard
description: A skill to monitor the Taipei City Dashboard website and backend server health.
---

# Monitor Taipei City Dashboard

This skill provides instructions for an agent to check the health of the Taipei City Dashboard website and its backend server.

**⚠️ IMPORTANT SECURITY WARNING ⚠️**
You must **STRICTLY FOLLOW** these instructions:
1.  You are **ONLY** allowed to execute the specified script (`monitor_dashboard.sh`).
2.  You are **FORBIDDEN** from executing any other SSH commands, `docker` commands, or system management commands manually.
3.  All system check logic is encapsulated within the automation script.

## 1. Website Health Check

**Goal**: Verify that the "Metro Passenger Traffic Trends" chart is displaying data correctly.

**Steps**:
1.  **Navigate**: Use the `browser_subagent` tool to visit `https://citydashboard.taipei/dashboard?index=metro&city=taipei`.
2.  **Verify**:
    -   Wait for the page to load completely.
    -   Look for the section titled "捷運人流趨勢" (Metro Passenger Traffic Trends).
    -   Check if the chart is visible and not empty.
    -   Check for any visible error messages on the page.
3.  **Report**:
    -   If the chart is visible and looks normal, report "Website Check: OK".
    -   If there are issues (empty chart, error messages, page not loading), capture a screenshot and report "Website Check: FAILED" with details.

## 2. Server Health Check (Automated Script Only)

**Goal**: Verify backend server status by executing the ONLY permitted script.

**Steps**:
1.  **Execute Monitoring Script**:
    -   Use the `run_command` tool to execute:
        ```bash
        # If password is required (and SSH_PASSWORD env var is set)
        export SSH_PASSWORD='your_password' # (Skip if already set globally)
        ./monitor_dashboard.sh
        ```
    -   **Note**: The script handles SSH connection, Docker container status checks (including filtering rules), log fetching, and disk usage checks automatically.

2.  **Analyze Output**:
    -   The script will output detailed check results.
    -   If the script returns an error or shows `[ALERT]` / `[WARNING]`, quote the logs or error messages from the script output directly.

3.  **Prohibitions**:
    -   ❌ **DO NOT** attempt to SSH into the server to debug manually.
    -   ❌ **DO NOT** execute `docker ps` or `docker logs` manually (the script does this).
    -   ❌ **DO NOT** execute any other unauthorized commands.

## 3. Final Summary

Combine findings from the Website Check (Browser) and Server Check (Script Output) into a concise report for the user.
