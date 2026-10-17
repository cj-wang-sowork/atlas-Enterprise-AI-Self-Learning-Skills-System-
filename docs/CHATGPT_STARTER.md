# ChatGPT Starter Kit — first task and manual review

**For non-engineers:** use the four text files in
[`starter/chatgpt/`](../starter/chatgpt/README.md). No terminal, Python,
API key, runtime installation, or upload of the whole repository is required.
The aim is one useful draft plus one reviewed lesson in about **10 minutes**.
That is a design target, not a timed user study or a guarantee. Live ChatGPT UI
setup has **not** been verified for this release.

## What this route is (and is not)

A ChatGPT Project can organize instructions and supplied context. You manually
add the kit text, inspect the draft, and decide which lessons to retain. Consult
[OpenAI's Projects guide](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)
for current UI steps, availability, sharing, memory, and limits; account or
workspace settings can change what you see. The instructions below are manual
guidance, not a claim of completed UI automation.

This is **not** a native ChatGPT shell installer, a connection to a local ATLAS
workspace, or a backend access-control/automatic-learning integration. Copying
a code block does not execute it on your computer. Project memory/context is not
ATLAS's reviewed learning/promotion lifecycle. Prompt rules are not an
authorization or tenant-isolation boundary.

## A short first-use path

### 1. Get the files

On the repository's GitHub page, choose **Code → Download ZIP**, unzip it, then
open `starter/chatgpt`. Use a clean repository download, not a coworker's
personalized workspace. Start with the fictional sample only.

| File | What to do with it |
| --- | --- |
| `README.md` | Read the quick steps and copy the first task prompt |
| `PROJECT_INSTRUCTIONS.md` | Copy the text into the Project's instructions |
| `SAMPLE_BRIEF.md` | Upload as context or paste its text into the project chat |
| `OUTCOME_REVIEW_LOG.md` | Copy locally; fill in after reviewing the output |

Do **not** upload `MEMORY.md`, `TOOLS.md`, `memory/`, `outputs/`, raw chats,
API keys, private client material, or the entire repository. Remove private
information before using your own brief and inspect actual project sharing and
data controls. A sentence saying “private” does not enforce privacy.

### 2. Create the Project and set instructions

In ChatGPT, create a new Project such as “ATLAS practice”. Open its options and
Project settings. Paste `PROJECT_INSTRUCTIONS.md` into the instructions field.
Uploading it as an ordinary file is not the same as setting project instructions.
If Projects/settings are unavailable, consult OpenAI's guide or your workspace
administrator. You can paste the sanitized brief and rules into one chat as a
fallback, but that is chat-local context, not verified saved Project setup.

### 3. Add the fictional brief and ask for a draft

Upload `SAMPLE_BRIEF.md` or paste its contents, then start a chat **inside that
Project** and send:

> Use the supplied fictional sample brief. Draft a 120-word launch email.
> Separate supplied facts from suggestions. List missing facts instead of
> inventing them. Do not claim you sent the email. Finish with one candidate
> lesson for my review, not an automatic memory update.

Check that the response uses the worksheet sections in the sample, avoids
inventing a price/date/download URL or customer results, and is clearly a draft.
Ask it to fix deviations before accepting the result. The human, not a generated
claim of success, decides whether the task meets its acceptance criteria.

### 4. Record the actual outcome and review the candidate lesson

Fill in your local copy of `OUTCOME_REVIEW_LOG.md`: output reference, what you
checked, evidence, remaining errors, candidate rule, audience, and a human
**Accept / Revise / Reject / Defer** decision. A single example is limited evidence;
do not turn it into an unsupported universal rule. Rejecting a weak lesson is a
valid outcome. No decision means no approval.

### 5. Manually retain only approved context

After approval, paste the corrected, sanitized lesson into Project instructions
or add a reviewed reference file yourself. Record where you put it and verify
the intended version is visible. Remove/replace obsolete uploads or instructions.
For the next task, explicitly ask ChatGPT to use that approved rule, then inspect
whether it actually did. This is manual context maintenance, not a claim of
model training, backend registry mutation, or automatic cross-session learning.

## Optional local export (terminal users only)

From an existing repository checkout:

```bash
./scripts/install-workspace.sh --target chatgpt --dest ~/Documents/atlas-chatgpt-kit
```

This copies only the four text files. Existing kit files get collision-resistant
sibling backups unless you explicitly pass destructive `--force`. It does not
log into ChatGPT, create a Project, upload files, or run backend Python. `all`
installs local runtime context, including kit reference files inside its workspace
bundles, but does not create a standalone kit destination or configure ChatGPT.

## What was verified

The sandbox installer tests verify export contents, repeated installs/backups,
and rejection of unsafe paths. They do not verify a logged-in ChatGPT session,
account-specific UI, actual model adherence, memory recall, or elapsed setup time.
Use the human checks above for your account. The current official help page was
available through search excerpts during preparation; a full-page/live UI
verification was blocked, so this guide deliberately avoids plan-specific limits
or claims of a completed live setup.

For executable backend boundaries and evidence, see
[ACCESS_CONTROL.md](ACCESS_CONTROL.md),
[LEARNING_LIFECYCLE.md](LEARNING_LIFECYCLE.md), and
[VERIFICATION.md](VERIFICATION.md). Those capabilities are not activated by
this manual kit.
