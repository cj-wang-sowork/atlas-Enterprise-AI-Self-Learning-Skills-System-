# ATLAS ChatGPT Starter Kit — manual setup

This is a small set of text files for a ChatGPT Project. No terminal, Python,
API key, connector, or repository upload is needed. Download this repository's
ZIP from its GitHub page, unzip it, and open `starter/chatgpt`.

## Start here

1. In ChatGPT, create a **New project**, for example “ATLAS practice”. If your
   account does not show Projects, check your workspace policy and OpenAI's guide.
2. Open the project's settings and paste the contents of
   `PROJECT_INSTRUCTIONS.md` into its instructions field. A file upload alone is
   not the same as setting project instructions.
3. Add `SAMPLE_BRIEF.md` as a project file, or paste its text into a project chat.
   Use this fictional brief first; do not upload private workspace files.
4. Paste this first task into a chat **inside that project**:

   > Use the supplied fictional sample brief. Draft a 120-word launch email.
   > Separate supplied facts from suggestions. List missing facts instead of
   > inventing them. Do not claim you sent the email. Finish with one candidate
   > lesson for my review, not an automatic memory update.

5. Check the draft against the brief yourself. Copy `OUTCOME_REVIEW_LOG.md` to a
   local working file, fill in your decision and evidence, and retain it locally.
   Only after review, manually paste an approved, sanitized lesson into project
   instructions or add a reviewed reference file. Remove or replace obsolete
   uploads rather than leaving conflicting versions in the project.

Aim: a first draft and one human-reviewed lesson in about 10 minutes. This is a
setup goal, not a measured usability result or a guarantee; login, availability,
and review can take longer. No actual ChatGPT UI end-to-end test is claimed.

## Boundaries

- The kit does not run `install-workspace.sh` or any local shell/Python code in
  ChatGPT. A code block in a chat is not execution on your computer.
- It does not connect to ATLAS's backend, enforce its access policy, or run its
  learning/promotion pipeline. All lesson acceptance here is manual.
- Project memory is a ChatGPT feature governed by your account settings, not the
  ATLAS lifecycle. Do not equate recalled context with a reviewed/approved lesson.
- Prompt rules are not an authorization boundary. Keep secrets, personal memory,
  raw conversations, and another client's information out of uploads. Inspect
  the real account/project sharing and data controls before adding business data.
- If Markdown upload is unavailable, paste the relevant text into the chat.
  This is chat-local context; it is not equivalent to saved project instructions.

Current UI steps, availability and limits: [OpenAI Projects guide](https://help.openai.com/en/articles/10169521-projects-in-chatgpt).
