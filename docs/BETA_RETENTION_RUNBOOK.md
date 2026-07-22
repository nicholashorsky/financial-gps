# Synthetic Beta Retention Runbook

This runbook implements the retention boundary in the [Beta Data and Storage Policy](BETA_DATA_POLICY.md). It applies only to fictional beta data.

## Current limitation

Financial GPS records account creation time but does not record last login. Therefore, the 90-day inactive-account policy is a **manual review**, not an automated deletion rule. Do not infer inactivity from account age alone.

Until activity tracking is introduced, review accounts created more than 90 days ago, confirm status through the private tester channel, and delete only accounts confirmed inactive or explicitly requested for deletion.

## Tester-requested deletion

The preferred method is tester self-service through **Settings → Delete beta account**. It deletes the authenticated user row, and SQLite foreign-key cascades remove associated application records.

If self-service is unavailable:

1. Verify the request through the tester's private invitation channel.
2. Resolve the exact user ID without sharing account information publicly.
3. Stop writes or place the app in maintenance mode.
4. Create a protected matching backup only when retention is justified.
5. Delete the exact user row in a transaction and verify no user-owned rows remain.
6. Record the date and outcome without copying transaction details.
7. Remove applicable backups on their retention schedule where practical.

Never delete by an unverified display name, broad wildcard, or unresolved environment variable.

## Scheduled review

Review the invited tester list monthly:

* Confirm which accounts are still active through the private tester channel.
* Remove accounts confirmed inactive after 90 days.
* Resolve deletion requests promptly.
* Check that backups are protected and no longer retained than needed.
* Confirm uploaded source CSV files are not being stored.

## End of synthetic beta

No later than 30 days after the beta ends:

1. Stop new tester access.
2. Export only non-sensitive aggregate findings needed for product decisions.
3. Delete tester accounts and the active SQLite database.
4. Delete associated backups where practical.
5. Verify the public repository contains no database, secret, or uploaded CSV artifact.
6. Record completion in the project issue without including tester data.

Application rollback and protected backups remain governed by the deployment record and Beta Data and Storage Policy.
