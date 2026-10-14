# Datong Society of China Studies at UC Berkeley
> *Student-led Organization at Cal*

Datong Society of China Studies at UC Berkeley is a student-led intellectual community bridging diverse academic perspectives on China and East Asia. We welcome undergraduates, graduate students, and researchers across disciplines—ranging from history and cultural studies to political economy and empirical social science (both qualitative and quantitative).

---

## What We Do

Rather than following a rigid schedule, our activities adapt dynamically to the research interests of our members. Our core engagement formats include:

* **Discussion & Reading Groups**  
  In-depth, text-based analytical discussions on classic literature and contemporary scholarship.
* **Seminars & Methodological Exchanges**  
  Peer research presentations, discussion of works-in-progress, and interdisciplinary dialogues.
* **Scholar & Guest Exchanges**  
  Occasional lectures and informal discussions with visiting scholars, writers, and artists.

---

## Our Ethos

We prioritize high-density intellectual exchange in an open, collaborative setting. Whether you are pursuing formal China studies or applying social science methods to East Asian issues, Datong provides a space for critical inquiry and interdisciplinary learning.

---

## Get Involved

> [!NOTE]
> We welcome non-members and prospective fellows to join our regular meetings! Please email our Primary Contact in advance to check for availability and location details.
* 🌐 **Website:** [datong.studentorg.berkeley.edu](https://datong.studentorg.berkeley.edu/)
* 📍 **Location:** UC Berkeley Campus

## Website maintenance

The site is a bilingual static website served by OCF. Edit `content/pages/`,
`content/events.json`, `content/resources.json`, and shared `templates/`.
Run `python scripts/build_site.py` to generate the root HTML pages; do not edit
those generated pages directly. Shared styles live in `assets/css/main.css`.

See [architecture and editing guide](docs/architecture.md) and
[deployment, rollback, and handover](docs/deployment.md).

Before publishing, add new files to Git and run `python scripts/check_site.py`.
The OCF workflow builds and validates the same artifact on Linux. GitHub Pages
remains disabled. Preview locally with `python scripts/serve_site.py --port 8766`.

GoatCounter analytics is configured in `content/site.json` for the society-owned
`datong.goatcounter.com` account. View statistics there after signing in.
Set its provider to `none` to disable tracking.
