name: Sync Squarespace Blog

on:
  schedule:
    - cron: '17 * * * *'
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: blog-sync
  cancel-in-progress: false

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - name: Sync blog posts
        run: python sync.py

      - name: Commit updated posts
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add posts.json

          if git diff --cached --quiet; then
            echo "No new blog posts."
          else
            git commit -m "Update latest blog posts"
            git pull --rebase origin main
            git push origin main
          fi

      - name: Prepare public feed
        run: |
          mkdir -p public
          cp posts.json public/posts.json

      - name: Configure GitHub Pages
        uses: actions/configure-pages@v5

      - name: Upload public feed
        uses: actions/upload-pages-artifact@v3
        with:
          path: public

  deploy:
    needs: sync
    runs-on: ubuntu-latest

    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}

    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
