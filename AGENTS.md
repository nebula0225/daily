# daily

Selenium script that logs in to several Korean sites once a day, does the attendance check, and sends one Telegram summary. Windows, Chrome, run by `daily.bat` through `.venv`.

## Layout

- `daily.py`: everything. Telegram report helpers, alert helpers, one `async def` per site, `SITES`, `run_site`, `main`.
- `common.py`: small JSON/dir helpers.
- `personal.json`, `telegram.json`: credentials. Gitignored. Never print their values, never commit them.
- `log/`: daily log files (`*.txt`, gitignored, created at startup).
- `requirements.txt`: tracked through a `!requirements.txt` exception because `.gitignore` ignores `*.txt`.

## How a run works

- `main()` loops over `SITES`, a list of `(personal.json key, site function)`.
- `run_site()` opens a fresh browser for each site and closes it afterwards, so a second account (`inven2`, `item_mania2`) never runs on the first account's session.
- A site function is `async def f(driver, id, pwd)`. It returns the result text for the report (or `None`) and raises to fail.
- Result status: `OK` (no exception), `FAIL` (exception; a screenshot is attached), `SKIP` (no entry in `personal.json`).
- `OK` only means the flow finished. Whether attendance really happened is judged from the result text.
- `send_report()` sends failure screenshots silently, then a single HTML summary. It is the only place that talks to Telegram and it never raises, so a Telegram outage cannot block attendance.

## Rules that are easy to break

- Never run `daily.py` or log in with the real accounts to test something unless the user says so. Attendance is once per day per account, and a test run consumes it. Looking at public pages without logging in is fine.
- After a click that makes the site show an alert, send no other WebDriver command before `read_alert()` / `expect_alert()`. ChromeDriver closes an unhandled alert on the next command and raises `UnexpectedAlertPresentException`, and the result text is lost.
- `implicitly_wait` is set in every site function. Do not add explicit element waits on top of it. Alert waits are fine.
- The `time.sleep` calls after login and navigation are settle time. Do not remove them without checking against the live site.
- Retry loops use `for attempt in range(MAX_RETRIES + 1)` and re-raise the last error. Do not bring back `while 1`.
- Do not classify success or failure by guessed keywords. Only alert texts that were actually observed may be used. So far that is one: ItemMania shows `로그인 후 이용하세요` when not logged in.
- Escape every dynamic value that goes into the HTML summary.
- The Telegram summary is one message per run. Do not add per-site or start/end messages.

## ItemMania notes

- PC attendance requires the "바로접속ON" state. The script gets it by opening the URL the site's own "add to favorites" button saves (`counter/survey.php?imcounter=dot_bookmark_com`) before login. That URL sets the `counterIDX` cookie.
- The attendance button is `[data-event="1"]`. The site answers a click with `alert(msg)`, and that text is the result.
- The login form is `form[name="g_LOGIN_FORM"]`.
- Whether a logged-in session is actually treated as "바로접속ON" has not been confirmed. The result alert text of a real run is the evidence to look for.

## Verifying changes

There is no test suite in the repo. What has worked:

- `python -m py_compile daily.py common.py`.
- A fake driver object for flow logic such as retries and status handling.
- Real headless Chrome against local mock pages, with `driver.get` remapped to the mock URLs.
- Real headless Chrome against the public pages without logging in, to check selectors.

Check selectors in a real browser. Parsing downloaded HTML with a static parser gave a different element path than the rendered page.

Say plainly which of these were done. A mock-page run proves the code, not the site.

## Not verified yet

- Logged-in behavior of every site, including the ItemMania result text and whether its notice popup appears.
- The alert texts of ondisk, yesfile and filebogo.
- Real Telegram delivery.

## Known gaps

- `login_filenori` is unfinished and not in `SITES`.
- ondisk discards the alert shown right after the login click, so a login failure there is not reported.
- Fixed sleeps make a run slow.

## Git

- Commits go directly on `main`.
- Commit finished, verified work without asking for approval first. The user granted this for this project on 2026-10-04. It covers commits only; push when asked.
- Split unrelated changes into separate commits.
- Commit messages are in English, in the form `daily.py: what changed`.
- No AI attribution trailers.
