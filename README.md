[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![Rank](https://make.fun/badge/news-image-20261125/onlybountyy-hub/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![Reward](https://make.fun/badge/news-image-20261125/onlybountyy-hub/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

# THE WORLD TODAY — Wednesday 25 November 2026

One image summing up 25 November 2026's world news — a newspaper front
page for the make.fun `news-image-20261125` bounty.

**Hero:** US spy agencies hit by cyberattack — CNN reported the CIA and the
Office of the Director of National Intelligence were hit, affecting
classified information.

**Also in the image:**

- Huawei found guilty in a US trial — a jury convicted Huawei on 10 of 12
  criminal counts, including trade-secret theft and bank fraud.
- WHO evacuates staff in Congo — health workers sheltered three days from
  fighting in Akwe, Ituri; the Ebola outbreak there counts 5,775 deaths
  among 11,762 cases.
- Houthi drone hits Riyadh tower — eleven people injured, Saudi civil
  defence said.
- Trump honours Giuliani — the Presidential Medal of Freedom for the former
  New York City mayor.
- England level T20 series — an eight-wicket win over Australia, chasing
  185, to level the five-match series.

## How it is made

Pure Python standard library only — no PIL, no third-party packages, no
network, no external assets. `main.py` draws the whole front page with its
own 5×7 bitmap font and writes a PNG with a hand-rolled zlib encoder. The
output is byte-identical on every run.

## Run

```sh
MAKEFUN_OUTPUT_DIR=out python3 -P -s main.py
```

This writes `out/entry.png` (1024×1024, PNG).
