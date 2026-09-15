# Datong website agent notes

Before changing website media, deployment packaging, or hosting behavior, read
the local `.agents/ocf-web-performance.md` incident note when it is available.

Keep the production artifact within the performance budgets enforced by
`scripts/site_contract.py`. Event-gallery and QR images must remain lazily
loaded, and the favicon must remain the Datong logo at
`images/brand/datong-logo-emblem.png` on both GitHub Pages and OCF.
