---
name: gemlogin-facebook
description: Build, test, and debug Facebook sharing and group-post link collection workflows in GemLogin. Use for profile/page switching, profile or group sharing, Public-audience recovery, collecting the latest published post link from a group, resilient Facebook selectors, and saving post permalinks to a Text file.
---

# GemLogin Facebook

Use this skill with `$gemlogin` for live Facebook browser testing and `$gemlogin-edit` for DB-backed workflow changes. Keep Facebook-specific selectors and recovery paths here; keep SQLite editing mechanics in `$gemlogin-edit`.

## Workflow rules

1. Inspect the live DOM before choosing an XPath. Scope selectors to the active dialog/post and avoid page-wide indexes such as `(//...)[last()]`.
2. Prefer native GemLogin blocks for Facebook UI clicks. Use JavaScript only for DOM inspection, variable assignment, and reading values.
3. Do not use `document.body.click()` or JavaScript `.click()` for Facebook menus in production workflows; this caused GemLogin runtime errors such as `Cannot read properties of undefined (reading 'insert')`.
4. After a share, refresh the destination feed once, wait for the refreshed page, then locate the newest post by the caption before collecting its link.
5. Every critical Facebook action needs a labelled fallback edge. Keep main and fallback rows visually separate.

## Collect latest post link from a group

Use this pattern for workflow `[FB] Collect Link post from group` when the goal is to collect an existing post link, not create another share:

```text
read-file-text (group UID)
  -> validate numeric UID + build group URL
  -> open group
  -> wait for group
  -> Manage posts / Manage your content
  -> Published
  -> View in group
  -> wait
  -> tab-url
  -> validate + normalize multi_permalinks URL
  -> file-action append/newLine
```

Trigger parameters:

- `groupUidFilePath`: `filepath`, a Text file containing one numeric Facebook Group UID
- `postLinkFilePath`: `filepath`, the output Text file for appending the collected link

When adding or changing either parameter, update both `script.trigger.parameters` and `script.drawflow.nodes[trigger-node].data.parameters`.

Use native GemLogin blocks for the Facebook clicks. Main selectors and the observed fallback pairs are:

```xpath
//*[self::a or self::button or @role='button'][normalize-space(.)='Manage posts']
//*[self::a or self::button or @role='button'][contains(normalize-space(.),'Manage your content')]
//*[self::a or self::button or @role='button'][normalize-space(.)='Published']
//a[normalize-space(.)='Published']
//*[self::a or self::button or @role='button'][normalize-space(.)='View in group']
//*[self::a or self::button or @role='button'][contains(normalize-space(.),'View in group')]
```

Keep the UID at the trust boundary. Read and trim the file value, reject anything that is not digits-only, then build `https://www.facebook.com/groups/<uid>`. Do not interpolate unvalidated file content into the URL.

After `View in group`, read the active tab URL. Require the `multi_permalinks` query parameter; reject the result if it is missing or if the page is not a group-post URL. Normalize and save only the clean group path plus the `multi_permalinks` value, then use `file-action` with `writeMode: append` and `appendMode: newLine`.

This is a single-pass collector: do not add a loop unless the user explicitly wants to process multiple UID lines. It must not run share actions, so a retry cannot create duplicate posts. JavaScript is limited to UID validation, URL normalization, and variable assignment.

## Profile and Page switching

- Open `https://www.facebook.com/profile` to inspect the active identity first.
- For a page, open `https://www.facebook.com/profile.php?id={{variables.pageUid}}`, then click the live `Switch Now` button.
- For returning to a personal profile, open the profile switch menu, capture the visible personal name, and click the button whose aria-label is `Switch to <captured name>`; do not hard-code a person's name.
- Keep `usePersonalProfile` and `usePageProfile` as checkbox parameters. When adding inputs, update both `script.trigger.parameters` and `script.drawflow.nodes[trigger-node].data.parameters`.

## Share and Public recovery

- Scope the source Share button to the current permalink/story rather than selecting a broad global Share button.
- In the profile share dialog, verify Public with:

  ```xpath
  //div[@role='button' and starts-with(@aria-label,'Edit privacy. Sharing with Public')]
  ```

- If that check falls back, use native Event Click blocks in this order:

  ```text
  Edit privacy. Sharing with -> Public -> Done with privacy audience selection and close dialog -> verify Public again
  ```

  Selectors observed in the live UI:

  ```xpath
  //div[@role='button' and starts-with(@aria-label,'Edit privacy. Sharing with')]
  //div[@role='dialog']//span[normalize-space(.)='Public']
  //div[@role='button' and @aria-label='Done with privacy audience selection and close dialog']
  ```

- Use `//div[@role='button' and @aria-label='Share now']` only inside the active share dialog.
- For group sharing, scope the group selector to the configured group name and verify the selected Public group before posting.

## Permalink report

- Add a manual trigger parameter with `type: filepath` for the output `.txt` file. Keep it synchronized in both trigger parameter locations.
- Use `file-action` with `writeMode: append` and `appendMode: newLine`.
- The reliable Facebook link path is:

  ```text
  share/post -> open active profile or stay on group page -> reload tab -> wait -> Actions for latest captioned post -> Embed -> read plugins/post.php input -> file-action
  ```

- Use native Event Click for `Actions for this post` and `Embed`; use a small synchronous JavaScript block only to read the Embed input and set `sharedPostLink`.
- Extract the decoded `href` from the Embed iframe and require `permalink.php` before writing it. Never report the profile URL as the post URL.

## Verification checklist

- Test with a real GemLogin profile and record the active identity (personal or page).
- Confirm the audience label is Public before clicking Share now.
- Confirm the new post contains the requested caption and the success toast or visible post.
- Confirm the report file receives a decoded `https://www.facebook.com/permalink.php?...` URL.
- For `[FB] Collect Link post from group`, confirm the input UID is numeric, the group page opens, the newest Published post opens through `View in group`, the URL contains `multi_permalinks`, and the output file receives one appended group-post link.
- Run one controlled test with a disposable output file before treating a new collector as production-ready.
- Stop the test browser profile when finished unless the user explicitly asks to keep it open.
