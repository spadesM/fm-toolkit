"""Locate which LZ4 block / compressed byte produces a given uncompressed offset in a UnityFS bundle.

Usage: python bundle_locate_byte.py <bundle_name> <uncompressed_offset_hex> [expected_byte_hex]
"""
import sys, struct
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import use_fm27  # noqa
from fm26save.binary_decompiler import lz4_decompress_block


def parse_bundle(data):
    assert data.startswith(b"UnityFS\x00")
    pos = 8
    ver = struct.unpack_from(">I", data, pos)[0]; pos += 4
    while data[pos]: pos += 1
    pos += 1
    while data[pos]: pos += 1
    pos += 1
    hdr_pos = pos
    total_size, c_bi, u_bi, flags = struct.unpack_from(">QIII", data, pos); pos += 20
    if ver >= 7: pos = (pos + 15) & ~15
    bi_pos = pos
    bi_raw = data[pos: pos + c_bi]; pos += c_bi
    if flags & 0x200: pos = (pos + 15) & ~15
    c_type = flags & 0x3F
    bi = lz4_decompress_block(bi_raw, u_bi) if c_type in (2, 3) else bi_raw
    cnt = struct.unpack_from(">I", bi, 16)[0]
    blocks = []
    b = 20
    cpos, upos = pos, 0
    for _ in range(cnt):
        u, c, f = struct.unpack_from(">IIH", bi, b); b += 10
        blocks.append(dict(c_off=cpos, c_sz=c, u_off=upos, u_sz=u, flags=f))
        cpos += c; upos += u
    return dict(ver=ver, hdr_pos=hdr_pos, total_size=total_size, flags=flags, bi_pos=bi_pos, c_bi=c_bi,
                u_bi=u_bi, bi=bi, blocks=blocks, data_start=pos)


def lz4_trace(src, target):
    """Decode an LZ4 block; return ('literal', src_index) or ('match', ...) for uncompressed index `target`."""
    i, out_len = 0, 0
    n = len(src)
    while i < n:
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255: break
        if out_len <= target < out_len + lit:
            return ("literal", i + (target - out_len))
        i += lit; out_len += lit
        if i >= n: break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        if out_len <= target < out_len + ml:
            return ("match", dict(offset=off, start=out_len, length=ml))
        out_len += ml
    return ("notfound", None)


if __name__ == "__main__":
    bname = sys.argv[1]
    target = int(sys.argv[2], 16)
    path = use_fm27.FM27 / "fm_Data/StreamingAssets/aa/StandaloneWindows64" / bname
    data = path.read_bytes()
    info = parse_bundle(data)
    print(f"ver={info['ver']} total={info['total_size']} filelen={len(data)} flags={info['flags']:#x} blocks={len(info['blocks'])}")
    for bi_, blk in enumerate(info["blocks"]):
        if blk["u_off"] <= target < blk["u_off"] + blk["u_sz"]:
            rel = target - blk["u_off"]
            src = data[blk["c_off"]: blk["c_off"] + blk["c_sz"]]
            print(f"block {bi_}: {blk} rel={rel:#x} type={blk['flags'] & 0x3f}")
            dec = lz4_decompress_block(src, blk["u_sz"]) if blk["flags"] & 0x3f in (2, 3) else src
            print("  context:", dec[rel - 16: rel + 8].hex(" "), "byte=", hex(dec[rel]))
            kind, where = lz4_trace(src, rel) if blk["flags"] & 0x3f in (2, 3) else ("raw", rel)
            print("  trace:", kind, where)
            if kind == "literal":
                print(f"  -> file offset of literal byte: {blk['c_off'] + where:#x} value={data[blk['c_off'] + where]:#x}")
