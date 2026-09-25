# The review wizard (`--wizard`)

Invoke the skill `mattpocock-skills:wizard` and follow its process, with these
fixed inputs. They replace its own scoping questions: the user already confirmed
the test brief in step 3, which counts as its step-1 confirmation.

| Wizard input | Value for a review |
|---|---|
| Path | `~/.local/state/tilt-env/review-wizard.sh` — outside every repo; `tilt-review.py restore` deletes it |
| Results file | first line below the `STAGES` marker: `ENV_FILE="$HOME/.local/state/tilt-env/review-results.env"` — the library reads `ENV_FILE` at call time |
| Stages | one stage for the manual Data steps from step 5 (omit it when there are none), then one stage per test step, grouped by PR in brief order |
| Captured values | per test step, a **result** and a note — plain `ask`; nothing is secret and nothing goes to GitHub, so no `ask_secret`, `set_secret` or `set_var` |

## A test-step stage

```bash
stage "PR 855 · 2/4 · Express verdict carries the delivery date"
open_url "http://localhost:3000/checkout"
step "Add the Form 4 sample part, choose Express shipping"
say  "Working: the verdict shows 'Delivered by <date>' under the Express option"
note "Not working? tilt logs form-now-ecommerce-backend | tail -100"
until [[ "${PR855_STEP2:-}" =~ ^(pass|fail|skip)$ ]]; do
  ask PR855_STEP2 "Result — pass / fail / skip:"
done
write_env PR855_STEP2 "$PR855_STEP2"
ask PR855_STEP2_NOTE "What did you see? (Enter for nothing)"
write_env PR855_STEP2_NOTE "$PR855_STEP2_NOTE"
```

- Keys are `PR<number>_STEP<n>` and `PR<number>_STEP<n>_NOTE`; step 8 reads them back.
- The `say` line is the brief's "working looks like" for that step, word for word.
- Put a `confirm` gate before any step that destroys data (cancelling an order,
  deleting a record) — the wizard skill's rule for irreversible actions.

## Verify

The wizard skill's step 4 applies. Done when `bash -n` passes, `shellcheck` is clean
where installed, and a static trace shows every test step of the guide writes both
of its keys.
