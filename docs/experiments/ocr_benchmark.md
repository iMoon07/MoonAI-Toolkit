# OCR Benchmark Report

**Target Image:** `debug_20260701_223303_original.jpg`
**Image Size:** 960x1280

## Summary

| PSM | Description | Chars | Words | Time (s) |
|-----|-------------|-------|-------|----------|
| 3 | Fully automatic page segmentation, but no OSD. (Default) | 0 | 0 | 0.73 |
| 4 | Assume a single column of text of variable sizes. | 0 | 0 | 0.24 |
| 6 | Assume a single uniform block of text. | 40 | 12 | 0.27 |
| 7 | Treat the image as a single text line. | 0 | 0 | 0.22 |
| 11 | Sparse text. Find as much text as possible in no particular order. | 160 | 42 | 0.38 |
| 12 | Sparse text with OSD. | 176 | 51 | 0.52 |

## Detailed Output

### PSM 3
- **Chars:** 0
- **Time:** 0.73s

```text
[EMPTY (0 chars)]
```

---

### PSM 4
- **Chars:** 0
- **Time:** 0.24s

```text
[EMPTY (0 chars)]
```

---

### PSM 6
- **Chars:** 40
- **Time:** 0.27s

```text
INZAEL
MEN SU AK/ oy “Seay
| ' aaa \ 4 ;
```

---

### PSM 7
- **Chars:** 0
- **Time:** 0.22s

```text
[EMPTY (0 chars)]
```

---

### PSM 11
- **Chars:** 160
- **Time:** 0.38s

```text
a

e

‘Tia a

Vig

Lf

a" ~~

IN/

= =

wy t

MEN

(5

NZ

7&2

>:

TABI

45 p

wip

IN

4 r || iF

SS

eee

ae

D

/,

SC os

Kad

|

ie

NS @F

|

iniaetee tt
```

---

### PSM 12
- **Chars:** 176
- **Time:** 0.52s

```text
a ee —.

———

eS

2

m

:

©

5

|

Z

oy —

fi

y

L'\?m—

Ch)

<<

:

|

oe NS cx

/ SG

aK

. se

ay > a

f>

LAP

=

—

/ A

—)

we

oe

a AN.

a,

ry

ae

1G

‘=

wt

7 .€
```

---

