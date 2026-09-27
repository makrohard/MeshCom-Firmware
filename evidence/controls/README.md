# Controls outside the posted PR heads

## Old PR1 (`c4f508b3`): the F1 `{SET}` regression control

- `c4f508b3` = `7af1ef86` + `c4f508b3` on upstream `6cc8b552`: the pre-gate-2 PR1. The two commits are in
  `old-pr1-c4f508b3-patches/`.
- Image: `flash-r6-pr1-instr.bin` (INSTRUMENT_ENABLED, meshcom-qemu-raspi overlay `113ff40b`). Its sha256 is in
  `old-pr1-c4f508b3-image.sha256`. Build log: `old-pr1-c4f508b3-image-build.log` (first line: "tree at c4f508b3").
- Run in this evidence set, on the idle PC:
  - log: `../qemu/idle/qemu-sethop-oldpr1-c4f508b3-instr.log`
  - UART: `../qemu/idle/qemu-sethop-idle-oldpr1-c4f508b3-instr/`
- Result: `{SET}2` → RAM 2, NVS `max_hop_text` **4** after a hard power-off, `...MAXHOP text 4` after the reboot,
  NVS **4** after a TX + power-off. The value is LOST: the regression.
- The fixed PR1 (posted `3f936a63`) and the merge keep **2** in all three places.
- A first attempt used the wrong image (built from `b1de77e4`, the fixed PR1). It is kept as
  `../qemu/idle/INVALID-wrong-image-b1de77e4-*`.
