# MyTodo — Development Workflow

## The two folders

| Folder | Branch | Purpose |
|---|---|---|
| `mytodo/` | `main` | Stable. Run this for personal use. |
| `mytodo-dev/` | `dev` | Development. Build new features here. |

Both folders are checkouts of the **same git repository**. They share history — there is no duplication. Each has its own independent `.mytodo.toml` data file.

---

## Scenario: I want to develop a new feature

1. Open `mytodo-dev/` in your editor.
2. Build and test the feature there. Run the app with `python3 main.py` from that folder.
3. Commit your changes from `mytodo-dev/` as usual:
   ```bash
   git add <files>
   git commit -m "Description of feature"
   ```
4. Push the `dev` branch if you want it backed up on GitHub:
   ```bash
   git push origin dev
   ```

Your `mytodo/` folder (on `main`) is completely untouched throughout.

---

## Scenario: The feature is ready — I want to move it to the stable folder

This is called merging. You bring the commits from `dev` into `main`.

1. Make sure all your work in `mytodo-dev/` is committed (no unsaved changes).
2. Open a terminal in the **stable folder** (`mytodo/`).
3. Run:
   ```bash
   git merge dev
   ```
4. That's it. `mytodo/` now has the new feature. Run `python3 main.py` from there to verify.
5. Optionally push `main` to GitHub:
   ```bash
   git push origin main
   ```

> **Data files are not affected by merges.** Each folder keeps its own `.mytodo.toml`. Merging only moves code.

---

## Scenario: The merge went wrong — I want to undo it

### If the merge produced conflicts and hasn't completed yet:
```bash
git merge --abort
```
This cancels the merge entirely and leaves `main` exactly as it was.

### If the merge completed but the result is broken:
```bash
git reset --hard HEAD~1
```
This rewinds `main` by one commit, undoing the merge. Your `mytodo-dev/` folder and the `dev` branch are unaffected — you can fix the issue there and try again.

### If you're not sure how many commits to rewind:
```bash
git log --oneline -10
```
This shows the last 10 commits with their hashes. Find the last good commit, then:
```bash
git reset --hard <hash>
```

---

## Scenario: I want to start a brand-new feature from scratch (not continuing dev)

If `dev` has accumulated messy or half-finished work and you want a clean slate:

1. From `mytodo/` (on `main`):
   ```bash
   git worktree remove ../mytodo-dev   # remove the old dev folder
   git branch -D dev                   # delete the old dev branch
   git worktree add ../mytodo-dev -b dev  # create a fresh one from current main
   ```
2. Copy your data file across if needed:
   ```bash
   cp .mytodo.toml ../mytodo-dev/.mytodo.toml
   ```

---

## Day-to-day rules of thumb

- **Run the app for personal use** → always from `mytodo/`
- **Write new code** → always in `mytodo-dev/`
- **Commits on `dev`** → don't affect `main` until you merge
- **Commits on `main`** → don't automatically appear in `mytodo-dev/`; pull them in with `git rebase main` or `git merge main` from the dev folder if needed
- **Data files are independent** — changes to one folder's `.mytodo.toml` never affect the other
