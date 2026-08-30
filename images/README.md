# Image catalog — Datong Society website

This directory holds **every** image used by the site. The file names are part of the
documentation: each name says what the picture is, so a person browsing the folder and an
AI reading the repo can both tell what an asset is without opening it.

Regenerate this file with `python .workbuddy-ai/make_image_catalog.py` (from the repo root)

after adding, removing or renaming images.


## Naming rules

| Rule | Why |
|---|---|
| lowercase ASCII only, words joined by `-` | URL-safe, no percent-encoding, safe on every OS and in git |
| no Chinese characters in file or folder names | avoids `%E4%B8%AD...` in URLs and path bugs on Windows |
| event folders are `<year>-<type>-<topic>` | the listing sorts chronologically and reads as a sentence |
| inside an event folder: `cover.jpg` is the card thumbnail, `01.jpg`…`NN.jpg` are the gallery | one obvious cover, gallery order is explicit |
| folders group by role: `background/`, `brand/`, `sections/`, `qr/`, `events/` | you can find an asset by what it *does*, not by guessing a name |
| never reuse the template names `pic01/pic02/pic03`, `bg.jpg`, `logo.jpg` | those say nothing about content |

## Layout

```
images/
├── background/          site chrome — what sits behind the content
│   ├── site-background.jpg
│   └── overlay-texture.png
├── brand/               logos
│   ├── datong-logo.jpg
│   └── datong-logo-emblem.png
├── sections/            wide banners shown at the top of each section
│   ├── banner-intro.jpg
│   ├── banner-activities.jpg
│   └── banner-about-us-grad-2025sp.jpg
├── qr/                  scannable codes
│   ├── qr-wechat-official.jpg
│   ├── qr-recruit-qa.jpg
│   └── qr-recruit-form.png
└── events/              Past Events gallery, one folder per event
    ├── 2016-salon-social-science/   (5 images)
    ├── 2017-field-trip-hoover-archives/   (5 images)
    ├── 2018-community-retreat-senior-citation/   (5 images)
    ├── 2018-fall-salons-member-portraits/   (5 images)
    ├── 2019-exhibition-sookmyung-embroidery/   (7 images)
    ├── 2023-author-talk-geling-yan/   (4 images)
    ├── 2023-lecture-zhukeliang-wechat-lawsuit/   (7 images)
    ├── 2025-graduation-portraits/   (6 images)
    ├── course-decal-contemporary-china/   (3 images)
    ├── film-still-life-screening/   (5 images)
    ├── film-the-chinese-mayor-screening/   (2 images)
```

## Site assets

| File | Size | Dimensions | What it is |
|---|---|---|---|
| `background/site-background.jpg` | 199 KB | 1280x832 (JPEG) | Full-page site background photo, sits behind the blurred overlay on every view<br><span style="opacity:.6">整站全屏背景图，位于毛玻璃遮罩之下，所有页面共用</span> |
| `background/overlay-texture.png` | 4 KB | 512x512 (PNG) | 512x512 repeating dot/grid texture tile; the CSS scales it to 256px and layers it over the background photo<br><span style="opacity:.6">512×512 重复平铺的网点纹理；CSS 缩放到 256px 后叠在背景图之上</span> |
| `brand/datong-logo.jpg` | 212 KB | 960x960 (JPEG) | Datong Society logo — emblem with lettering (original artwork)<br><span style="opacity:.6">大同学社 logo：徽标 + 文字（原始稿件）</span> |
| `brand/datong-logo-emblem.png` | 145 KB | 320x320 (PNG) | Emblem-only logo cut-out, navy + gold; transparency restored and colour boosted so it reads on dark backgrounds<br><span style="opacity:.6">仅徽标的去背 logo，藏青 + 烫金；已还原透明度并提升饱和，适配深色背景</span> |
| `sections/banner-intro.jpg` | 124 KB | 1365x768 (JPEG) | Wide banner at the top of the "Intro" section (was a 1.05 MB PNG mislabelled `.jpg`; re-encoded as JPEG — 946 KB saved)<br><span style="opacity:.6">「Intro」版块顶部横幅图（原为 1.05 MB 的 PNG 却命名为 .jpg，已重新编码为 JPEG，节省 946 KB）</span> |
| `sections/banner-activities.jpg` | 9 KB | 960x320 (JPEG) | Wide banner at the top of the "Activities" section<br><span style="opacity:.6">「Activities」版块顶部横幅图</span> |
| `sections/banner-about-us-grad-2025sp.jpg` | 627 KB | 1920x1080 (JPEG) | Group photo of the Spring 2025 graduating cohort (Hearst Memorial Mining Building); the "About Us" banner. Displayed full-frame via the `.bleed` class — never cropped<br><span style="opacity:.6">2025 春季毕业班合影（Hearst Memorial Mining Building），用作「About Us」横幅；通过 `.bleed` 类完整显示，不做裁切</span> |
| `qr/qr-wechat-official.jpg` | 30 KB | 275x276 (JPEG) | QR code — Datong Society WeChat official account<br><span style="opacity:.6">大同学社微信公众号二维码</span> |
| `qr/qr-recruit-qa.jpg` | 192 KB | 1080x1632 (JPEG) | QR code — Fall 2026 recruitment Q&A WeChat group<br><span style="opacity:.6">2026 秋季招新答疑微信群二维码</span> |
| `qr/qr-recruit-form.png` | 7 KB | 275x276 (PNG) | QR code — Fall 2026 recruitment sign-up form<br><span style="opacity:.6">2026 秋季招新报名表二维码</span> |

