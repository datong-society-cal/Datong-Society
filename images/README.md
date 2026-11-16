# Website images

Every file here is published, and packaging fails if a file is not referenced by
a page or stylesheet. Delete unused images instead of keeping them here; Git
history retains old versions.

| Rule | Why |
|---|---|
| lowercase ASCII only, words joined by `-` | URL-safe and identical on every OS |
| event folders are named after the event ID in `content/*.json` | the JSON record and its media are easy to match |
| inside an event folder: `cover.jpg` or `poster.jpg`, then `01.jpg`…`NN.jpg` | one obvious cover; explicit gallery order |
| folders group by role: `background/`, `brand/`, `qr/`, `events/` | find an asset by what it does |
| resize photos to at most 2000 px on the long edge, JPEG/WebP | keeps the artifact within the OCF budget |

Captions must describe the actual image; a publicity image is not a scene from
the event.
