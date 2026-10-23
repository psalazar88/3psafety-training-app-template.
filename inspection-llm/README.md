# 3P Safety Inspection LLM (self-hosted)

Your own AI for inspection and compliance reports. It runs on hardware you control, uses an open-weight model, and doesn't call any outside AI service.

| Piece | What it is | Where |
|---|---|---|
| **Ollama** | Runs the AI model | Your PC or a GPU server |
| **Open WebUI** | Claude-style chat app: upload photos, chat, knowledge base, user logins | Browser, port 3000 |
| **Rulebook** | How every report must be written: severity scale, structure, "draft only" rules | `rulebook/system-prompt.md` |
| **Reference library** | Standards and good past reports it may cite | `knowledge/` |
| **Customer memory** | Equipment and history per customer, kept separate | `memory/<customer>/` |
| **Test cases** | Past inspections to check it against your real reports | `test-cases/` |

The AI drafts. A certified inspector reviews and signs. That's written into the rulebook and must stay that way.

---

## 1. Pick where it runs

**Option A: Windows PC (start here).** Fine for building and testing with one user. Speed depends on the graphics card or unified memory. The AMD Strix Halo with 128 GB handles mid-size models. A normal office laptop will be slow, but it works for a test.

**Option B: rented GPU server (RunPod or similar).** For real speed, bigger models, or more than a couple of users. Pay by the hour, and shut it off when you're not using it. Uses `docker-compose.yml`.

## 2. Install

### Option A: Windows

1. Install Ollama: https://ollama.com/download. It runs in the background on port 11434.
2. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
3. Start the chat app in PowerShell:
   ```powershell
   docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway `
     -v open-webui:/app/backend/data --name open-webui --restart always `
     ghcr.io/open-webui/open-webui:main
   ```
4. Open http://localhost:3000 and create the admin account. The first account is the admin.

### Option B: GPU server

```bash
git clone <this repo> && cd inspection-llm
docker compose up -d
```
Open `http://<server-ip>:3000`. Put it behind HTTPS and a login before any customer uses it.

## 3. Download a model

The model has to read photos (a "vision" model). Check the current tags on https://ollama.com/library. As of Oct 2026 the leading open vision families are **Gemma 4** and **Qwen3-VL / Qwen3.5**, with Qwen stronger at reading labels, tags and documents.

```powershell
ollama pull qwen3-vl:8b  # fits a 16 GB card; check the exact tag on ollama.com
ollama pull gemma4       # second candidate, to compare
```

Pick a size that fits your memory: roughly the model's download size plus 20–30%.

## 4. Build the 3P inspector model and test it on real jobs

```powershell
cd inspection-llm
powershell -ExecutionPolicy Bypass -File .\scripts\build-model.ps1
```
This bakes the rulebook into a model named `3p-inspector`. The base model is the `FROM` line in `Modelfile`. Re-run the script after any rulebook edit.

**Then test it before trusting it.** This step decides whether the whole idea works:

1. For each of 10–20 past jobs, make a folder in `test-cases/` (copy `_example`) holding the photos, your field notes in `notes.md`, and the report you actually sent as `actual-report.pdf`.
2. If you have customer history, copy `memory/_template` to `memory/<customer>/`, fill it in, and put that folder name in the test case's `customer.txt`.
3. Run it:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\draft-report.ps1 -Case test-cases\<job>
   ```
   It saves `draft-3p-inspector.md` next to your real report.
4. Compare. Did it catch the defects you caught? Did it make anything up? Is the severity right?
5. To try another base model, change `FROM` in `Modelfile`, rebuild, and re-run. Or test a raw model with `-Model qwen3-vl`. The result is saved under a separate file name so you can compare side by side.

If it misses real defects or invents ones that aren't there, fix the rulebook, try a bigger model, or keep the AI to writing up the findings you dictate rather than finding defects itself.

## 5. Use it day to day (Open WebUI)

1. **Workspace → Knowledge:** create a "Standards" collection and upload `knowledge/standards/`. Create a "Report examples" collection from `knowledge/past-reports/`.
2. **Workspace → Models:** pick `3p-inspector` and attach both collections.
3. **Per customer:** create a Knowledge collection per customer from `memory/<customer>/` and attach it only when working that customer's job.
4. Start a chat with `3p-inspector`, drop in photos and notes, and ask for the draft report.

## Photos-only report (mobile crane)

In Open WebUI, pick `3p-inspector`, drag in the photos, and type:

> Make a mobile crane inspection report based on the photos provided.

It identifies what each photo shows and works through the mobile crane checklist (`rulebook/checklists/mobile-crane.md`). Every item is marked OK, Possible defect, or Not visible. It ends with a list of the extra photos it needs. Nameplate text it can't read clearly is marked `[?]`, not guessed.

From the test script, a test case folder with only photos works too:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\draft-report.ps1 -Case test-cases\<job>
powershell -ExecutionPolicy Bypass -File .\scripts\draft-report.ps1 -Case test-cases\<job> -Equipment 'overhead crane'
```

**Photo tips on a 16 GB card:**
- Send 4–6 photos at a time: nameplate, boom, hook block, rope at drum, outriggers, cab/LMI. Then send the next batch in the same chat.
- Use close-ups, one component per photo.
- Add another equipment type by dropping a new checklist (e.g. `overhead-crane.md`) into `rulebook/checklists/` and re-running `build-model.ps1`.

## Memory: how this matches what you do with Claude

With Claude, memory is notes Claude reads before answering. Here it's the same idea, but you own and control the files:

- **Always on:** the rulebook (`rulebook/system-prompt.md`), like your Claude instructions.
- **Per customer:** `memory/<customer>/`, with equipment, history and preferences. Kept separate so customers never see each other's data.
- **Look-up:** the standards and past reports, searched when relevant.

After each finished job, add the findings to that customer's `history.md`. That's what lets the next report say "repeat finding" or "corrected since last inspection".

## Turning it into a SaaS later

This setup is a working internal tool and the test bench. Before selling it:
- One login and one Knowledge/memory space per customer company, with no shared customer data.
- HTTPS, backups, and a written data policy for customers.
- An inspector sign-off step before any report leaves the system.
- Keep the test cases. Re-run them whenever you change models or the rulebook.
