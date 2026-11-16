# Imagine

Local image generator for Bastion: describe a picture, pick Photo / Anime / Pixel / Logo, a size and Draft or not, and get
1 or 4 images made on the server's own GPU. The page never shows model names, steps or seeds.
The page opens on Anime and Make 1 (nothing is remembered; Make 4 is one tap away). Every image can also be opened as editable fields,
changed by hand and made again with a new seed. No AI edits the picture or the fields.

The page has two tabs (`?s=`): **Create** (the generator above) and **Characters** (phase 1 of a manhwa tool; stories come later).

## How it works
- The engine is ComfyUI in the AI CT at `/models/comfyui` (venv `/models/comfyui/venv`, unit `comfyui.service`). It listens on
  `127.0.0.1:8188` only, is **not enabled**, and is started per job. It is hidden: the agent reaches it only through
  `pct exec`, using `bin/gen.py` (pushed to `/opt/imagine/gen.py`), which builds the fixed workflows itself.
- Workflows, all named in the `MODELS` table at the top of `bin/gen.py` (file, steps, cfg, sampler, scheduler):

  | Style | Model | Settings |
  |---|---|---|
  | Pixel, Logo | FLUX.1-schnell GGUF Q5_K_S | 4 steps, cfg 1, euler |
  | Anime | NoobAI-XL 1.1 (SDXL) | 28 steps, cfg 5.5, Euler a, normal, CLIP skip 1; Adult switch |
  | Photo | Juggernaut XL | 25 steps, cfg 5.5, dpmpp_2m karras |
  | Draft (any style) | SDXL Turbo, 512 px long side | 4 steps; ignores the Adult switch |

  Anime prompt: `masterpiece, best quality, newest, absurdres, highres, safe,` + your prompt + the style text, with a negative list
  that starts with `nsfw`. Adult on drops `safe,` and `nsfw` and nothing else. Other styles get no extra tags.
  The old Q4_K_S FLUX file was deleted on 2026-11-08 after Q5 was in place; to go back, download it again and set `unet` and `REQUIRED_FILES` back.
- Agent module `agent/imagine.py`: routes `GET /imagine/state|characters`, `POST /imagine/submit|cancel|delete|json|regenerate` and `/imagine/character/save|delete|looks|reference|batch|rate|cleanup`. Queue in
  `/var/lib/dash-imagine/queue.json`; images in `/srv/bastion-files/imagine/<YYYY-MM-DD>/<job>-<n>.png` + `.json` sidecar
  (prompt, style, size, draft, adult, ts, seed, parent `{job,n}` or null, json), shown through the Files add-on's `/api/files/raw`.

## Job flow (one worker thread, one job and one image at a time)
1. In the AI CT stop `warm-model.timer`, unload every loaded Ollama model, wait until at least 7700 MiB of VRAM is free (9500 for IP-Adapter jobs); if it does not come, stop kokoro, then subgen (see Memory rules); still short after 30 s: the job fails with that message.
2. `systemctl start comfyui`, wait until it answers.
3. Generate the images one by one, saving each as soon as it is done. On CUDA OOM: unload Ollama again, `POST /free`, retry once.
4. When the queue is empty, or on any failure or cancel: `POST /free`, start the containers this agent stopped, start `warm-model.timer` + `warm-model.service` (qwen is back). `comfyui` stops after 10 minutes idle.
5. Agent restart: running jobs go back to queued; the warm timer is started again if no job is waiting.

Games guard: submit is refused and a running job pauses between images while games stream (`nvidia-smi` encoder
session count above 0, or a GPU process whose CT is the games CT; a stopped games CT is not streaming).
Message: "Games are streaming, try later".

