# Manual setup and verification

Documentation review date: 2026-10-25. Native account setup, upload and model
behavior: PENDING, not live-tested. This package grants no native account access.

## Claude custom skill

Enable Code execution and file creation where permitted. Use
Customize > Skills > + > + Create skill > Upload a skill and upload the Claude
ZIP containing the single atlas-marketing-team/ folder. Toggle the skill on.
Organization policy can disable skill creation/execution. Check the current UI
and permissions; this ZIP is not an installer. Optional Python commands run from
inside the extracted atlas-marketing-team/ root and need Python 3.9+ execution.

## ChatGPT skills-only plugin

The plugin ZIP has root plugin.json using Agent Plugins schema 1.0.0 and discovers
the skill under skills/atlas-marketing-team/. It has no MCP configuration, app
connections, hooks, account adapters or credentials. It does not require an MCP
server. Optional helper execution depends on actual runtime tools; use built-in
web tools or bundled methods otherwise.

Where available on ChatGPT web, an eligible owner/admin with upload permissions
uses Admin console > intended workspace > Plugins > Add > Upload plugin. Other
surfaces/roles may differ; availability depends on current account/workspace
settings. Review scan findings and test the installed package before sharing.
Dragging a ZIP into an ordinary chat is not permanent skill/plugin installation.
This is a draft package, not an OpenAI-verified or publicly published plugin.

## ChatGPT Project fallback (manual text workflow)

Unzip locally. Paste PROJECT_INSTRUCTIONS.md into the Project instructions;
upload PLAYBOOK.md and your separately filled CLIENT_CONTEXT.md as Project files.
The playbook compiles the same canonical director and resources, with source-path
section headings. Keep only one active playbook revision; manually manage visible
inputs, output IDs and approvals. Do not upload a competing legacy role kit.
This route is not a native plugin install and includes no executable package.
No auto-learning, cross-chat state sync, publishing or client isolation guarantee.

## Acceptance checks after setup

In a clean session request one concrete output, then a different task type.
Confirm adaptive stages, actual discovery or LIVE_SEARCH_UNAVAILABLE, selected
methods used in complete outputs, source/version citations, QA and DRAFT/unpublished
status. Inspect real tool logs rather than assuming the helper ran. Test in the
user's language. Record actual outputs and deviations. Installation, model
adherence and cross-conversation reuse remain PENDING until observed.

## Official references reviewed

- https://support.claude.com/en/articles/12512180-use-skills-in-claude
- https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
- https://developers.openai.com/plugins/build/plugins
- https://help.openai.com/en/articles/20001256-plugins-in-chatgpt
- https://help.openai.com/en/articles/20001066-skills-in-chatgpt
- https://agent-plugins.org/schemas/1.0.0/plugin.schema.json

These sources document packaging/UI requirements, not successful live acceptance
of this artifact. Recheck changed platform behavior before installation.
