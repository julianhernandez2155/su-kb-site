---
title: "Hermes Agent: What It Is and How to Approach It Safely"
description: Explains what the open-source Hermes Agent is, the security model you take on by running it, and the precautions students should follow, including keeping it away from university accounts and data.
department: data-ai
last_modified: 2026-06-08
tags: [ai-agents, security, data-privacy, third-party-tools]
audience: [students]
origin: native
visibility: public
---

Hermes Agent is a popular open-source AI agent that students may run into and want to experiment with. This page explains what it is, how it differs from assistants like Claude or Copilot, and the security realities you accept the moment you run it, so you can decide whether and how to try it without putting yourself or the university at risk.

---

## What is Hermes Agent

Hermes Agent is an open-source autonomous agent built by Nous Research and released in February 2026 under the MIT license. Unlike a chat assistant you open in a browser, it runs as an always-on background process (a daemon) on a computer or server you control. It keeps memory across sessions, runs scheduled jobs on a timer (cron), connects to messaging apps such as Telegram, Discord, Slack, and WhatsApp, and can write its own reusable "skill" files so it gets more capable the longer it runs. It is provider-agnostic: you point it at a language-model backend (Anthropic, OpenAI, Google, OpenRouter, a Nous subscription, or a local model). It needs a Unix-like environment, so on Windows you have to install WSL2 and run it from inside that.

The distinction that matters: Claude and Copilot are assistants you prompt one message at a time. Hermes is an agent you deploy. It has a terminal, file access, and the ability to act on a schedule without you watching. That capability is both the appeal and the entire risk.

---

## Why students are interested

The draw is real. Hermes gives you persistent memory so you stop re-explaining context, automation that runs while you sleep, a single agent reachable from the messaging app you already use, and all of it free and self-hosted. For anyone studying AI agents, systems administration, or security, it is a legitimate hands-on learning platform, not a toy. The same features that make it useful are exactly the ones that make it dangerous if you run it carelessly, which is the rest of this page.

---

## The security model you are accepting

> [!warning] You are running a program that can act on its own
> Running Hermes means running software that can execute shell commands, read and write files, reach the internet, and take scheduled actions on your behalf, continuously. Treat the machine it runs on as fully exposed to it.

### It is permissive by default

An independent security audit of an earlier release found no malware and no hidden data exfiltration, but it concluded that the out-of-the-box posture is allow-all, which is risky for anyone who does not know to harden it. Authorization is binary: an authorized user gets full terminal, file-write, and scheduling access, and there is no built-in tier that grants someone "read-only" or "chat-only" use. There are also per-platform flags that authorize every user at once, and a "YOLO" mode that auto-approves every command it wants to run. Set command approval to manual, and never turn on auto-approve on a machine you care about.

### The only real boundary is your user account

Nous Research's own security policy is explicit that the load-bearing boundary is the host operating system account Hermes runs as: its file permissions and what that account is allowed to reach. The in-process checks (command pattern-matching, prompt-injection scanning of context files) are helpful, but the project does not treat them as guarantees. The practical consequence is that you should run Hermes as a low-privilege user in an isolated environment, a dedicated virtual machine, container, or WSL2 distribution, and never as an administrator or root account on your daily computer. Assume that anything that account can touch, the agent can touch.

### The agent writes its own skills, and that is an attack surface

The audit flagged that skill files the agent creates persist and get loaded into future sessions, which makes them a durable prompt-injection vector, and that the guard screening those files is pattern-based and tends to "ask" rather than "block" on agent-written content. In plain terms, content the agent reads today (a web page, an email, a file you hand it) can plant instructions that fire later. Review any skills it writes, and be careful about pointing it at content you do not trust.

### Windows users silently lose a layer

One of Hermes's command-screening tools (called tirith) does not run on native Windows and is skipped without showing you a warning. The documented fix is to run Hermes under WSL2, which it requires anyway. If you are on Windows, use WSL2, both because Hermes needs it and because skipping it quietly disables a safety check you would otherwise have.

---

## If you want to try it safely

> [!note] Treat this as a checklist, not a suggestion
> Hermes is only as safe as the environment you put it in and the limits you set. The defaults will not protect you.

1. **Use a throwaway, isolated host.** A dedicated virtual machine, a cheap cloud instance, a container, or a WSL2 distribution. Do not run it in your primary operating-system account, and never as administrator or root.
2. **Run as a low-privilege user.** The OS account is the real boundary, so give it the least access it needs to do what you are testing.
3. **Set approvals to manual and leave auto-approve off.** Review commands before they run, especially while you are still learning what it does.
4. **Set an allowlist.** Network-connected adapters should refuse to act until you tell them who is allowed. Lock messaging access to your own user ID only.
5. **Protect your credentials.** Keep the configuration and secrets file readable only by you (`chmod 600`), use a separate API key per service, and never commit secrets to a git repository.
6. **Never grant send or delete authority you would not give a stranger.** For email or messaging, configure it to draft actions for your review rather than executing them.
7. **Keep its data off synced folders.** Background file-sync services like OneDrive or Dropbox fight a daemon over file locks and can corrupt the agent's state. Store its data on the local filesystem.
8. **Back up its state, and treat that backup as a secret too.** It can contain tokens and personal context.

---

## Do not connect it to university accounts, data, or systems

> [!warning] This is the hard line for Syracuse students
> Hermes is not an approved tool for use with university data, and its allow-all, single-boundary design is the opposite of what handling protected information requires.

Do not authenticate Hermes with your NetID or any Syracuse account. Do not give it access to university email, files, Teams, or any other SU system. Do not run it on university-managed or university-owned hardware. Keep your experimentation on personal accounts and personal hardware, fully separated from anything connected to Syracuse.

If you have a legitimate academic or research reason to run an autonomous agent against any university resource, that decision goes through SU IT and the approved-tools process first, not the other way around. See [Approved Tools for Use with University Data](approved-tools-for-use-with-university-data.md).

---

## Keep in mind

- **You are the security boundary.** Hermes is as safe as the environment you give it and the limits you set, not as safe as its defaults.
- **Verify before you trust.** It can act on bad or injected instructions, so review what it does, especially anything it scheduled or any skill it wrote for itself.
- **Personal and university stay separate.** Nothing connected to Syracuse should touch Hermes, and nothing Hermes touches should go near your Syracuse credentials.

---

## Support

Need help? **ITS Help Desk**: 315-443-2677 · [help@syr.edu](mailto:help@syr.edu)
