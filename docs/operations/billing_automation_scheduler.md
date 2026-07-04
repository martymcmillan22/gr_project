# Billing Automation Scheduler

Use the management command below to queue and process billing operational automation jobs on a schedule.

## Command

```bash
./a_gr_venv/bin/python manage.py run_billing_automation --tenant=default --client=all --limit=50
```

Optional flags:

- `--queue-only`: queue an automation job but do not process pending jobs.
- `--window-days=30`: include desired analytics window in payload.
- `--schedule-hint=hourly`: stores scheduling intent in queued payload.

## macOS launchd (hourly)

1. One-command install (writes plist, loads it, and starts it):

```bash
./scripts/operations/install_billing_automation_launchd.sh
```

2. Manual reference plist is available at [com.grassroots.billing-automation.plist.example](./com.grassroots.billing-automation.plist.example).

3. Verify:

```bash
launchctl list | grep com.grassroots.billing-automation
```

4. Check logs:

```bash
tail -n 200 /tmp/grassroots-billing-automation.log
tail -n 200 /tmp/grassroots-billing-automation.err.log
```

5. Uninstall if needed:

```bash
./scripts/operations/uninstall_billing_automation_launchd.sh
```

## Cron fallback

If launchd is not preferred:

```cron
0 * * * * cd /Users/martymcmillan/Desktop/GrassRoots && /Users/martymcmillan/Desktop/GrassRoots/a_gr_venv/bin/python manage.py run_billing_automation --tenant=default --client=all --limit=50 >> /tmp/grassroots-billing-automation.log 2>&1
```

## Dry run pattern

Use queue-only for a safe first check:

```bash
./a_gr_venv/bin/python manage.py run_billing_automation --tenant=default --client=all --queue-only
./a_gr_venv/bin/python manage.py run_billing_automation --tenant=default --client=all --limit=50
```
