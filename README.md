# 描眉画目·定制美学 — website

Production website for a private eyebrow studio in Shanghai Pudong.

**Live:** https://miaomeihuamu.com/

Static HTML on GitHub Pages. No framework. Content is edited through Pages CMS (`.pages.yml`) or by commit.

## Why this repository is public

It is a working example of a small-business site that publishes the same facts to people and to machines:

- visible pages for people;
- schema.org JSON-LD for search and answer engines;
- `llms.txt` and `.well-known/ai.txt` for AI crawlers;
- `ai/summary.json`, `ai/faq.json`, `ai/service.json` for machine reading.

Keeping those copies in agreement is the hard part. Before each release we run [website-fact-check](https://github.com/wintercheer5353-png/website-fact-check), a read-only checker, over the site and review anything it flags. This repository is its reference deployment.

This is not a template. It is a live business site, and the content is specific to it.

## Fact policy

These are release rules, not suggestions:

- One canonical brand name: **描眉画目·定制美学**.
- One public phone number, repeated across surfaces by design. Before each release the checker compares the copies it finds across pages, `llms.txt` and the `ai/*.json` files — root fields, nested fields and FAQ answers included.
- No prices in public content. The site points to the current booking listing instead.
- The practitioner is referred to publicly as **乐乐老师**. The owner's personal legal name is not published.
- Works images are published with the owner's authorization. Review excerpts are shown with nicknames redacted.

## Editing and release

1. Edit through Pages CMS or commit directly.
2. Run `website-fact-check` against the changed files.
3. Deploy on merge to `main`.

The checker is read-only; it never edits the site. A failing check is reviewed by a human, who decides which surface is wrong, before the release goes out.

## Layout

```text
index.html          home
about.html          studio and practitioner
price.html          services and rules (no prices)
wild-brow.html      technique comparison
area.html           location and arrival
works.html          work records by project
posts/*.html        long-form pages, FAQ, arrival guide
ai/*.json           machine-readable summary, FAQ, services
llms.txt            root-level AI index
.well-known/ai.txt  crawler notes and canonical entry points
robots.txt          explicit allow list for search and AI crawlers
sitemap.xml         canonical public page list
feed.xml            RSS
content/*.json      Pages CMS source data
assets/             images and work records
admin/              Pages CMS entry
CNAME               custom domain
```

## License

- Code and configuration: MIT. See `LICENSE`.
- Site copy, images, and brand assets: © 描眉画目·定制美学， all rights reserved. See `LICENSE-CONTENT`.

## 中文概要

这是描眉画目·定制美学的官网源码：静态 HTML，GitHub Pages 部署，Pages CMS 维护。
同一事实同时出现在正文、JSON-LD、`ai/*.json`、`llms.txt` 和 `.well-known/ai.txt`；
发布前用 website-fact-check 检查这些出口是否一致。代码 MIT，文案与图片版权归门店。
