# Malfoid's Vault

Amazon affiliate site for Draconia Malfoid, with AI-generated card art.

## What's here

| File | What it does |
|---|---|
| `index.html` | The site. Affiliate tag, social links and "Malfoid's Own Picks" are at the top of its script. |
| `products.js` | The pool of products the daily picks rotate through. |
| `art/` | Generated card images, plus `manifest.js` listing them. |
| `scripts/generate_art.py` | Makes 3 images per product with Gemini, picks the best, places it. |
| `.github/workflows/generate-art.yml` | Runs that script daily and on demand. |
| `my-photos/` | Optional: your own product photos to recreate (see below). |

## One-time setup

1. **Create the repository.** On GitHub, make a new public repository (for example `malfoid-vault`) and upload everything in this folder, keeping the folder structure. The `.github` folder must be included.
2. **Turn on the website.** Repository Settings > Pages > Source: "Deploy from a branch", branch `main`, folder `/ (root)`. Your site appears at `https://<your-username>.github.io/<repository-name>/` after a minute or two.
3. **Get a Gemini API key.** Create one at Google AI Studio (aistudio.google.com) and enable billing on it. Image generation has no free tier.
4. **Store the key privately.** Repository Settings > Secrets and variables > Actions > New repository secret. Name: `GEMINI_API_KEY`. Value: your key. Never put the key in a file.
5. **Run it.** Actions tab > "Generate product art" > Run workflow. Try one product first by entering an id such as `slytherin-scarf` in the "only" box. If it looks good, run it again with the box empty to do the rest.

## Cost

Each product uses 3 images at about $0.034 each, so roughly $0.10 per product and about $4 for all 36 (plus a few cents of token charges). Choosing the best image uses a model with a free tier. After the first full run, daily runs find nothing missing and cost nothing. Each run is capped at 40 products.

## Day to day

- **Add a product:** add an entry to `products.js` (copy an existing one, give it a new `id`). The next daily run draws its art.
- **Redo an image you don't like:** run the workflow with that product's id and "force" ticked.
- **Change the look:** edit `STYLE` and `PROMPTS` near the top of `scripts/generate_art.py`.
- **3D or scene:** each product's `kind` is `"3d"` (render on a pedestal, used for toys and collectibles) or `"setting"` (styled scene, used for clothing and home items).

## Recreating a product you own

Put your own photo in `my-photos/` named after the product id (for example `my-photos/slytherin-scarf.jpg`) and run the workflow for that id with "force". The generator then recreates that exact item instead of working from the text description.

Only use photos you took yourself. Amazon's listing photos (and other retailers') must not go in here: Amazon only allows its product images to be shown through its API, and reworking them with AI doesn't change that.

## Good to know

- Cards with generated art carry a small "Illustration" label so shoppers know it is not a photo of the exact item.
- Prompts ask for no text, logos or brand marks. Check each image before promoting it; regenerate any that slipped through.
- Keep the footer disclosure ("As an Amazon Associate I earn from qualifying purchases").
- Model names change. If a run fails saying the model is not found, set `IMAGE_MODEL` or `JUDGE_MODEL` in the workflow's `env` to the current names from Google's pricing page.