## Edit flow (fields, manual edit, regenerate)
Fixed schema, short strings except `details`: `{subject, setting, composition, lighting, colors, mood, details: [up to 6]}`. Style and size stay outside it.
The viewer shows them as five labelled groups: **Subject** (subject), **Scene** (setting, with the time of day kept inside it), **Look** (lighting,
colors, mood), **Shot** (composition) and **Extras** (details, one per line, max 6). The keys are unchanged, so old sidecars still work.
- `POST /imagine/json {job,n}`: the sidecar's `json`, or, when missing, made once from the original prompt (text only, no vision, no image) by `qwen3.5:9b`
  (Ollama chat, `think: false`, `format: json`, temperature 0, default keep_alive) and saved to the sidecar. The prompt is passed as data and
  its language is kept. Output is validated in code: allowed keys only, strings 200 chars, details 6 x 120, missing keys become "".
  This is the only AI call of the edit flow; there is no tweak route and no instruction box.
- `POST /imagine/regenerate {job,n,json,keep_seed}`: the owner's edited fields are validated again, the prompt is composed in code (fields in schema
  order, then details, joined with ", ", empties skipped) and one new job (count 1) is queued with the source's style, size, draft and adult flag (the editor may flip it) and `parent`. Old sidecars without `adult` count as off.
  The seed is new and random by default; "Keep seed" (`keep_seed`) reuses the source's seed (a random one if an old image has none). Its sidecar
  stores the json and seed. Same games guard and engine check as submit.
- Gallery items made this way show a "From an earlier picture" link in the viewer while the parent still exists.

## Characters
Fictional characters only, never real people. A character is `{id, name, gender (girl|boy|other), age, hair, eyes, build, outfit, extras (each <= 120 chars),
note (<= 300), adult, reference {job,n,seed,file} | null, created}`; at most 50. Stored in `/var/lib/dash-imagine/characters.json` (atomic write).
The reference picture is copied to `/srv/bastion-files/imagine/characters/<id>/reference.png` so deleting it from the gallery does not break the character.
- **Age is a gate: whole number, 18 or older.** `17`, `"18"` (a string), `18.5` or a missing age are refused in both the proxy and the agent. The number is never
  sent to the model and cannot control what it draws, so you still look at every image yourself.
- Prompt tags are composed in code, deterministic: `1girl|1boy|1other, solo, adult, hair, eyes, build, outfit, extras` (empties skipped; the note is never used).
  Always Anime (NoobAI) with its usual quality prefix; the character's Adult flag decides `safe`/`nsfw` as for any anime job. Looks never use Draft.