## Events gallery — `images/events/`

Each folder is one Past Events card. `cover.jpg` is the thumbnail shown on the card;
the numbered files are the photos opened in the lightbox.

| Folder | Date | Category | Event | Images | Folder size |
|---|---|---|---|---|---|
| `2016-salon-social-science` | 2016-09-22 | Salon | Salon — "Let's Talk About Social Science"; interdisciplinary dialogue across history, sociology and political science<br><span style="opacity:.6">跨学科沙龙「Let's Talk About Social Science」：历史 / 社会学 / 政治学对话</span> | 5 | 213 KB |
| `2017-field-trip-hoover-archives` | ~2017 | Field Trip | Field trip — Stanford Hoover Institution archive visit<br><span style="opacity:.6">斯坦福 Hoover Institution 档案馆参访</span> | 5 | 395 KB |
| `2018-community-retreat-senior-citation` | 2018-2019 | Retreat / Citation | Community life — annual retreats and senior citations<br><span style="opacity:.6">社区生活：年度 Retreat 与毕业 Citation</span> | 5 | 676 KB |
| `2018-fall-salons-member-portraits` | 2018 Fall | Salon | Fall 2018 salon series and member portraits<br><span style="opacity:.6">2018 秋季沙龙季与社团成员合影</span> | 5 | 522 KB |
| `2019-exhibition-sookmyung-embroidery` | 2019 Spring | Exhibition | Exhibition — modern Chinese-character embroidery on pillow covers, Sookmyung Women's University (Korea)<br><span style="opacity:.6">韩国淑明女子大学汉字刺绣枕顶展</span> | 7 | 662 KB |
| `2023-author-talk-geling-yan` | 2023-10-22 | Author Talk | Author talk and book signing with Geling Yan (《米拉蒂》)<br><span style="opacity:.6">严歌苓《米拉蒂》新书签售会</span> | 4 | 403 KB |
| `2023-lecture-zhukeliang-wechat-lawsuit` | 2023-04-09 | Lecture | Lecture by attorney Ke-liang Zhu — the WeChat lawsuit against Trump<br><span style="opacity:.6">朱可亮律师讲座：在美华人 vs 美国总统（WeChat 诉 Trump）</span> | 7 | 326 KB |
| `2025-graduation-portraits` | 2025-05 | Community | Graduation portraits — Spring 2025 graduating members<br><span style="opacity:.6">2025 春季毕业合影</span> | 6 | 1.24 MB |
| `course-decal-contemporary-china` | 2016-ongoing | Student Course | DeCal student course — Global Studies 198, Contemporary China<br><span style="opacity:.6">DeCal 学生课程：Global Studies 198 当代中国</span> | 3 | 838 KB |
| `film-still-life-screening` | 2015 / 2023 | Film & Panel | Film screening and scholar discussion — 《三峡好人》 Still Life<br><span style="opacity:.6">《三峡好人》放映与学者分享</span> | 5 | 438 KB |
| `film-the-chinese-mayor-screening` | 2015 / 2021 | Film & Panel | Film screening and panel — 《中国市长》 The Chinese Mayor<br><span style="opacity:.6">《中国市长》放映与座谈</span> | 2 | 417 KB |

**Gallery photo names** are `01.jpg`, `02.jpg`, … in the order they appear on the page.
They are deliberately numbered rather than described: the individual shots are not captioned
anywhere, and inventing a description would be a guess. The folder name plus `cover.jpg`
tells you what the group of photos is.


