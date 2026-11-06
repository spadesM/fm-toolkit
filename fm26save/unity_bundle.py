"""Minimal UnityFS (v6-v8) asset-bundle reader / writer used by the FM UI patches.

Only what is needed for *surgical* edits is implemented:

* :func:`read_bundle` parses the header, the (LZ4/LZ4HC-compressed) ``BlocksInfo``
  table and the storage-block layout of a ``.bundle`` file.
* :func:`decompress` returns the fully decompressed data stream (all serialized
  files concatenated, i.e. the same bytes Unity reads after decompression).
* :func:`patch_bytes` changes bytes at *uncompressed* offsets, re-compresses only the
  affected storage block(s) and rebuilds the header / ``BlocksInfo`` so that the
  result is a valid bundle whose decompressed stream differs **only** at the
  requested offsets.
* :func:`trace_lz4_byte` tells whether an uncompressed byte is stored as an LZ4
  literal (patchable in place) or produced by a back-reference (needs re-compression).

Compression needs the optional ``lz4`` package (``pip install lz4``); decompression
falls back to the pure-Python decoder in :mod:`fm26save.binary_decompiler`.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

try:  # optional, fast + required for re-compression
    import lz4.block as _lz4_block
except ImportError:  # pragma: no cover - exercised only without lz4
    _lz4_block = None

__all__ = [
    "BundleBlock",
    "UnityBundle",
    "read_bundle",
    "decompress",
    "patch_bytes",
    "trace_lz4_byte",
]

_COMP_NONE, _COMP_LZMA, _COMP_LZ4, _COMP_LZ4HC = 0, 1, 2, 3


def _lz4_decompress(src: bytes, size: int) -> bytes:
    if _lz4_block is not None:
        return _lz4_block.decompress(src, uncompressed_size=size)
    from fm26save.binary_decompiler import lz4_decompress_block

    return lz4_decompress_block(src, size)


def _lz4_compress(src: bytes) -> bytes:
    if _lz4_block is None:
        raise RuntimeError("Re-compressing a bundle needs the 'lz4' package:  pip install lz4")
    return _lz4_block.compress(src, mode="high_compression", compression=12, store_size=False)


@dataclass
class BundleBlock:
    """One storage block of a UnityFS bundle."""

    index: int
    c_off: int  #: file offset of the compressed block
    c_size: int
    u_off: int  #: offset of the block inside the decompressed stream
    u_size: int
    flags: int

    @property
    def compression(self) -> int:
        return self.flags & 0x3F


@dataclass
class UnityBundle:
    path: Path
    data: bytes
    version: int
    header_fields_pos: int  #: file offset of (size:u64, cBlocksInfo:u32, uBlocksInfo:u32, flags:u32)
    total_size: int
    flags: int
    blocks_info: bytes  #: decompressed BlocksInfo (hash + blocks + directory)
    blocks: list[BundleBlock] = field(default_factory=list)

    @property
    def uncompressed_size(self) -> int:
        return sum(b.u_size for b in self.blocks)

    def block_for(self, u_offset: int) -> BundleBlock:
        for blk in self.blocks:
            if blk.u_off <= u_offset < blk.u_off + blk.u_size:
                return blk
        raise IndexError(f"offset {u_offset:#x} outside the bundle data stream")

    def block_bytes(self, blk: BundleBlock) -> bytes:
        return self.data[blk.c_off : blk.c_off + blk.c_size]

    def decompress_block(self, blk: BundleBlock) -> bytes:
        raw = self.block_bytes(blk)
        if blk.compression in (_COMP_LZ4, _COMP_LZ4HC):
            return _lz4_decompress(raw, blk.u_size)
        if blk.compression == _COMP_NONE:
            return raw
        raise NotImplementedError(f"block compression {blk.compression} (LZMA) is not supported")


def read_bundle(path: str | Path) -> UnityBundle:
    path = Path(path)
    data = path.read_bytes()
    if not data.startswith(b"UnityFS\x00"):
        raise ValueError(f"{path} is not a UnityFS bundle")
    pos = 8
    version = struct.unpack_from(">I", data, pos)[0]
    pos += 4
    for _ in range(2):  # unity version string + unity revision string
        pos = data.index(b"\x00", pos) + 1
    hdr_pos = pos
    total_size, c_bi, u_bi, flags = struct.unpack_from(">QIII", data, pos)
    pos += 20
    if flags & 0x80:
        raise NotImplementedError("BlocksInfo at end of file is not supported")
    if version >= 7:
        pos = (pos + 15) & ~15
    bi_raw = data[pos : pos + c_bi]
    pos += c_bi
    if flags & 0x200:
        pos = (pos + 15) & ~15
    c_type = flags & 0x3F
    blocks_info = _lz4_decompress(bi_raw, u_bi) if c_type in (_COMP_LZ4, _COMP_LZ4HC) else bi_raw

    bundle = UnityBundle(path, data, version, hdr_pos, total_size, flags, blocks_info)
    count = struct.unpack_from(">I", blocks_info, 16)[0]
    b = 20
    c_off, u_off = pos, 0
    for i in range(count):
        u_size, c_size, bflags = struct.unpack_from(">IIH", blocks_info, b)
        b += 10
        bundle.blocks.append(BundleBlock(i, c_off, c_size, u_off, u_size, bflags))
        c_off += c_size
        u_off += u_size
    return bundle


def decompress(bundle: UnityBundle | str | Path) -> bytes:
    if not isinstance(bundle, UnityBundle):
        bundle = read_bundle(bundle)
    return b"".join(bundle.decompress_block(blk) for blk in bundle.blocks)


def _rebuild(bundle: UnityBundle, new_blocks: dict[int, tuple[bytes, int]]) -> bytes:
    """Re-assemble the bundle; ``new_blocks`` maps block index -> (stored bytes, flags)."""
    bi = bytearray(bundle.blocks_info)
    payload = bytearray()
    b = 20
    for blk in bundle.blocks:
        stored, bflags = new_blocks.get(blk.index, (bundle.block_bytes(blk), blk.flags))
        struct.pack_into(">IIH", bi, b, blk.u_size, len(stored), bflags)
        b += 10
        payload += stored
    c_type = bundle.flags & 0x3F
    bi_stored = _lz4_compress(bytes(bi)) if c_type in (_COMP_LZ4, _COMP_LZ4HC) else bytes(bi)

    out = bytearray(bundle.data[: bundle.header_fields_pos])
    out += b"\x00" * 20  # filled below
    if bundle.version >= 7:
        out += b"\x00" * (-len(out) % 16)
    out += bi_stored
    if bundle.flags & 0x200:
        out += b"\x00" * (-len(out) % 16)
    out += payload
    struct.pack_into(">QIII", out, bundle.header_fields_pos, len(out), len(bi_stored), len(bi), bundle.flags)
    return bytes(out)


def patch_bytes(bundle: UnityBundle, patches: dict[int, bytes]) -> bytes:
    """Return a new bundle file with ``patches`` ({uncompressed_offset: new_bytes}) applied."""
    by_block: dict[int, bytearray] = {}
    for u_off, new in patches.items():
        for k, byte in enumerate(new):
            blk = bundle.block_for(u_off + k)
            buf = by_block.setdefault(blk.index, bytearray(bundle.decompress_block(blk)))
            buf[u_off + k - blk.u_off] = byte
    new_blocks: dict[int, tuple[bytes, int]] = {}
    for idx, buf in by_block.items():
        blk = bundle.blocks[idx]
        if blk.compression in (_COMP_LZ4, _COMP_LZ4HC):
            new_blocks[idx] = (_lz4_compress(bytes(buf)), blk.flags)
        else:
            new_blocks[idx] = (bytes(buf), blk.flags)
    return _rebuild(bundle, new_blocks)


def trace_lz4_byte(block_data: bytes, rel_offset: int) -> tuple[str, int | dict]:
    """Return ("literal", compressed_index) or ("match", {...}) for a decompressed offset."""
    i = out_len = 0
    n = len(block_data)
    while i < n:
        tok = block_data[i]
        i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                v = block_data[i]
                i += 1
                lit += v
                if v != 255:
                    break
        if out_len <= rel_offset < out_len + lit:
            return "literal", i + rel_offset - out_len
        i += lit
        out_len += lit
        if i >= n:
            break
        off = block_data[i] | (block_data[i + 1] << 8)
        i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                v = block_data[i]
                i += 1
                ml += v
                if v != 255:
                    break
        ml += 4
        if out_len <= rel_offset < out_len + ml:
            return "match", {"offset": off, "start": out_len, "length": ml}
        out_len += ml
    return "notfound", -1