- Routes: `GET /imagine/characters` (each with its `looks`: gallery images whose sidecar has `character=<id>`, newest first), `POST /imagine/character/save`
  (create, or update when `id` is given; manual edits only), `/character/delete {id}` (the character and its reference copy, not the gallery images),
  `/character/looks {id}` (one job: 4 images, portrait, Anime, not Draft, hidden composed prompt; same games guard, engine check and GPU path as submit),
  `/character/reference {id,job,n}` (copies the PNG, stores the sidecar's seed, `null` for old sidecars without one).
- Create tab: with Anime and at least one character a **Character** select appears. The prompt box holds only your scene text; the agent puts the character's
  tags in front. Adult follows the character unless flipped for that picture. **Match reference** (on by default, only with a reference; it was "Same look" and reused the reference seed) sends the reference through IP-Adapter, see below. The sidecar stores `character` and `scene`.

### Stage A: reference -> rated batches -> approved set (0.6.0)
Characters must be **original**: this add-on is for your own characters, not copies of published ones or of real people.
1. **Reference**: make 4 looks, pick one with "Use as reference" (Change in the Reference section goes back to the looks).
2. **Make 4 more** (`POST /imagine/character/batch {id}`; 400 without a reference): ONE job of 4 non-draft anime portraits. The job carries `variants`, a prompt per
   image: composed character tags + the looks framing + one expression (neutral, smile, serious, surprised), one angle (from front, three-quarter view, from side,
   slightly from above) and one light (soft light, rim light, dramatic lighting, daylight), each list shuffled so the 4 images differ in every axis. New random seeds.
   The worker uses `variants[n-1]` for image n (jobs without `variants` use `prompt`); the sidecar stores the exact prompt, `character` and `batch: true`.
3. **Rate** (`POST /imagine/character/rate {id, job, n, verdict}`): `good` copies the PNG + sidecar to `/srv/bastion-files/imagine/characters/<id>/set/<job>-<n>.png`
   (at most 60 in the set, the reference included; 400 when full), `bad` only records it as rejected, `clear` removes it from the set / rejected. Ratings live in the
   character record (`set: [{job,n,file,prompt}]`, `rejected: [{job,n}]`). The reference is always the first set picture and is not rated.
4. **Delete rejected** (`POST /imagine/character/cleanup {id}`, tap twice in the UI): deletes the gallery PNG + sidecar of that character's rejected pictures only.
`GET /imagine/characters` adds per character `set` (reference first, with files), `unrated` (its pictures in neither set nor rejected), `rejected` / `rejected_n`
and `target` (goal 8-12 approved, limit 60). Goal of the stage: 8-12 approved pictures.

### IP-Adapter: pictures follow the reference (0.7.0)
Used for (a) **Make 4 more** batches and (b) Create jobs with a character that has a reference while **Match reference** is on (the old "Same look"; default on,
disabled with a one-line reason when the character has no reference). It replaces the old reference-seed trick, so those jobs get random seeds. Never for Draft,
for the Looks jobs that create the reference, or for jobs without a character.
- The agent reads `/srv/bastion-files/imagine/characters/<id>/reference.png`, sends it base64 with the image request, and `bin/gen.py` uploads it to ComfyUI's input folder
  (`POST /upload/image`, named `ref_<id>_<hash>.png`, so the same picture is reused). The graph adds `LoadImage` -> `IPAdapterModelLoader` + `CLIPVisionLoader` ->
  `IPAdapterAdvanced` (weight 0.25 (0.5 and up burns the colours on NoobAI; 0.35 kept the scar but shifted them), `linear`, 0.0 to 1.0, `concat`, `V only`) on the NoobAI model before the KSampler. Steps, cfg, sampler, prompts and the Adult handling are unchanged.
- Files (all named in `MODELS["ipadapter"]`): node pack `/models/comfyui/custom_nodes/ComfyUI_IPAdapter_plus`, `models/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors`,
  `models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors`. The node pack loads only when ComfyUI starts (it stops by itself when idle).
- The job and the image sidecar store `ipadapter: true` and `ip_weight`. Jobs without a reference are unchanged.

### Your own pictures (0.8.0)
In the Set section the owner can add pictures of an **original character** (rule, shown above the button and required: *My own pictures of an original character. No real people, no art of published characters.*; the tick is not remembered and the button stays off until it is set; the route refuses without `ack: true`).
They sit in the character's set next to the approved copies (pill "Upload", tap-twice remove), count towards the same limit of 60, and are what later IP-Adapter references and the LoRA training step use: training takes the whole set.
- Transport: base64 JSON through the app proxy (as the chat's file upload does), one file at a time from the browser. `POST /imagine/character/upload {id, name, data, ack}` and `POST /imagine/character/upload/delete {id, file}` (uploads only, never the reference).
- Limits: 10 MB per file, PNG / JPEG / WebP decided by magic bytes (name and type are ignored), opened with Pillow; broken, animated, over 8000 px a side or over 40 million pixels are refused.
- Stripped: all metadata (EXIF, GPS, ICC, text chunks) because the saved PNG is built from the pixels only; the EXIF turn is applied first. Longest side shrunk to 2048 px. Saved as `/srv/bastion-files/imagine/characters/<id>/set/up-<10 hex>.png`; the set entry is `{file, source: "upload", prompt: "", name}` (name = cleaned original file name, 60 characters).

## Memory rules (0.7.0)
Plain jobs need 7700 MiB of free VRAM, IP-Adapter jobs 9500 MiB. Order in the worker: stop `warm-model.timer`, unload Ollama, wait up to 20 s for the memory; if still short,
stop the Docker containers **`kokoro`** (read-aloud voice) and then **`subgen`** (Whisper subtitles) in the AI CT, one at a time, re-measuring with `nvidia-smi` between.
Nothing else is ever stopped (the names are a fixed list in the agent, `stopped.json` is filtered to it, and a container that was not running is left alone).
- Before each stop its name is written (atomic) to `/var/lib/dash-imagine/stopped.json`; the job shows "Freeing memory" meanwhile, and "Voice and subtitles are paused
  until the images are done" on queue rows while anything is stopped (`voice_paused` in `/imagine/state`).
- They are started again (`docker start`, only the listed ones, the file is emptied) in the same release step that brings qwen back: queue empty, failure or cancel. With more jobs
  waiting they stay stopped. After an agent restart, anything the file still lists and that is not running is started. A failed start stays listed for the next try.
- Whisper (subgen) needs about 3 minutes to load after it starts again; the worker does not wait for it. Games guard unchanged.
- If the card still has less than the requirement, the job fails with "Not enough free GPU memory".

## GPU lock
One `threading.RLock` (`GPU`) in the agent. The worker holds it for a whole job (unloading Ollama through the restore step) and every qwen call holds
it for its Ollama call, so they never overlap. While any job is queued, running or paused the json route answers 400 "An image is being made,
try again when it is done" at once; a job queued during a qwen call just waits for the lock. regenerate only queues (no qwen). qwen calls skip the games guard and never pin the model.

## Adult switch, licence, age rule
- `adult` (boolean, default false) on `POST /imagine/submit` and `/imagine/regenerate`; the page shows the switch only for Anime. The proxy rejects
  non-booleans; the agent ignores it for other styles. It changes the prompt text only, the model stays NoobAI.
- NoobAI-XL licence: fair-ai-public-license-1.0-sd, plus no commercial use and no "unethical or offensive" content. Check it before sharing output.
- Adult mode is for adults only. No sexual content of minors, and none of real people.

## Swapping a model
Edit its line in `MODELS` in `bin/gen.py` (and the file name in `REQUIRED_FILES` in `agent/imagine.py`, the install check). The workflow shape
(checkpoint vs FLUX unet/clip/vae) stays; steps, cfg and sampler move with the line. `gen.py` is pushed to the AI CT on the next job.

## VRAM budget (12 GB card, GB)
| Always resident | Kokoro 0.8, Whisper 1.1 |
| Reserved | Immich ML 2.0, headroom 0.4 |
| Chat | qwen 6.7 warm normally |
| While generating | qwen OFF; ceiling 7.7 GB for the engine, 9.5 GB with IP-Adapter (kokoro / subgen stopped if needed) |
| Games streaming | no generation |

## Tests
`python3 -I addons/imagine/tests/test_imagine.py` (IP-Adapter graph and wiring, which jobs carry it, 9500 vs 7700, stopped.json before the stop and cleared after, only kokoro/subgen, restart recovery; characters: age gate, composition, looks job, reference + seed, delete, caps, limit, guards; uploads (ack, magic bytes, metadata stripped, resize, size/bomb limits, shared set limit, delete rules, name cleaning); queue transitions, validation, games detection on fake nvidia-smi output, workflows, edit JSON validation, compose, regenerate (new seed by default, keep_seed, parent), busy guard and GPU lock with a stubbed Ollama).

## Undo
IP-Adapter off: set `ipadapter` jobs back by removing the reference branch in `bin/gen.py` `_sdxl` (or reinstall 0.6.0 from `/var/lib/dash-addons/old`). Remove the pack:
`pct exec <ai ct> -- rm -r /models/comfyui/custom_nodes/ComfyUI_IPAdapter_plus /models/comfyui/models/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors /models/comfyui/models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors`
(and `/models/comfyui/input/ref_*.png`), then restart `comfyui`. If something stayed stopped: `pct exec <ai ct> -- docker start kokoro subgen`, then empty `/var/lib/dash-imagine/stopped.json` (`[]`).
`pct exec <ai ct> -- systemctl disable --now comfyui; pct exec <ai ct> -- rm -r /models/comfyui /opt/imagine`, then remove the
add-on on /addons. Pictures stay in `/srv/bastion-files/imagine`; uploads are `characters/<id>/set/up-*.png` (remove with the x in the set, or delete the files and their `source: upload` entries); characters live in `/var/lib/dash-imagine/characters.json` (+ `characters/` under the pictures).