## Renamed from the previous layout

Kept so git history and old links can be traced. Nothing below still exists on disk.

| Old path (before) | New path (now) |
|---|---|
| `images/bg.jpg` | `images/background/site-background.jpg` |
| `images/overlay.png` | `images/background/overlay-texture.png` |
| `images/logo.jpg` | `images/brand/datong-logo.jpg` |
| `images/logo-emblem.png` | `images/brand/datong-logo-emblem.png` |
| `images/pic01.jpg` | `images/sections/banner-intro.jpg` |
| `images/pic02.jpg` | `images/sections/banner-activities.jpg` |
| `images/pic03.jpg` | `removed — unused template placeholder` |
| `images/about-us-banner.jpg` | `images/sections/banner-about-us-grad-2025sp.jpg` |
| `images/wechat-qr.jpg` | `images/qr/qr-wechat-official.jpg` |
| `images/recruit-qa-qr.jpg` | `images/qr/qr-recruit-qa.jpg` |
| `images/recruit-form-qr.png` | `images/qr/qr-recruit-form.png` |
| `images/events/community/` | `images/events/2018-community-retreat-senior-citation/` |
| `images/events/decal/` | `images/events/course-decal-contemporary-china/` |
| `images/events/embroidery/` | `images/events/2019-exhibition-sookmyung-embroidery/` |
| `images/events/fall2018/` | `images/events/2018-fall-salons-member-portraits/` |
| `images/events/grad2025/` | `images/events/2025-graduation-portraits/` |
| `images/events/hoover/` | `images/events/2017-field-trip-hoover-archives/` |
| `images/events/mayor/` | `images/events/film-the-chinese-mayor-screening/` |
| `images/events/socialsci/` | `images/events/2016-salon-social-science/` |
| `images/events/stilllife/` | `images/events/film-still-life-screening/` |
| `images/events/yan/` | `images/events/2023-author-talk-geling-yan/` |
| `images/events/zhukeliang/` | `images/events/2023-lecture-zhukeliang-wechat-lawsuit/` |
| `images/events/*/<chinese-name>-cover.jpg` | `images/events/<slug>/cover.jpg` |

## Where the two newest assets come from

| Site file | Source file (outside the repo, in `../`) | Note |
|---|---|---|
| `background/site-background.jpg` | `Website/bg.jpg` | ⚠️ the source is **actually a PNG** mislabelled `.jpg`. Converted to JPEG, 1280x832, q85. |
| `sections/banner-about-us-grad-2025sp.jpg` | `Website/About Us Banner_Grad 25SP.png` | ⚠️ the source is **actually a PNG** too. 3140x1766 → resized to 1920x1080, q88. Shown uncropped. |

## Mislabelled files found while cataloguing

Several files in this project carry an extension that does not match their real format.
All of the ones *inside* `images/` have been re-encoded so the extension now tells the truth.
The two source files in `Website/` are left alone — rename them there if you want.

| File | Extension says | Actually is | Status |
|---|---|---|---|
| `images/sections/banner-intro.jpg` | `.jpg` | PNG, 1.05 MB | ✅ re-encoded as JPEG (123 KB) |
| `images/background/site-background.jpg` | `.jpg` | — | ✅ generated as real JPEG |
| `images/sections/banner-about-us-grad-2025sp.jpg` | `.jpg` | — | ✅ generated as real JPEG |
| `../Website/bg.jpg` *(source)* | `.jpg` | PNG, 2.5 MB | ⚠️ still mislabelled |
| `../Website/About Us Banner_Grad 25SP.png` *(source)* | `.png` | PNG ✅ | ✅ correct |

Quick check on Windows/git-bash: `head -c 4 file | xxd` — `ffd8` is JPEG, `8950 4e47` is PNG.


## Known issues

- `images/members/alex.jpg` is referenced by the "Meet Our Members" block in `index.html`
  but **the file has never existed in this repo**. The block falls back to a neutral
  gradient placeholder circle via an `onerror` handler, so nothing renders broken —
  but the member names in that block are still placeholder text and need real content.
- The `.image.main` wrapper draws a 50%-opacity texture overlay (`.image:before`) over every
  image, banners included. That is inherited template styling; remove it per-image with
  `.image.main.no-overlay:before { display: none; }` if you want a clean photo.

## Totals

- site assets: **10 files**, 1.51 MB
- events gallery: **11 folders**, 6.02 MB
- **grand total: 7.53 MB**
