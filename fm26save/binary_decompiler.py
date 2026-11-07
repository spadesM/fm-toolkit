"""Permanent Binary & Source-Code Reverse-Engineering / Decompiler Engine for FM26 & FM27.

Directly decompiles and extracts:
1. ``global-metadata.dat`` (Unity IL2CPP v31):
   - All 127 C# Assemblies/Images (`FM.UI.dll`, `SI.Bindable.dll`, `FM.Match.dll`, `SI.Match.dll`, `SI.MatchTypes.dll`, `FM.GamePlugin.dll`, `FMGame.dll`, etc.)
   - All 17,691 TypeDefinitions (classes, structs, interfaces, enums)
   - All 752+ FM/SI Enums with exact constant names and integer values
   - All 78,075 Fields, 128,072 Methods (with parameter signatures & tokens), 26,210 Properties, and 29,841 StringLiterals
2. ``GameAssembly.dll`` (x86-64 PE64 Machine Code & IL2CPP CodeGen):
   - O(1) discovery of ``g_CodeGenModules`` (`Il2CppCodeGenModule` method pointer arrays for all 127 assemblies)
   - Chained `.pdata` (`RUNTIME_FUNCTION` + `UNWIND_INFO` with `UNW_FLAG_CHAININFO`) function boundary reconstruction
   - Disassembly of all `PropertyRegistration.Initialise` (`8,270+` FourCC -> Property Name mappings) and `ContextRegistration.Initialise` (`220+` FourCC -> Context Name mappings) across all assemblies via `.data` `Il2CppMetadataUsage` string literal token resolution
   - Disassembly of all `874+` `*Reference` classes (`PersonReference`, `ClubReference`, `TeamReference`, `CompReference`, `StadiumReference`, `ContractReference`, `TacticReference`, etc. — including all 19 `0x4442xxxx` `"DB\\x00\\xXX"` database table entities) to extract the complete Entity -> Properties, Inheritance (`DerivesFromInternal`), Parameterized Properties, Contexts (`GetContextsInternal`), and Child Entity References (`GetPropertyTypeInternal`) dependency graph
3. ``il2cpp.usym`` (Unity Symbol Table v2):
   - Parses the 24-byte v2 header + 1,593,548 x 24-byte symbol records + string table to reconstruct the 2,619 original Sports Interactive TeamCity C# source files (`C:/TeamCity/work/.../*.cs`) and RVA-to-line mappings
4. ``tables.fmf`` & ``simatch.fmf`` Binary Lookup Tables:
   - ``tables/jumping_reach.jsb`` & ``tables/aerial_reach.jsb`` (height-to-reach 1..20 conversion tables for male & female players)
   - ``simatch/qme_stat_relevant_attribute_data.jsb`` (Quick Match Engine stat -> governing attributes)
   - ``simatch/player_ratings_data.jsb`` (11 match expectation multipliers + 32 role profiles x 52 event rating coefficients)
   - ``simatch/oop_attributes_scoring.jsb`` (Out-Of-Possession RolePosition bitmask -> attribute IDs)
   - ``simatch/weights.jsb`` (Frame #223 master `TEAM_PICKING_STYLE` weights across all 4 squad rotation profiles)
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import struct
from pathlib import Path
from typing import Any

from fm26save.formulas import extract_fmf_frames, parse_jsb, read_fmf_directory

DEFAULT_FM_PATHS: tuple[Path, ...] = (
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 26"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Football Manager 27"),
)


def resolve_fm_install_dir(fm_install_dir: str | os.PathLike[str] | None = None) -> Path:
    """Locate the Football Manager 26 / 27 installation directory.

    Resolution order: explicit ``fm_install_dir`` -> ``FM_INSTALL_DIR`` environment variable ->
    :data:`DEFAULT_FM_PATHS` (FM26 first, then FM27). When both games are installed, pass
    ``fm_install_dir`` (CLI: ``--fm-dir``) or set ``FM_INSTALL_DIR`` to target FM27 explicitly.
    """
    if fm_install_dir is not None:
        p = Path(fm_install_dir)
        if p.exists():
            return p
    env_dir = os.environ.get("FM_INSTALL_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)
    for cand in DEFAULT_FM_PATHS:
        if cand.exists():
            return cand
    raise FileNotFoundError("Football Manager 26/27 installation directory not found.")


def fourcc_to_ascii(u32: int) -> str:
    """Convert a 32-bit FourCC integer to printable ASCII or hex representation."""
    b = struct.pack(">I", u32)
    if all(32 <= c < 127 for c in b):
        return b.decode("ascii")
    b_le = struct.pack("<I", u32)
    if all(32 <= c < 127 for c in b_le):
        return b_le.decode("ascii")
    return f"0x{u32:08x}"


# ==============================================================================
# 1. GLOBAL-METADATA.DAT (IL2CPP v31 & v39) DECOMPILER
# ==============================================================================


def _parse_metadata_header(meta: bytes) -> dict[str, int]:
    """Return version-normalized offsets, sizes, and entry sizes for IL2CPP v31 (FM26) and v39 (FM27)."""
    sanity, version = struct.unpack_from("<II", meta, 0)
    if version >= 38:
        # IL2CPP v39 (Unity 6000.3+ / FM27): (offset, size, count) 3-tuples after (sanity, version)
        hdr = struct.unpack_from("<80I", meta, 0)
        return {
            "sanity": sanity,
            "version": version,
            "str_lit_off": hdr[2],
            "str_lit_sz": hdr[3],
            "str_lit_cnt": hdr[4],
            "str_lit_data_off": hdr[5],
            "str_lit_data_sz": hdr[6],
            "str_off": hdr[8],
            "str_sz": hdr[9],
            "events_off": hdr[11],
            "events_sz": hdr[12],
            "props_off": hdr[14],
            "props_sz": hdr[15],
            "methods_off": hdr[17],
            "methods_sz": hdr[18],
            "param_def_off": hdr[20],
            "param_def_sz": hdr[21],
            "field_def_off": hdr[23],
            "field_def_sz": hdr[24],
            "def_data_off": hdr[26],
            "def_data_sz": hdr[27],
            "params_off": hdr[32],
            "params_sz": hdr[33],
            "fields_off": hdr[35],
            "fields_sz": hdr[36],
            "types_off": hdr[59],
            "types_sz": hdr[60],
            "images_off": hdr[62],
            "images_sz": hdr[63],
            "image_stride": 36,
            "type_stride": 76,
            "method_stride": 30,
            "field_stride": 10,
            "param_stride": 10,
            "prop_stride": 20,
            "field_def_stride": 10,
        }
    hdr = struct.unpack_from("<64I", meta, 0)
    return {
        "sanity": sanity,
        "version": version,
        "str_lit_off": hdr[2],
        "str_lit_sz": hdr[3],
        "str_lit_cnt": hdr[3] // 8,
        "str_lit_data_off": hdr[4],
        "str_lit_data_sz": hdr[5],
        "str_off": hdr[6],
        "str_sz": hdr[7],
        "events_off": hdr[8],
        "events_sz": hdr[9],
        "props_off": hdr[10],
        "props_sz": hdr[11],
        "methods_off": hdr[12],
        "methods_sz": hdr[13],
        "param_def_off": hdr[14],
        "param_def_sz": hdr[15],
        "field_def_off": hdr[16],
        "field_def_sz": hdr[17],
        "def_data_off": hdr[18],
        "def_data_sz": hdr[19],
        "params_off": hdr[22],
        "params_sz": hdr[23],
        "fields_off": hdr[24],
        "fields_sz": hdr[25],
        "types_off": hdr[40],
        "types_sz": hdr[41],
        "images_off": hdr[42],
        "images_sz": hdr[43],
        "image_stride": 40,
        "type_stride": 88,
        "method_stride": 36,
        "field_stride": 12,
        "param_stride": 12,
        "prop_stride": 20,
        "field_def_stride": 12,
    }


def _extract_string_literals(meta: bytes, mh: dict[str, int]) -> list[str]:
    str_lit_off = mh["str_lit_off"]
    str_lit_data_off = mh["str_lit_data_off"]
    if mh["version"] >= 38:
        cnt = mh["str_lit_cnt"]
        if cnt <= 1:
            return []
        offsets = struct.unpack_from(f"<{cnt}I", meta, str_lit_off)
        return [
            meta[str_lit_data_off + offsets[i] : str_lit_data_off + offsets[i + 1]].decode("utf-8", errors="replace")
            for i in range(cnt - 1)
        ]
    lit_cnt = mh["str_lit_sz"] // 8
    return [
        meta[str_lit_data_off + data_idx : str_lit_data_off + data_idx + length].decode("utf-8", errors="replace")
        for length, data_idx in (struct.unpack_from("<II", meta, str_lit_off + i * 8) for i in range(lit_cnt))
    ]


def decompile_global_metadata(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    include_all_methods: bool = False,
    filter_namespace_or_image: str | None = None,
) -> dict[str, Any]:
    """Decompile ``global-metadata.dat`` (IL2CPP v31 in FM26 / v39 in FM27) into structured assemblies, types, enums, fields, methods, properties, and string literals."""
    root = resolve_fm_install_dir(fm_install_dir)
    meta_path = root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat"
    if not meta_path.exists() and root.name == "global-metadata.dat":
        meta_path = root
    meta = meta_path.read_bytes()

    mh = _parse_metadata_header(meta)
    sanity, version = mh["sanity"], mh["version"]
    is_v39 = version >= 38
    str_off, str_sz = mh["str_off"], mh["str_sz"]
    props_off, props_sz = mh["props_off"], mh["props_sz"]
    methods_off, methods_sz = mh["methods_off"], mh["methods_sz"]
    field_def_off, field_def_sz = mh["field_def_off"], mh["field_def_sz"]
    def_data_off, def_data_sz = mh["def_data_off"], mh["def_data_sz"]
    params_off, params_sz = mh["params_off"], mh["params_sz"]
    fields_off, fields_sz = mh["fields_off"], mh["fields_sz"]
    types_off, types_sz = mh["types_off"], mh["types_sz"]
    images_off, images_sz = mh["images_off"], mh["images_sz"]
    image_stride = mh["image_stride"]
    type_stride = mh["type_stride"]
    method_stride = mh["method_stride"]
    field_stride = mh["field_stride"]
    param_stride = mh["param_stride"]
    prop_stride = mh["prop_stride"]
    field_def_stride = mh["field_def_stride"]

    def get_mstr(off: int) -> str:
        if off < 0 or off >= str_sz:
            return ""
        end = meta.find(b"\x00", str_off + off)
        return meta[str_off + off : end].decode("utf-8", errors="replace")

    # 1. String Literals
    string_literals = _extract_string_literals(meta, mh)
    lit_cnt = len(string_literals)

    # 2. Field Default Values
    def _read_compressed_int(pos: int) -> int:
        if pos < 0 or pos >= def_data_sz:
            return 0
        p = def_data_off + pos
        b0 = meta[p]
        if (b0 & 0x80) == 0:
            return b0
        if (b0 & 0xC0) == 0x80:
            return ((b0 & 0x3F) << 8) | meta[p + 1]
        if (b0 & 0xE0) == 0xC0:
            return ((b0 & 0x1F) << 24) | (meta[p + 1] << 16) | (meta[p + 2] << 8) | meta[p + 3]
        if b0 == 0xF0:
            return struct.unpack_from("<i", meta, p + 1)[0]
        if b0 == 0xFE:
            return -2
        if b0 == 0xFF:
            return -1
        return b0

    field_defaults: dict[int, int] = {}
    fd_fmt = "<iHi" if is_v39 else "<iii"
    for i in range(field_def_sz // field_def_stride):
        f_idx, _t_idx, d_idx = struct.unpack_from(fd_fmt, meta, field_def_off + i * field_def_stride)
        if d_idx >= 0:
            field_defaults[f_idx] = _read_compressed_int(d_idx)

    # 3. Images / Assemblies (40 bytes in v31; 36 bytes in v39)
    images: list[dict[str, Any]] = []
    type_to_image: dict[int, str] = {}
    for img_i in range(images_sz // image_stride):
        base_img = images_off + img_i * image_stride
        if is_v39:
            name_i, asm_i, t_start, t_cnt = struct.unpack_from("<iiHH", meta, base_img)
            ep_idx, tok_u = struct.unpack_from("<iI", meta, base_img + 20)
        else:
            u = struct.unpack_from("<10i", meta, base_img)
            name_i, asm_i, t_start, t_cnt, ep_idx, tok_u = u[0], u[1], u[2], u[3], u[6], u[7] & 0xFFFFFFFF
        iname = get_mstr(name_i)
        images.append(
            {
                "image_index": img_i,
                "name": iname,
                "assembly_index": asm_i,
                "type_start": t_start,
                "type_count": t_cnt,
                "entry_point_index": ep_idx,
                "token": f"0x{tok_u:08x}",
            }
        )
        for ti in range(t_start, t_start + t_cnt):
            type_to_image[ti] = iname

    # 4. Types (88 bytes in v31; 76 bytes in v39), Enums, Fields, Properties, Methods
    types_list: list[dict[str, Any]] = []
    enums_dict: dict[str, dict[str, Any]] = {}
    num_types = types_sz // type_stride

    for ti in range(num_types):
        base_td = types_off + ti * type_stride
        if is_v39:
            tu = struct.unpack_from("<13i8Hii", meta, base_td)
            tname = get_mstr(tu[0])
            tnamespace = get_mstr(tu[1])
            f_start_v = tu[5]
            m_start_v = tu[6]
            p_start_v = tu[8]
            m_cnt_v = tu[13]
            p_cnt_v = tu[14]
            f_cnt_v = tu[15]
            bitfield_v = tu[21]
        else:
            u = struct.unpack_from("<22i", meta, base_td)
            tname = get_mstr(u[0])
            tnamespace = get_mstr(u[1])
            f_start_v = u[8]
            m_start_v = u[9]
            p_start_v = u[11]
            m_cnt_v = u[16] & 0xFFFF
            p_cnt_v = (u[16] >> 16) & 0xFFFF
            f_cnt_v = u[17] & 0xFFFF
            bitfield_v = u[20]

        iname = type_to_image.get(ti, "")
        full_name = f"{tnamespace}.{tname}" if tnamespace else tname

        if filter_namespace_or_image:
            flt = filter_namespace_or_image.lower()
            if flt not in full_name.lower() and flt not in iname.lower():
                continue

        is_enum = bool((bitfield_v >> 1) & 1)
        is_valuetype = bool(bitfield_v & 1)

        fields: list[dict[str, Any]] = []
        if f_start_v >= 0 and f_cnt_v > 0:
            for fi in range(f_start_v, f_start_v + f_cnt_v):
                if (fi + 1) * field_stride <= fields_sz:
                    if is_v39:
                        fni, fti, ftok_hi = struct.unpack_from("<iiH", meta, fields_off + fi * field_stride)
                        ftok = (ftok_hi << 16) | ((fi + 1) & 0xFFFF)
                    else:
                        fni, fti, ftok = struct.unpack_from("<iiI", meta, fields_off + fi * field_stride)
                    fname = get_mstr(fni)
                    f_entry: dict[str, Any] = {"name": fname, "type_index": fti, "token": f"0x{ftok:08x}"}
                    if fi in field_defaults:
                        f_entry["default_value"] = field_defaults[fi]
                    fields.append(f_entry)

        if is_enum and fields:
            enum_vals = {}
            for idx_f, f_entry in enumerate(fields):
                if f_entry["name"] == "value__":
                    continue
                enum_vals[f_entry["name"]] = f_entry.get("default_value", idx_f - 1)
            enums_dict[f"{iname}::{full_name}"] = {
                "image": iname,
                "namespace": tnamespace,
                "name": tname,
                "full_name": full_name,
                "values": enum_vals,
            }

        props: list[str] = []
        if p_start_v >= 0 and p_cnt_v > 0:
            for pi in range(p_start_v, p_start_v + p_cnt_v):
                if (pi + 1) * prop_stride <= props_sz:
                    pni = struct.unpack_from("<i", meta, props_off + pi * prop_stride)[0]
                    props.append(get_mstr(pni))

        methods: list[dict[str, Any]] = []
        if (
            include_all_methods
            or any(k in iname for k in ("FM", "SI.", "Assembly-CSharp", "SceneLoadTest"))
        ) and m_start_v >= 0 and m_cnt_v > 0:
            for mi in range(m_start_v, m_start_v + m_cnt_v):
                if (mi + 1) * method_stride <= methods_sz:
                    if is_v39:
                        mu = struct.unpack_from("<iiiihIHHHH", meta, methods_off + mi * method_stride)
                        mname = get_mstr(mu[0])
                        param_start = mu[3]
                        mtok = mu[5]
                        param_cnt = mu[9]
                    else:
                        mu = struct.unpack_from("<7i4H", meta, methods_off + mi * method_stride)
                        mname = get_mstr(mu[0])
                        param_start = mu[4]
                        mtok = mu[6] & 0xFFFFFFFF
                        param_cnt = mu[10]
                    params: list[str] = []
                    if param_start >= 0 and param_cnt > 0:
                        for pmi in range(param_start, param_start + param_cnt):
                            if (pmi + 1) * param_stride <= params_sz:
                                pm_ni = struct.unpack_from("<i", meta, params_off + pmi * param_stride)[0]
                                params.append(get_mstr(pm_ni))
                    methods.append(
                        {
                            "method_index": mi,
                            "name": mname,
                            "token": f"0x{mtok:08x}",
                            "rid": mtok & 0x00FFFFFF,
                            "parameters": params,
                        }
                    )

        types_list.append(
            {
                "type_index": ti,
                "image": iname,
                "namespace": tnamespace,
                "name": tname,
                "full_name": full_name,
                "is_enum": is_enum,
                "is_valuetype": is_valuetype,
                "field_count": f_cnt_v,
                "method_count": m_cnt_v,
                "property_count": p_cnt_v,
                "fields": fields,
                "properties": props,
                "methods": methods,
            }
        )

    return {
        "metadata_path": str(meta_path),
        "sanity": f"0x{sanity:08x}",
        "version": version,
        "counts": {
            "images": images_sz // image_stride,
            "types": num_types,
            "enums": len(enums_dict),
            "fields": fields_sz // field_stride,
            "methods": methods_sz // method_stride,
            "properties": props_sz // prop_stride,
            "parameters": params_sz // param_stride,
            "string_literals": lit_cnt,
        },
        "images": images,
        "enums": enums_dict,
        "types": types_list,
        "string_literals_sample": string_literals[:250],
    }


# ==============================================================================
# 2. GAMEASSEMBLY.DLL (X86-64 DISASSEMBLER & BINDABLE REFERENCE GRAPH EXTRACTOR)
# ==============================================================================


def decompile_gameassembly_bindings(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Disassemble ``GameAssembly.dll`` and ``global-metadata.dat`` to extract:
    - All ``Il2CppCodeGenModule`` method pointer tables
    - All FourCC -> Property Name registrations (`PropertyRegistration.Initialise`)
    - All FourCC -> Context Name registrations (`ContextRegistration.Initialise`)
    - All ``*Reference`` classes (`PersonReference`, `ClubReference`, `StadiumReference`, etc.)
      with their Entity FourCC ID, `DerivesFrom`, `Properties`, `ParameterizedProperties`, `Contexts`,
      and `ChildEntityReferences` (`GetPropertyTypeInternal`).
    """
    root = resolve_fm_install_dir(fm_install_dir)
    ga_path = root / "GameAssembly.dll"
    meta_path = root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat"
    pe = ga_path.read_bytes()
    meta = meta_path.read_bytes()

    mh = _parse_metadata_header(meta)
    is_v39 = mh["version"] >= 38
    str_off, str_sz = mh["str_off"], mh["str_sz"]
    methods_off, _methods_sz = mh["methods_off"], mh["methods_sz"]
    types_off, _types_sz = mh["types_off"], mh["types_sz"]
    images_off, images_sz = mh["images_off"], mh["images_sz"]
    image_stride = mh["image_stride"]
    type_stride = mh["type_stride"]
    method_stride = mh["method_stride"]

    literals = _extract_string_literals(meta, mh)

    def get_mstr(off: int) -> str:
        if off < 0 or off >= str_sz:
            return ""
        end = meta.find(b"\x00", str_off + off)
        return meta[str_off + off : end].decode("utf-8", errors="replace")

    # Parse PE64 Sections
    e_lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
    num_sec = struct.unpack_from("<H", pe, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", pe, e_lfanew + 20)[0]
    image_base = struct.unpack_from("<Q", pe, e_lfanew + 24 + 24)[0]
    sec_off = e_lfanew + 24 + opt_size
    sections: list[tuple[str, int, int, int, int]] = []
    for i in range(num_sec):
        s = pe[sec_off + i * 40 : sec_off + (i + 1) * 40]
        name = s[:8].rstrip(b"\x00").decode("ascii", errors="replace")
        vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
        sections.append((name, vaddr, vsize, raddr, rsize))

    def off_to_va(off: int) -> int:
        for _, vaddr, _, raddr, rsize in sections:
            if raddr <= off < raddr + rsize:
                return image_base + vaddr + (off - raddr)
        return 0

    def va_to_off(va: int) -> int:
        rva = va - image_base
        for _, vaddr, vsize, raddr, rsize in sections:
            if vaddr <= rva < vaddr + max(vsize, rsize):
                off = raddr + (rva - vaddr)
                return off if off < raddr + rsize else -2
        return -1

    def resolve_string_literal_va(va: int) -> str:
        foff = va_to_off(va)
        if foff < 0:
            return ""
        val = struct.unpack_from("<I", pe, foff)[0]
        if (val >> 29) == 5 and (val & 1) == 1:
            lit_idx = (val & 0x1FFFFFFF) >> 1
            if 0 <= lit_idx < len(literals):
                return literals[lit_idx]
        return ""

    # Reconstruct exact function boundaries from chained .pdata entries
    pdata_sec = [s for s in sections if s[0] == ".pdata"][0]
    pdata = pe[pdata_sec[3] : pdata_sec[3] + pdata_sec[4]]
    rva_to_end: dict[int, int] = {}
    cur_start: int | None = None
    for i in range(0, len(pdata), 12):
        b_rva, e_rva, u_rva = struct.unpack_from("<III", pdata, i)
        if b_rva == 0:
            continue
        u_off = va_to_off(image_base + u_rva)
        flags = (pe[u_off] >> 3) if u_off >= 0 else 0
        if (flags & 4) and cur_start is not None and b_rva == rva_to_end[cur_start]:
            rva_to_end[cur_start] = e_rva
        else:
            cur_start = b_rva
            rva_to_end[cur_start] = e_rva

    # Locate g_CodeGenModules in O(1) via "FM.UI.dll\x00"
    fm_ui_str_off = pe.find(b"\x00FM.UI.dll\x00") + 1
    fm_ui_mod_off = pe.find(struct.pack("<Q", off_to_va(fm_ui_str_off)))
    ptr_in_array_off = pe.find(struct.pack("<Q", off_to_va(fm_ui_mod_off)))
    start_arr = ptr_in_array_off
    while start_arr >= 8:
        cand_va = struct.unpack_from("<Q", pe, start_arr - 8)[0]
        cand_off = va_to_off(cand_va)
        if cand_off > 0:
            name_off = va_to_off(struct.unpack_from("<Q", pe, cand_off)[0])
            if name_off > 0 and b".dll" in pe[name_off : name_off + 64]:
                start_arr -= 8
                continue
        break

    modules: dict[str, tuple[int, int, int]] = {}
    cur = start_arr
    while True:
        cand_va = struct.unpack_from("<Q", pe, cur)[0]
        cand_off = va_to_off(cand_va)
        if cand_off <= 0:
            break
        name_va, m_cnt, m_ptrs_va = struct.unpack_from("<QQQ", pe, cand_off)
        name_off = va_to_off(name_va)
        if name_off <= 0:
            break
        end = pe.find(b"\x00", name_off)
        mname = pe[name_off : end].decode("utf-8", errors="replace")
        if not (mname.endswith(".dll") or mname == "__Generated"):
            break
        modules[mname] = (cand_off, m_cnt, m_ptrs_va)
        cur += 8

    # Decode PropertyRegistration.Initialise & ContextRegistration.Initialise across all assemblies
    prop_map: dict[int, str] = {}
    prop_assembly_map: dict[int, str] = {}
    ctx_map: dict[int, str] = {}
    ctx_assembly_map: dict[int, str] = {}

    def _unpack_img(img_i: int) -> tuple[str, int, int]:
        base_img = images_off + img_i * image_stride
        if is_v39:
            name_i, _asm_i, t_start, t_cnt = struct.unpack_from("<iiHH", meta, base_img)
        else:
            iu = struct.unpack_from("<10i", meta, base_img)
            name_i, t_start, t_cnt = iu[0], iu[2], iu[3]
        return get_mstr(name_i), t_start, t_cnt

    def _unpack_td(ti: int) -> tuple[str, str, int, int]:
        base_td = types_off + ti * type_stride
        if is_v39:
            tu = struct.unpack_from("<13i8Hii", meta, base_td)
            return get_mstr(tu[0]), get_mstr(tu[1]), tu[6], tu[13]
        tu = struct.unpack_from("<22i", meta, base_td)
        return get_mstr(tu[0]), get_mstr(tu[1]), tu[9], tu[16] & 0xFFFF

    def _unpack_md(mi: int) -> tuple[str, int]:
        base_md = methods_off + mi * method_stride
        if is_v39:
            mu = struct.unpack_from("<iiiihIHHHH", meta, base_md)
            return get_mstr(mu[0]), (mu[5] & 0xFFFFFF) - 1
        mu = struct.unpack_from("<7i4H", meta, base_md)
        return get_mstr(mu[0]), (mu[6] & 0xFFFFFF) - 1

    for img_i in range(images_sz // image_stride):
        iname, t_start, t_cnt = _unpack_img(img_i)
        if iname not in modules:
            continue
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        if ptrs_off < 0 or m_cnt_mod == 0:
            continue
        for ti in range(t_start, t_start + t_cnt):
            tname, _tnamespace, m_start, m_cnt = _unpack_td(ti)
            if tname in ("PropertyRegistration", "ContextRegistration"):
                for mi in range(m_start, m_start + m_cnt):
                    mname, rid = _unpack_md(mi)
                    if mname == "Initialise":
                        if not (0 <= rid < m_cnt_mod):
                            continue
                        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                        if va == 0:
                            continue
                        rva = va - image_base
                        end_rva = rva_to_end.get(rva, rva + 256)
                        foff = va_to_off(va)
                        code = pe[foff : foff + (end_rva - rva)]
                        for m in re.finditer(rb"\x33\xd2\xb9(....)\xe8....", code, re.DOTALL):
                            pos = m.start()
                            u32 = struct.unpack("<I", m.group(1))[0]
                            window = code[pos : pos + 130]
                            m_r8 = re.search(rb"\x4c\x8b\x05(....)", window, re.DOTALL)
                            if m_r8:
                                r8_va = va + pos + m_r8.end() + struct.unpack("<i", m_r8.group(1))[0]
                                s = resolve_string_literal_va(r8_va)
                                if s:
                                    if tname == "PropertyRegistration":
                                        prop_map[u32] = s
                                        prop_assembly_map[u32] = iname
                                    else:
                                        ctx_map[u32] = s
                                        ctx_assembly_map[u32] = iname

    # Pass 1 over all *Reference classes across all assemblies to map Entity FourCC -> Reference Class Name
    entity_id_to_class: dict[int, str] = {}
    ref_candidates: list[tuple[str, int, str, str, int, int, int, int]] = []

    for img_i in range(images_sz // image_stride):
        iname, t_start, t_cnt = _unpack_img(img_i)
        if iname not in modules:
            continue
        _, m_cnt_mod, m_ptrs_va = modules[iname]
        ptrs_off = va_to_off(m_ptrs_va)
        if ptrs_off < 0 or m_cnt_mod == 0:
            continue
        for ti in range(t_start, t_start + t_cnt):
            tname, tnamespace, m_start, m_cnt = _unpack_td(ti)
            if not tname.endswith("Reference"):
                continue
            if m_cnt == 0:
                continue
            ref_candidates.append((iname, ti, tnamespace, tname, m_start, m_cnt, ptrs_off, m_cnt_mod))
            for mi in range(m_start, m_start + m_cnt):
                mname, rid = _unpack_md(mi)
                if mname in ("get_ID", "get_Identifier"):
                    if 0 <= rid < m_cnt_mod:
                        va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
                        if va > 0:
                            foff = va_to_off(va)
                            mcode = pe[foff : foff + 16]
                            if len(mcode) >= 5 and mcode[0] == 0xB8:
                                eid = struct.unpack_from("<I", mcode, 1)[0]
                                entity_id_to_class[eid] = tname
                                break

    # Pass 2: Decode full property, inheritance, context, and child-entity graph for every *Reference class
    reference_classes: dict[str, dict[str, Any]] = {}
    db_table_entities: list[dict[str, Any]] = []
    property_to_entities: dict[str, list[str]] = {}

    for iname, ti, tnamespace, tname, m_start, m_cnt, ptrs_off, m_cnt_mod in ref_candidates:
        ref_id = 0
        prop_count_declared = 0
        props_list: list[str] = []
        parameterized_props: list[str] = []
        ctxs_list: list[str] = []
        derives_list: list[str] = []
        child_entity_refs: list[str] = []

        for mi in range(m_start, m_start + m_cnt):
            mname, rid = _unpack_md(mi)
            if not (0 <= rid < m_cnt_mod):
                continue
            va = struct.unpack_from("<Q", pe, ptrs_off + rid * 8)[0]
            if va == 0:
                continue
            rva = va - image_base
            end_rva = rva_to_end.get(rva, rva + 64)
            foff = va_to_off(va)
            mcode = pe[foff : foff + (end_rva - rva)]

            if mname in ("get_ID", "get_Identifier") and len(mcode) >= 5 and mcode[0] == 0xB8:
                ref_id = struct.unpack_from("<I", mcode, 1)[0]
            elif mname == "GetPropertyCountInternal" and len(mcode) >= 5 and mcode[0] == 0xB8:
                prop_count_declared = struct.unpack_from("<I", mcode, 1)[0]
            elif mname == "GetPropertiesInternal":
                for pm in re.finditer(rb"\x33\xd2\xb9(....)\xe8", mcode, re.DOTALL):
                    pu32 = struct.unpack("<I", pm.group(1))[0]
                    pname = prop_map.get(pu32, f"0x{pu32:08x}")
                    props_list.append(pname)
                    property_to_entities.setdefault(pname, []).append(tname)
            elif mname == "GetContextsInternal":
                for cm in re.finditer(rb"\xba(....)", mcode, re.DOTALL):
                    cu32 = struct.unpack("<I", cm.group(1))[0]
                    if cu32 in ctx_map and ctx_map[cu32] not in ctxs_list:
                        ctxs_list.append(ctx_map[cu32])
                for pm in re.finditer(rb"\x81\xff(....)", mcode, re.DOTALL):
                    pu32 = struct.unpack("<I", pm.group(1))[0]
                    if pu32 in prop_map and prop_map[pu32] not in parameterized_props:
                        parameterized_props.append(prop_map[pu32])
            elif mname == "DerivesFromInternal":
                for dm in re.finditer(rb"\x81\xf9(....)", mcode, re.DOTALL):
                    du32 = struct.unpack("<I", dm.group(1))[0]
                    dname = entity_id_to_class.get(du32, fourcc_to_ascii(du32))
                    if dname not in derives_list:
                        derives_list.append(dname)
            elif mname == "GetPropertyTypeInternal":
                for tm in re.finditer(rb"\x33\xd2\xb9(....)\xe8", mcode, re.DOTALL):
                    tu32 = struct.unpack("<I", tm.group(1))[0]
                    target_cls = entity_id_to_class.get(tu32)
                    if target_cls and target_cls not in child_entity_refs:
                        child_entity_refs.append(target_cls)

        if ref_id == 0 and not props_list and not derives_list:
            continue

        is_db_table = (ref_id & 0xFFFF0000) == 0x44420000
        entry = {
            "class_name": tname,
            "namespace": tnamespace,
            "assembly": iname,
            "entity_id_hex": f"0x{ref_id:08x}",
            "entity_fourcc": fourcc_to_ascii(ref_id),
            "is_core_db_table": is_db_table,
            "db_table_index": (ref_id & 0xFFFF) if is_db_table else None,
            "property_count": len(props_list) or prop_count_declared,
            "derives_from": derives_list,
            "properties": props_list,
            "parameterized_properties": parameterized_props,
            "contexts": ctxs_list,
            "child_entity_references": child_entity_refs,
        }
        reference_classes[tname] = entry
        if is_db_table:
            db_table_entities.append(entry)

    db_table_entities.sort(key=lambda x: x["db_table_index"] or 0)

    return {
        "gameassembly_path": str(ga_path),
        "image_base": f"0x{image_base:x}",
        "counts": {
            "codegen_modules": len(modules),
            "registered_properties": len(prop_map),
            "registered_contexts": len(ctx_map),
            "reference_entities": len(reference_classes),
            "core_db_table_entities": len(db_table_entities),
        },
        "codegen_modules": {
            k: {"file_offset": v[0], "method_count": v[1], "method_pointers_va": f"0x{v[2]:x}"}
            for k, v in modules.items()
        },
        "properties": {
            f"0x{k:08x}": {"name": v, "fourcc": fourcc_to_ascii(k), "assembly": prop_assembly_map.get(k, "")}
            for k, v in prop_map.items()
        },
        "contexts": {
            f"0x{k:08x}": {"name": v, "fourcc": fourcc_to_ascii(k), "assembly": ctx_assembly_map.get(k, "")}
            for k, v in ctx_map.items()
        },
        "core_db_table_entities": db_table_entities,
        "reference_classes": reference_classes,
        "property_to_entities": property_to_entities,
    }


# ==============================================================================
# 3. IL2CPP.USYM (UNITY SYMBOL TABLE v2) DECOMPILER
# ==============================================================================


def decompile_usym_symbols(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    max_records: int | None = None,
    filter_substr: str | None = None,
) -> dict[str, Any]:
    """Parse ``il2cpp.usym`` v2 (`1,593,548` symbol records + string table) to extract SI's original C# source file tree and RVA-to-line mappings."""
    root = resolve_fm_install_dir(fm_install_dir)
    usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
    if not usym_path.exists():
        usym_path = root / "il2cpp.usym"
    data = usym_path.read_bytes()

    magic, version, sym_count, _, _, _ = struct.unpack_from("<4sIIIII", data, 0)
    if magic != b"sym-":
        raise ValueError(f"Unexpected il2cpp.usym magic: {magic!r}")

    records_off = 24
    str_table_off = records_off + sym_count * 24
    str_blob = data[str_table_off:]

    def get_ustr(off: int) -> str:
        if off <= 0 or off >= len(str_blob):
            return ""
        end = str_blob.find(b"\x00", off)
        return str_blob[off:end].decode("utf-8", errors="replace")

    # Pre-build offset -> string map from the string table in O(N_str)
    file_map: dict[int, str] = {}
    pos = 0
    all_usym_strs: list[str] = []
    for raw_part in str_blob.split(b"\x00"):
        if raw_part:
            decoded = raw_part.decode("utf-8", errors="replace")
            file_map[pos] = decoded
            all_usym_strs.append(decoded)
        pos += len(raw_part) + 1

    source_files = [s for s in all_usym_strs if s.endswith((".cs", ".cpp", ".h", ".hpp", ".c", ".cc", ".inl"))]

    # Map every compiled C# method_index (in hybrid IL2CPP v31/v39 usym) to its GameAssembly RVA range & .cs source file
    mv = memoryview(data)[records_off:str_table_off]
    method_rva_map: dict[int, list[int]] = {}
    for rva_u64, method_idx, file_off, line, parent_idx in struct.iter_unpack("<QIIII", mv):
        if method_idx == 0xFFFFFFFF or parent_idx != 0xFFFFFFFF:
            continue
        cur = method_rva_map.get(method_idx)
        if cur is None:
            method_rva_map[method_idx] = [rva_u64, rva_u64, file_off, line, line]
        else:
            if rva_u64 < cur[0]:
                cur[0] = rva_u64
            if rva_u64 > cur[1]:
                cur[1] = rva_u64
            if cur[2] == 0xFFFFFFFF and file_off != 0xFFFFFFFF:
                cur[2] = file_off
            if line != 0xFFFFFFFF:
                if cur[3] == 0xFFFFFFFF or line < cur[3]:
                    cur[3] = line
                if cur[4] == 0xFFFFFFFF or line > cur[4]:
                    cur[4] = line

    # Sample or filter symbol records (24 bytes each: <QIIII -> rva_u64, method_index_or_sym, file_str_off, line, parent_idx)
    limit = min(sym_count, max_records) if max_records is not None else min(sym_count, 5000)
    records: list[dict[str, Any]] = []
    flt = filter_substr.lower() if filter_substr else None

    scan_limit = sym_count if flt else limit
    for i in range(scan_limit):
        rva_u64, method_or_sym, file_off, line, parent_idx = struct.unpack_from("<QIIII", data, records_off + i * 24)
        file_name = file_map.get(file_off, get_ustr(file_off)) if file_off != 0xFFFFFFFF else ""
        sym_name = f"method_index:{method_or_sym}" if method_or_sym != 0xFFFFFFFF else ""
        if flt and flt not in sym_name.lower() and flt not in file_name.lower():
            continue
        records.append(
            {
                "index": i,
                "rva": f"0x{rva_u64:08x}",
                "method_index": None if method_or_sym == 0xFFFFFFFF else method_or_sym,
                "parent": None if parent_idx == 0xFFFFFFFF else parent_idx,
                "symbol": sym_name,
                "source_file": file_name,
                "line": None if line == 0xFFFFFFFF else line,
            }
        )
        if len(records) >= limit:
            break

    return {
        "usym_path": str(usym_path),
        "version": version,
        "symbol_count": sym_count,
        "mapped_csharp_method_count": len(method_rva_map),
        "string_table_offset": str_table_off,
        "string_table_size": len(str_blob),
        "source_file_count": len(source_files),
        "source_files": source_files,
        "records_sample": records,
        "_method_rva_map": {
            mid: {
                "rva_start": f"0x{vals[0]:08x}",
                "rva_end": f"0x{vals[1]:08x}",
                "source_file": file_map.get(vals[2], "") if vals[2] != 0xFFFFFFFF else "",
                "line_start": None if vals[3] == 0xFFFFFFFF else vals[3],
                "line_end": None if vals[4] == 0xFFFFFFFF else vals[4],
            }
            for mid, vals in method_rva_map.items()
        },
    }


# ==============================================================================
# 4. ENGINE BINARY LOOKUP TABLES (TABLES.FMF, SIMATCH.FMF, TRAINING.FMF, SIMATCHSHARED.FMF)
# ==============================================================================


def extract_engine_lookup_tables(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decode the compiled simulation, training, and match engine lookup tables from ``tables.fmf``,
    ``simatch.fmf``, ``training.fmf``, and ``simatchshared.fmf``."""
    root = resolve_fm_install_dir(fm_install_dir)
    tables_fmf = root / "shared/data/shared/tables.fmf"
    simatch_fmf = root / "shared/data/simatch.fmf"
    training_fmf = root / "data/game_simulation/training.fmf"
    simatchshared_fmf = root / "shared/data/simatchshared.fmf"

    out: dict[str, Any] = {
        "jumping_reach_table": {},
        "aerial_reach_table": {},
        "qme_stat_relevant_attributes": [],
        "oop_attributes_scoring": [],
        "player_ratings_data": {},
        "team_picking_weights_master": {},
        "training_tables": {},
        "simatch_extra_tables": {},
        "simatchshared_tables": {},
    }

    if tables_fmf.exists():
        t_frames = extract_fmf_frames(tables_fmf)
        t_dirs = read_fmf_directory(tables_fmf)
        for idx, d in enumerate(t_dirs):
            nm = d.get("name", "")
            if "jumping_reach.jsb" in nm:
                parsed = parse_jsb(t_frames[idx][1])
                if parsed and isinstance(parsed[0], dict):
                    out["jumping_reach_table"] = parsed[0]
            elif "aerial_reach.jsb" in nm:
                parsed = parse_jsb(t_frames[idx][1])
                if parsed and isinstance(parsed[0], dict):
                    out["aerial_reach_table"] = parsed[0]

    if simatch_fmf.exists():
        s_frames = extract_fmf_frames(simatch_fmf)
        s_dirs = read_fmf_directory(simatch_fmf)
        for idx, d in enumerate(s_dirs):
            nm = d.get("name", "")
            if "qme_stat_relevant_attribute_data.jsb" in nm:
                parsed = parse_jsb(s_frames[idx][1])
                if parsed and isinstance(parsed[0], dict):
                    out["qme_stat_relevant_attributes"] = parsed[0].get("values", [])
            elif "oop_attributes_scoring.jsb" in nm:
                parsed = parse_jsb(s_frames[idx][1])
                if parsed and isinstance(parsed[0], dict):
                    scoring = parsed[0].get("SCORING", [])
                    if scoring:
                        out["oop_attributes_scoring"] = scoring[0].get("SCORES", [])
            elif "player_ratings_data.jsb" in nm:
                parsed = parse_jsb(s_frames[idx][1])
                if parsed and isinstance(parsed[0], dict):
                    vals = parsed[0].get("values", [])
                    if vals:
                        out["player_ratings_data"] = {
                            "expected_score_data": vals[0].get("expected_score_data", []),
                            "role_data_count": len(vals[0].get("role_data", [])),
                            "baseline_role_coefficients": vals[0].get("role_data", [{}])[0].get("coefficients", []),
                        }
            elif nm.endswith("/weights.jsb") or nm == "simatch/weights.jsb":
                parsed = parse_jsb(s_frames[idx][1])
                if parsed and isinstance(parsed[0], dict):
                    w = parsed[0].get("WEIGHTS", [])
                    if w:
                        out["team_picking_weights_master"] = w[0]
            elif nm.endswith(".jsb"):
                parsed = parse_jsb(s_frames[idx][1])
                out["simatch_extra_tables"][nm] = {
                    "size_bytes": len(s_frames[idx][1]),
                    "top_keys": list(parsed[0].keys()) if parsed and isinstance(parsed[0], dict) else [],
                    "preview": parsed[0] if len(s_frames[idx][1]) <= 16384 and parsed else None,
                }

    if training_fmf.exists():
        tr_frames = extract_fmf_frames(training_fmf)
        tr_dirs = read_fmf_directory(training_fmf)
        for idx, d in enumerate(tr_dirs):
            nm = d.get("name", "")
            if nm.endswith(".jsb"):
                parsed = parse_jsb(tr_frames[idx][1])
                out["training_tables"][nm] = {
                    "size_bytes": len(tr_frames[idx][1]),
                    "parsed": parsed[0] if parsed and len(tr_frames[idx][1]) <= 32768 else None,
                    "top_keys": list(parsed[0].keys()) if parsed and isinstance(parsed[0], dict) else [],
                }
            elif nm.endswith(".xml"):
                out["training_tables"][nm] = {
                    "size_bytes": len(tr_frames[idx][1]),
                    "xml_text": tr_frames[idx][1].decode("utf-8-sig", errors="replace"),
                }

    if simatchshared_fmf.exists():
        sh_frames = extract_fmf_frames(simatchshared_fmf)
        sh_dirs = read_fmf_directory(simatchshared_fmf)
        for idx, d in enumerate(sh_dirs):
            nm = d.get("name", "")
            if nm.endswith(".jsb"):
                parsed = parse_jsb(sh_frames[idx][1])
                out["simatchshared_tables"][nm] = {
                    "size_bytes": len(sh_frames[idx][1]),
                    "parsed": parsed[0] if parsed else None,
                }

    return out


# ==============================================================================
# 5. GAME_PLUGIN.DLL (C++ NATIVE CORE EXPORT DIRECTORY & P/INVOKE BRIDGE)
# ==============================================================================


def decompile_game_plugin_exports(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Extract all native C/C++ exported functions and layout signatures from ``game_plugin.dll``
    (``fm_Data/Plugins/x86_64/game_plugin.dll``) and ``lib_burst_generated.dll``."""
    root = resolve_fm_install_dir(fm_install_dir)
    gp_path = root / "fm_Data/Plugins/x86_64/game_plugin.dll"
    burst_path = root / "fm_Data/Plugins/x86_64/lib_burst_generated.dll"

    def _parse_pe_exports(dll_path: Path) -> dict[str, Any]:
        if not dll_path.exists():
            return {"exists": False, "export_count": 0, "exports": []}
        file_sz = dll_path.stat().st_size
        with open(dll_path, "rb") as f:
            hdr_bytes = f.read(4096)
            if len(hdr_bytes) < 0x100:
                return {"exists": True, "path": str(dll_path), "size_bytes": file_sz, "export_count": 0, "exports": []}
            e_lfanew = struct.unpack_from("<I", hdr_bytes, 0x3C)[0]
            num_sec = struct.unpack_from("<H", hdr_bytes, e_lfanew + 6)[0]
            opt_size = struct.unpack_from("<H", hdr_bytes, e_lfanew + 20)[0]
            image_base = struct.unpack_from("<Q", hdr_bytes, e_lfanew + 24 + 24)[0]
            exp_rva, exp_sz = struct.unpack_from("<II", hdr_bytes, e_lfanew + 24 + 112)
            exc_rva, exc_sz = struct.unpack_from("<II", hdr_bytes, e_lfanew + 24 + 112 + 3 * 8)
            sec_off = e_lfanew + 24 + opt_size
            sections: list[tuple[str, int, int, int, int]] = []
            for i in range(num_sec):
                s = hdr_bytes[sec_off + i * 40 : sec_off + (i + 1) * 40]
                name = s[:8].rstrip(b"\x00").decode("ascii", errors="replace")
                vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
                sections.append((name, vaddr, vsize, raddr, rsize))

            def rva_to_off(rva: int) -> int:
                for _, vaddr, vsize, raddr, rsize in sections:
                    if vaddr <= rva < vaddr + max(vsize, rsize):
                        off = raddr + (rva - vaddr)
                        return off if off < file_sz else -1
                return -1

            pdata_info: dict[str, Any] = {
                "pdata_rva": f"0x{exc_rva:08x}",
                "pdata_size_bytes": exc_sz,
                "runtime_function_entries": 0,
                "valid_code_functions": 0,
                "total_code_bytes": 0,
                "largest_functions_top50": [],
            }
            if exc_rva and exc_sz:
                exc_off = rva_to_off(exc_rva)
                if 0 <= exc_off and exc_off + exc_sz <= file_sz:
                    n_pdata = exc_sz // 12
                    f.seek(exc_off)
                    pdata_ints = struct.unpack(f"<{n_pdata * 3}I", f.read(n_pdata * 12))
                    code_sec_end = sections[0][1] + sections[0][2] if sections else 0x05000000
                    code_funcs: list[tuple[int, int, int, int]] = []
                    tot_code = 0
                    for idx_p in range(0, len(pdata_ints), 3):
                        b_rva, e_rva, u_rva = pdata_ints[idx_p], pdata_ints[idx_p + 1], pdata_ints[idx_p + 2]
                        if 0x1000 <= b_rva < e_rva <= code_sec_end:
                            sz_f = e_rva - b_rva
                            code_funcs.append((b_rva, e_rva, sz_f, u_rva))
                            tot_code += sz_f
                    code_funcs.sort(key=lambda x: -x[2])
                    pdata_info = {
                        "pdata_rva": f"0x{exc_rva:08x}",
                        "pdata_size_bytes": exc_sz,
                        "runtime_function_entries": n_pdata,
                        "valid_code_functions": len(code_funcs),
                        "total_code_bytes": tot_code,
                        "largest_functions_top50": [
                            {
                                "start_rva": f"0x{b:08x}",
                                "end_rva": f"0x{e:08x}",
                                "start_va": f"0x{image_base + b:016x}",
                                "size_bytes": sz_f,
                                "unwind_rva": f"0x{u:08x}",
                            }
                            for b, e, sz_f, u in code_funcs[:50]
                        ],
                    }

            if not exp_rva or not exp_sz:
                return {
                    "exists": True,
                    "path": str(dll_path),
                    "size_bytes": file_sz,
                    "sections": [s[0] for s in sections],
                    "pdata_function_table": pdata_info,
                    "export_count": 0,
                    "exports": [],
                }
            exp_off = rva_to_off(exp_rva)
            if exp_off < 0 or exp_off + 40 > file_sz:
                return {
                    "exists": True,
                    "path": str(dll_path),
                    "size_bytes": file_sz,
                    "sections": [s[0] for s in sections],
                    "pdata_function_table": pdata_info,
                    "export_count": 0,
                    "exports": [],
                }
            f.seek(exp_off)
            (
                _,
                _,
                _,
                _,
                _,
                base_ord,
                num_funcs,
                num_names,
                addr_funcs_rva,
                addr_names_rva,
                addr_ords_rva,
            ) = struct.unpack("<IIHHIIIIIII", f.read(40))
            af_off = rva_to_off(addr_funcs_rva)
            an_off = rva_to_off(addr_names_rva)
            ao_off = rva_to_off(addr_ords_rva)
            if af_off < 0 or an_off < 0 or ao_off < 0:
                return {
                    "exists": True,
                    "path": str(dll_path),
                    "size_bytes": file_sz,
                    "sections": [s[0] for s in sections],
                    "export_count": 0,
                    "exports": [],
                }
            f.seek(an_off)
            name_rvas = struct.unpack(f"<{num_names}I", f.read(num_names * 4))
            f.seek(ao_off)
            ord_indices = struct.unpack(f"<{num_names}H", f.read(num_names * 2))
            f.seek(af_off)
            func_rvas = struct.unpack(f"<{num_funcs}I", f.read(num_funcs * 4))
            exports: list[dict[str, Any]] = []
            by_subsystem: dict[str, int] = {}
            for i in range(num_names):
                noff = rva_to_off(name_rvas[i])
                f.seek(noff)
                fn_name = f.read(192).split(b"\x00", 1)[0].decode("ascii", errors="replace")
                ord_idx = ord_indices[i]
                fn_rva = func_rvas[ord_idx]
                subsystem = fn_name.split("__")[0] if "__" in fn_name else "abi_layout_signature"
                by_subsystem[subsystem] = by_subsystem.get(subsystem, 0) + 1
                exports.append(
                    {
                        "ordinal": base_ord + ord_idx,
                        "name": fn_name,
                        "subsystem": subsystem,
                        "rva": f"0x{fn_rva:08x}",
                        "va": f"0x{image_base + fn_rva:016x}",
                    }
                )

            # Scan .data1 / .edata (section #1) for C++ FourCC vtable hierarchies (ActionContributor & SearchFilter)
            action_contributors: list[dict[str, Any]] = []
            search_filter_vtables: list[dict[str, Any]] = []
            if len(sections) >= 2:
                code_vaddr, _, code_raddr, code_rsize = sections[0][1], sections[0][2], sections[0][3], sections[0][4]
                data_vaddr, _, data_raddr, data_rsize = sections[1][1], sections[1][2], sections[1][3], sections[1][4]
                if code_raddr + code_rsize <= file_sz and data_raddr + data_rsize <= file_sz:
                    f.seek(code_raddr)
                    code_bytes = f.read(code_rsize)
                    f.seek(data_raddr)
                    data_bytes = f.read(data_rsize)
                    qwords = struct.unpack_from(f"<{len(data_bytes) // 8}Q", data_bytes, 0)
                    code_lo = image_base + code_vaddr
                    code_hi = code_lo + code_rsize
                    pair_groups: dict[tuple[int, int], list[dict[str, Any]]] = {}
                    for qi in range(len(qwords) - 12):
                        s1 = qwords[qi + 1]
                        if code_lo <= s1 < code_hi:
                            c_off = s1 - code_lo
                            if c_off + 6 <= len(code_bytes) and code_bytes[c_off] == 0xB8 and code_bytes[c_off + 5] == 0xC3:
                                u32 = struct.unpack_from("<I", code_bytes, c_off + 1)[0]
                                fc = fourcc_to_ascii(u32)
                                if not fc.startswith("0x") and any(ch.isalpha() for ch in fc):
                                    s3, s4 = qwords[qi + 3], qwords[qi + 4]
                                    if code_lo <= s3 < code_hi and code_lo <= s4 < code_hi:
                                        pair_groups.setdefault((s3, s4), []).append(
                                            {
                                                "fourcc": fc,
                                                "id_hex": f"0x{u32:08x}",
                                                "vtable_va": f"0x{image_base + data_vaddr + qi * 8:016x}",
                                                "get_id_va": f"0x{s1:016x}",
                                                "slot2_va": f"0x{qwords[qi + 2]:016x}",
                                                "can_contribute_or_eval_va": f"0x{qwords[qi + 10]:016x}",
                                            }
                                        )
                    sorted_groups = sorted(pair_groups.values(), key=len, reverse=True)
                    if len(sorted_groups) >= 1:
                        action_contributors = sorted_groups[0]
                    if len(sorted_groups) >= 2:
                        search_filter_vtables = sorted_groups[1]

        return {
            "exists": True,
            "path": str(dll_path),
            "size_bytes": file_sz,
            "image_base": f"0x{image_base:016x}",
            "sections": [
                {"name": n, "vaddr": f"0x{va:08x}", "vsize": vs, "rsize": rs}
                for n, va, vs, _, rs in sections
            ],
            "pdata_function_table": pdata_info,
            "action_contributor_vtables_count": len(action_contributors),
            "action_contributor_vtables": action_contributors,
            "search_filter_vtables_count": len(search_filter_vtables),
            "search_filter_vtables": search_filter_vtables,
            "export_count": len(exports),
            "subsystem_counts": by_subsystem,
            "exports": exports,
        }

    return {
        "game_plugin_dll": _parse_pe_exports(gp_path),
        "lib_burst_generated_dll": _parse_pe_exports(burst_path),
    }


# ==============================================================================
# 6. ALL FMF ARCHIVES, PERSON FILTER METADATA, SKELETONS & STANDALONE XML/DBC
# ==============================================================================


def extract_all_fmf_and_config_archives(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Extract all remaining ``.fmf`` archives (``filters.fmf``, ``achievements.fmf``, ``leaderboards.fmf``,
    ``settings.fmf``, ``store.fmf``, ``profanity_filter.fmf``, ``editor.fmf``, ``media.fmf``, ``simatch.fmf``),
    ``versus comps/*.xml``, ``sianim/skeletons/*/*.json``, and the complete ``database/db/*`` file inventory."""
    root = resolve_fm_install_dir(fm_install_dir)
    result: dict[str, Any] = {
        "fmf_archives_inventory": {},
        "person_search_filters": [],
        "achievements_xml": "",
        "leaderboards_xml": "",
        "settings_xmls": {},
        "store_xmls": {},
        "versus_comps_xmls": {},
        "sianim_skeletons": {},
        "match_sounds_cfg": "",
        "match_events_summary": {},
        "editor_fmf_files": [],
        "media_fmf_files": [],
        "database_files_inventory": [],
    }

    # 1. Scan all .fmf archives in the installation
    for fmf_path in sorted(root.rglob("*.fmf")):
        rel = fmf_path.relative_to(root).as_posix()
        try:
            dirs = read_fmf_directory(fmf_path)
            result["fmf_archives_inventory"][rel] = {
                "size_bytes": fmf_path.stat().st_size,
                "file_count": len(dirs),
                "sample_files": [d.get("name", "") for d in dirs[:25]],
            }
        except Exception as exc:
            result["fmf_archives_inventory"][rel] = {"error": str(exc)}

    # 2. Extract filters.fmf -> person_filter_metadata.xml
    filters_fmf = root / "data/game_simulation/filters.fmf"
    if filters_fmf.exists():
        f_frames = extract_fmf_frames(filters_fmf)
        f_dirs = read_fmf_directory(filters_fmf)
        for idx, d in enumerate(f_dirs):
            if "person_filter_metadata.xml" in d.get("name", ""):
                xml_txt = f_frames[idx][1].decode("utf-8-sig", errors="replace")
                for rec_m in re.finditer(r"<record>\s*<integer id=\"id\" value=\"([^\"]+)\"(.*?)</record>\s*(?=<record>|</list>)", xml_txt, re.DOTALL):
                    fid = rec_m.group(1)
                    body = rec_m.group(2)
                    name_m = re.search(r"<translation id=\"name\"[^>]*value=\"([^\"]+)\"", body)
                    cat_m = re.search(r"<translation id=\"category\"[^>]*value=\"([^\"]+)\"", body)
                    sf_m = re.search(r"<record id=\"search_filter\">\s*<integer id=\"id\" value=\"([^\"]+)\"", body)
                    vt_m = re.search(r"<flags id=\"valid_type\" value=\"([^\"]+)\"", body)
                    mode_m = re.search(r"<flags id=\"mode\" value=\"([^\"]+)\"", body)
                    result["person_search_filters"].append(
                        {
                            "filter_fourcc": fid,
                            "name": name_m.group(1) if name_m else "",
                            "category": cat_m.group(1) if cat_m else "",
                            "search_filter_fourcc": sf_m.group(1) if sf_m else "",
                            "valid_type": vt_m.group(1) if vt_m else "",
                            "mode": mode_m.group(1) if mode_m else "",
                        }
                    )

    # 3. Extract achievements.fmf, leaderboards.fmf, settings.fmf, store.fmf
    for sub_rel, key_target in (
        ("data/game_simulation/achievements.fmf", "achievements_xml"),
        ("data/game_simulation/leaderboards.fmf", "leaderboards_xml"),
    ):
        p = root / sub_rel
        if p.exists():
            fr = extract_fmf_frames(p)
            if fr:
                result[key_target] = fr[0][1].decode("utf-8-sig", errors="replace")

    for sub_rel, dict_target in (
        ("data/game_simulation/settings.fmf", "settings_xmls"),
        ("data/game_simulation/store.fmf", "store_xmls"),
    ):
        p = root / sub_rel
        if p.exists():
            fr = extract_fmf_frames(p)
            dr = read_fmf_directory(p)
            for idx, d in enumerate(dr):
                result[dict_target][d.get("name", f"file_{idx}")] = fr[idx][1].decode("utf-8-sig", errors="replace")

    # 4. Extract match_sounds.cfg & match_events.xml summary from simatch.fmf
    simatch_fmf = root / "shared/data/simatch.fmf"
    if simatch_fmf.exists():
        s_frames = extract_fmf_frames(simatch_fmf)
        s_dirs = read_fmf_directory(simatch_fmf)
        for idx, d in enumerate(s_dirs):
            nm = d.get("name", "")
            if nm.endswith("match_sounds.cfg"):
                result["match_sounds_cfg"] = s_frames[idx][1].decode("utf-8-sig", errors="replace")
            elif nm.endswith("match_events.xml"):
                ev_txt = s_frames[idx][1].decode("utf-8-sig", errors="replace")
                ev_types = sorted(set(re.findall(r'event_type="([^"]+)"', ev_txt)))
                result["match_events_summary"] = {
                    "size_bytes": len(s_frames[idx][1]),
                    "event_type_count": len(ev_types),
                    "event_types": ev_types,
                }

    # 5. Complete file lists for editor.fmf and media.fmf
    editor_fmf = root / "shared/data/editor.fmf"
    if editor_fmf.exists():
        result["editor_fmf_files"] = [
            {"name": d.get("name", ""), "uncompressed_size": d.get("uncompressed_size", 0)}
            for d in read_fmf_directory(editor_fmf)
        ]

    media_fmf = root / "data/game_simulation/media.fmf"
    if media_fmf.exists():
        result["media_fmf_files"] = [
            {"name": d.get("name", ""), "uncompressed_size": d.get("uncompressed_size", 0)}
            for d in read_fmf_directory(media_fmf)
        ]

    # 6. Extract standalone versus comps/*.xml and sianim/skeletons/*/*.json
    versus_dir = root / "data/game_simulation/versus comps"
    if versus_dir.exists():
        for xp in sorted(versus_dir.glob("*.xml")):
            result["versus_comps_xmls"][xp.name] = xp.read_text(encoding="utf-8-sig", errors="replace")

    skel_dir = root / "shared/data/sianim/skeletons"
    if skel_dir.exists():
        for jp in sorted(skel_dir.rglob("*.json")):
            rel = jp.relative_to(skel_dir).as_posix()
            try:
                jd = json.loads(jp.read_text(encoding="utf-8-sig", errors="replace"))
                result["sianim_skeletons"][rel] = {
                    "size_bytes": jp.stat().st_size,
                    "top_keys": list(jd.keys()) if isinstance(jd, dict) else [],
                    "joint_count": len(jd.get("joints", jd.get("bones", []))) if isinstance(jd, dict) else 0,
                }
            except Exception as exc:
                result["sianim_skeletons"][rel] = {"error": str(exc)}

    # 7. Inventory all standalone .dat, .dbc, .edt, .lnc, .ddt files in shared/data/
    shared_data = root / "shared/data"
    if shared_data.exists():
        for fp in sorted(shared_data.rglob("*")):
            if fp.is_file() and fp.suffix.lower() in (".dat", ".dbc", ".edt", ".lnc", ".ddt"):
                result["database_files_inventory"].append(
                    {
                        "path": fp.relative_to(root).as_posix(),
                        "suffix": fp.suffix.lower(),
                        "size_bytes": fp.stat().st_size,
                    }
                )

    # 8. Extract constants.fmf (colour pair, match crowd, draft, and training constants)
    constants_fmf = root / "data/game_simulation/constants.fmf"
    result["constants_fmf"] = {}
    if constants_fmf.exists():
        c_frames = extract_fmf_frames(constants_fmf)
        c_dirs = read_fmf_directory(constants_fmf)
        for idx, d in enumerate(c_dirs):
            nm = d.get("name", f"frame_{idx}")
            if idx < len(c_frames) and nm.endswith(".jsb"):
                parsed = parse_jsb(c_frames[idx][1])
                result["constants_fmf"][nm] = {
                    "size_bytes": len(c_frames[idx][1]),
                    "parsed": parsed[0] if parsed else None,
                }

    # 9. Decode latest DB folder's non_pl_hist_{index,id,dt}.dat, summary.dat, and lang_db_general.dat
    db_root = root / "shared/data/database/db"
    latest_fm_dir: Path | None = None
    if db_root.exists():
        fm_dirs = sorted(db_root.glob("*/*_fm"))
        if fm_dirs:
            latest_fm_dir = fm_dirs[-1]

    result["non_player_career_history"] = {}
    result["summary_dat"] = {}
    result["lang_db_general_dat"] = {}

    if latest_fm_dir is not None:
        # 9a. non_pl_hist_index.dat + non_pl_hist_id.dat + non_pl_hist_dt.dat
        idx_p = latest_fm_dir / "non_pl_hist_index.dat"
        id_p = latest_fm_dir / "non_pl_hist_id.dat"
        dt_p = latest_fm_dir / "non_pl_hist_dt.dat"
        if idx_p.exists() and id_p.exists() and dt_p.exists():
            try:
                import zstandard as zstd

                dctx = zstd.ZstdDecompressor()
                idx_raw = idx_p.read_bytes()
                idx_dec = dctx.decompress(idx_raw[12:], max_output_size=30_000_000)
                person_cnt = struct.unpack_from("<I", idx_dec, 0)[0]

                def _decomp_tadc(p: Path) -> bytes:
                    raw_b = p.read_bytes()
                    out_b = bytearray()
                    pos_b = 8
                    while pos_b < len(raw_b):
                        z_off = raw_b.find(b"\x28\xb5\x2f\xfd", pos_b)
                        if z_off == -1:
                            break
                        nxt_off = raw_b.find(b"\x28\xb5\x2f\xfd", z_off + 4)
                        chunk_b = raw_b[z_off : nxt_off if nxt_off != -1 else len(raw_b)]
                        try:
                            out_b.extend(dctx.decompress(chunk_b, max_output_size=16_000_000))
                        except Exception:
                            with dctx.stream_reader(raw_b[z_off:]) as reader:
                                out_b.extend(reader.read())
                        pos_b = nxt_off if nxt_off != -1 else len(raw_b)
                    return bytes(out_b)

                id_dec = _decomp_tadc(id_p)
                dt_dec = _decomp_tadc(dt_p)
                row_cnt = len(dt_dec) // 24
                sample_rows: list[dict[str, Any]] = []
                for r in range(min(20, row_cnt)):
                    c_uid, s_day, s_yr, e_day, e_yr, j_day, j_yr, role_id, r_flags, scope_id, leave_id, sec_uid = (
                        struct.unpack_from("<IHHHHHHBBBBi", dt_dec, r * 24)
                    )
                    sample_rows.append(
                        {
                            "row_index": r,
                            "club_or_nation_uid": c_uid,
                            "start_date": f"{s_yr}-day{s_day:03d}",
                            "end_date": None if e_yr == 0xFFFF else f"{e_yr}-day{e_day:03d}",
                            "reference_date": None if j_yr == 0xFFFF else f"{j_yr}-day{j_day:03d}",
                            "job_role_id": role_id,
                            "role_flags": r_flags,
                            "squad_scope": scope_id,
                            "leaving_reason": leave_id,
                            "secondary_uid": sec_uid,
                        }
                    )
                result["non_player_career_history"] = {
                    "db_folder": latest_fm_dir.relative_to(root).as_posix(),
                    "index_magic": idx_raw[:6].decode("latin1"),
                    "id_magic": id_p.read_bytes()[:6].decode("latin1"),
                    "dt_magic": dt_p.read_bytes()[:6].decode("latin1"),
                    "person_index_count": person_cnt,
                    "id_node_count": len(id_dec) // 8,
                    "id_decompressed_bytes": len(id_dec),
                    "dt_row_count": row_cnt,
                    "dt_row_stride_bytes": 24,
                    "dt_decompressed_bytes": len(dt_dec),
                    "dt_row_struct_format": "<IHHHHHHBBBBi",
                    "sample_rows": sample_rows,
                }
            except Exception as exc:
                result["non_player_career_history"] = {"error": str(exc)}

        # 9b. summary.dat
        sum_p = latest_fm_dir / "summary.dat"
        if sum_p.exists():
            try:
                sum_raw = sum_p.read_bytes()
                pos_s = 8
                n_cont = struct.unpack_from("<I", sum_raw, pos_s)[0]
                pos_s += 4
                continents: list[dict[str, Any]] = []

                def _parse_sum_comp(buf: bytes, p_off: int) -> tuple[dict[str, Any], int]:
                    _sent, _tag, comp_uid, _z1, _z2, rep, _b1, _b2, _s1, _s2, _s3, _dd, _dy = struct.unpack_from(
                        "<iBIIIbbBhhhhH", buf, p_off
                    )
                    p_off += 30
                    n_win = struct.unpack_from("<I", buf, p_off)[0]
                    p_off += 4
                    winners = list(struct.unpack_from(f"<{n_win}I", buf, p_off))
                    p_off += 4 * n_win
                    n_yr = struct.unpack_from("<I", buf, p_off)[0]
                    p_off += 4
                    years = list(struct.unpack_from(f"<{n_yr}H", buf, p_off))
                    p_off += 2 * n_yr
                    n_fl = struct.unpack_from("<I", buf, p_off)[0]
                    p_off += 4 + n_fl
                    n_ru = struct.unpack_from("<I", buf, p_off)[0]
                    p_off += 4 + 4 * n_ru
                    return {"comp_uid": comp_uid, "reputation": rep, "recent_winners": winners, "years": years}, p_off

                for _ in range(n_cont):
                    _sent, _tag, cont_uid, rep = struct.unpack_from("<iBIH", sum_raw, pos_s)
                    pos_s += 11
                    n_c1 = struct.unpack_from("<I", sum_raw, pos_s)[0]
                    pos_s += 4
                    men_comps = []
                    for _ in range(n_c1):
                        cp_d, pos_s = _parse_sum_comp(sum_raw, pos_s)
                        men_comps.append(cp_d)
                    n_c2 = struct.unpack_from("<I", sum_raw, pos_s)[0]
                    pos_s += 4
                    women_comps = []
                    for _ in range(n_c2):
                        cp_d, pos_s = _parse_sum_comp(sum_raw, pos_s)
                        women_comps.append(cp_d)
                    pos_s += 6
                    continents.append(
                        {
                            "continent_uid": cont_uid,
                            "reputation": rep,
                            "men_competitions": men_comps,
                            "women_competitions": women_comps,
                        }
                    )
                n_nations = struct.unpack_from("<I", sum_raw, pos_s)[0] if pos_s + 4 <= len(sum_raw) else 251
                ver_s = struct.unpack_from("<H", sum_raw, 6)[0]
                club_summary_count = (
                    sum_raw.count(b"\xff\xff\xff\xff\x09")
                    if ver_s >= 3
                    else sum_raw.count(b"\xff\xff\xff\xff\x08")
                )
                result["summary_dat"] = {
                    "path": sum_p.relative_to(root).as_posix(),
                    "size_bytes": len(sum_raw),
                    "header_magic": sum_raw[:6].decode("latin1"),
                    "version": ver_s,
                    "continent_count": n_cont,
                    "continents": continents,
                    "nation_count": n_nations,
                    "club_summary_record_count": club_summary_count,
                    "club_summary_record_stride_bytes": 25 if ver_s >= 3 else 23,
                }
            except Exception as exc:
                result["summary_dat"] = {"error": str(exc)}

        # 9c. lang_db_general.dat
        lgen_p = latest_fm_dir / "lang_db_general.dat"
        if lgen_p.exists():
            try:
                lg_frames = extract_fmf_frames(lgen_p)
                comp_cnt = struct.unpack_from("<I", lg_frames[1][1], 8)[0] if len(lg_frames) > 1 and len(lg_frames[1][1]) >= 12 else 0
                club_cnt = struct.unpack_from("<I", lg_frames[2][1], 8)[0] if len(lg_frames) > 2 and len(lg_frames[2][1]) >= 12 else 0
                award_cnt = struct.unpack_from("<I", lg_frames[6][1], 8)[0] if len(lg_frames) > 6 and len(lg_frames[6][1]) >= 12 else 0
                stad_cnt = struct.unpack_from("<I", lg_frames[7][1], 8)[0] if len(lg_frames) > 7 and len(lg_frames[7][1]) >= 12 else 0
                result["lang_db_general_dat"] = {
                    "path": lgen_p.relative_to(root).as_posix(),
                    "size_bytes": lgen_p.stat().st_size,
                    "zstd_frame_count": len(lg_frames),
                    "language_block_count": (len(lg_frames) - 1) // 16,
                    "tables_per_language": 16,
                    "generic_competition_overrides": comp_cnt,
                    "generic_club_overrides": club_cnt,
                    "generic_award_overrides": award_cnt,
                    "generic_stadium_overrides": stad_cnt,
                }
            except Exception as exc:
                result["lang_db_general_dat"] = {"error": str(exc)}

    return result


# ==============================================================================
# 7. PURE-PYTHON UNITYFS v8 (LZ4) UI & BINDABLE BUNDLE DECOMPILER
# ==============================================================================


try:
    import lz4.block as _lz4_block
except ImportError:
    _lz4_block = None


def lz4_decompress_block(src: bytes, uncompressed_size: int) -> bytes:
    """Fast C-accelerated (with pure-Python fallback) raw LZ4 block decompressor for UnityFS v8 archive blocks."""
    if _lz4_block is not None:
        return _lz4_block.decompress(src, uncompressed_size=uncompressed_size)
    dst = bytearray()
    pos = 0
    n = len(src)
    while pos < n and len(dst) < uncompressed_size:
        token = src[pos]
        pos += 1
        lit_len = token >> 4
        if lit_len == 15:
            while pos < n:
                b = src[pos]
                pos += 1
                lit_len += b
                if b != 255:
                    break
        dst.extend(src[pos : pos + lit_len])
        pos += lit_len
        if pos >= n or len(dst) >= uncompressed_size:
            break
        offset = src[pos] | (src[pos + 1] << 8)
        pos += 2
        match_len = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while pos < n:
                b = src[pos]
                pos += 1
                match_len += b
                if b != 255:
                    break
        start = len(dst) - offset
        for i in range(match_len):
            dst.append(dst[start + i])
    return bytes(dst)


def unpack_unityfs_bundle(bundle_path: Path) -> bytes:
    """Decompress a UnityFS v8 (``6000.0.52f1-fm26``) ``.bundle`` file into raw serialized asset bytes."""
    data = bundle_path.read_bytes()
    if not data.startswith(b"UnityFS\x00"):
        return b""
    pos = 8
    ver = struct.unpack_from(">I", data, pos)[0]
    pos += 4
    while data[pos] != 0:
        pos += 1
    pos += 1
    while data[pos] != 0:
        pos += 1
    pos += 1
    _, c_blocks_sz, u_blocks_sz, flags = struct.unpack_from(">QIII", data, pos)
    pos += 20
    if ver >= 7:
        pos = (pos + 15) & ~15
    c_type = flags & 0x3F
    blocks_info_raw = data[pos : pos + c_blocks_sz]
    pos += c_blocks_sz
    if flags & 0x200:
        pos = (pos + 15) & ~15
    bi = lz4_decompress_block(blocks_info_raw, u_blocks_sz) if c_type in (2, 3) else blocks_info_raw
    b_pos = 16
    block_cnt = struct.unpack_from(">I", bi, b_pos)[0]
    b_pos += 4
    out = bytearray()
    for _ in range(block_cnt):
        u_sz, c_sz, b_flags = struct.unpack_from(">IIH", bi, b_pos)
        b_pos += 10
        chunk = data[pos : pos + c_sz]
        pos += c_sz
        bt = b_flags & 0x3F
        out.extend(lz4_decompress_block(chunk, u_sz) if bt in (2, 3) else chunk)
    return bytes(out)


def decompile_unity_ui_bundles(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decompress all Unity UI & Bindable ``.bundle`` files (all 67 ``ui-*.bundle`` files plus
    ``sibindable_assets_all.bundle`` and ``shortcutdata_assets_all.bundle``) and extract their embedded
    ``GlobalMapping`` root bindings, ``Assets/...`` paths, ``TableFactory`` definitions, ``TableView`` presets,
    and UI binding paths."""
    root = resolve_fm_install_dir(fm_install_dir)
    aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
    if not aa_dir.exists():
        return {"bundle_count": 0, "bundles": {}}

    target_bundles = [
        "sibindable_assets_all.bundle",
        "shortcutdata_assets_all.bundle",
    ]
    for extra in sorted(aa_dir.glob("ui-*.bundle")):
        if extra.name not in target_bundles:
            target_bundles.append(extra.name)

    bundles_out: dict[str, Any] = {}
    all_bind_paths: set[str] = set()
    table_factories: list[str] = []
    table_factory_sort_bindings: list[str] = []
    table_views: list[str] = []
    total_assets = 0

    for bname in target_bundles:
        bpath = aa_dir / bname
        if not bpath.exists():
            continue
        raw = unpack_unityfs_bundle(bpath)
        assets = sorted(
            set(
                m.group(0).decode("ascii")
                for m in re.finditer(
                    rb"(?i)Assets/[A-Za-z0-9_.\-/ ]+\.(?:uxml|asset|uss|json|xml|png|jpg|ttf|otf|mat|shader)",
                    raw,
                )
            )
        )
        bind_paths = sorted(
            set(
                m.group(0).decode("ascii")
                for m in re.finditer(
                    rb"(?i)(?:person|player|club|team|match|comp|stadium|contract|tactic|staff|human|game|settings|binding|row|selection)\.[A-Za-z0-9_.]+",
                    raw,
                )
            )
        )
        if bname == "ui-tablefactories_assets_all.bundle":
            table_factories = sorted(
                set(m.group(0).decode("ascii") for m in re.finditer(rb"[A-Za-z0-9_]+TableFactory", raw))
            )
            table_factory_sort_bindings = sorted(
                set(m.group(0).decode("ascii") for m in re.finditer(rb"binding\.[A-Za-z0-9_.]+", raw))
            )
        elif bname == "ui-tableviews_assets_all.bundle":
            table_views = sorted(
                set(
                    m.group(1).decode("ascii")
                    for m in re.finditer(
                        rb"([A-Za-z0-9_\-]{4,80}(?:TableSettings|TableView|Table|View|Block|List))",
                        raw,
                    )
                    if any(k in m.group(1) for k in (b"Table", b"View", b"Settings"))
                )
            )
        all_bind_paths.update(bind_paths)
        total_assets += len(assets)
        bundles_out[bname] = {
            "compressed_size_bytes": bpath.stat().st_size,
            "decompressed_size_bytes": len(raw),
            "asset_count": len(assets),
            "assets": assets,
            "binding_path_count": len(bind_paths),
            "binding_paths": bind_paths,
        }

    return {
        "bundle_count": len(bundles_out),
        "total_extracted_asset_paths": total_assets,
        "total_unique_ui_binding_paths": len(all_bind_paths),
        "table_factory_count": len(table_factories),
        "table_factories": table_factories,
        "table_factory_sort_binding_count": len(table_factory_sort_bindings),
        "table_factory_sort_bindings": table_factory_sort_bindings,
        "table_view_count": len(table_views),
        "table_views": table_views,
        "all_unique_ui_binding_paths": sorted(all_bind_paths),
        "bundles": bundles_out,
    }


def decompile_csharp_method_bodies(
    fm_install_dir: str | os.PathLike[str] | None = None,
    *,
    filter_substr: str | None = None,
    max_methods: int = 25,
) -> dict[str, Any]:
    """Disassemble compiled C# method bodies in ``GameAssembly.dll`` using ``il2cpp.usym`` RVA ranges,
    annotating instructions with original ``.cs:line`` source numbers and resolving ``call`` targets."""
    root = resolve_fm_install_dir(fm_install_dir)
    ga_path = root / "GameAssembly.dll"
    usym_path = root / "fm_Data/il2cpp_data/il2cpp.usym"
    if not usym_path.exists():
        usym_path = root / "il2cpp.usym"
    meta_data = decompile_global_metadata(root, include_all_methods=True)
    usym_data = decompile_usym_symbols(root, max_records=10)
    rva_map: dict[int, dict[str, Any]] = usym_data.get("_method_rva_map", {})

    # Map start RVA -> (TypeFullName.MethodName, method_index)
    rva_to_method_name: dict[int, str] = {}
    matched_methods: list[dict[str, Any]] = []
    flt = (filter_substr or "").lower()

    for t in meta_data["types"]:
        t_full = f"{t['namespace']}.{t['name']}" if t["namespace"] else t["name"]
        for m in t["methods"]:
            mid = m["method_index"]
            rm = rva_map.get(mid)
            if not rm:
                continue
            r_start = int(rm["rva_start"], 16)
            r_end = int(rm["rva_end"], 16)
            full_sig = f"{t_full}.{m['name']}({', '.join(m['parameters'])})"
            rva_to_method_name[r_start] = full_sig
            if not flt or flt in full_sig.lower() or flt in rm.get("source_file", "").lower():
                matched_methods.append(
                    {
                        "image": t["image"],
                        "type": t_full,
                        "method": m["name"],
                        "parameters": m["parameters"],
                        "method_index": mid,
                        "token": m["token"],
                        "rva_start": rm["rva_start"],
                        "rva_end": rm["rva_end"],
                        "source_file": rm.get("source_file", ""),
                        "line_start": rm.get("line_start"),
                        "line_end": rm.get("line_end"),
                    }
                )

    # Collect per-RVA line annotations from il2cpp.usym for the matched methods
    target_mids = {m["method_index"] for m in matched_methods[:max_methods]}
    rva_line_map: dict[int, int] = {}
    if target_mids and usym_path.exists():
        raw_u = usym_path.read_bytes()
        sym_cnt = struct.unpack_from("<I", raw_u, 8)[0]
        mv_u = memoryview(raw_u)[24 : 24 + sym_cnt * 24]
        for rva_u64, mid_u, _foff, line_u, parent_u in struct.iter_unpack("<QIIII", mv_u):
            if mid_u in target_mids and parent_u == 0xFFFFFFFF and line_u != 0xFFFFFFFF:
                rva_line_map[rva_u64] = line_u

    # Disassemble matched methods from GameAssembly.dll
    try:
        import capstone

        cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    except Exception:
        cs = None

    disassembled: list[dict[str, Any]] = []
    with open(ga_path, "rb") as f_ga:
        hdr_b = f_ga.read(4096)
        e_lfanew = struct.unpack_from("<I", hdr_b, 0x3C)[0]
        num_sec = struct.unpack_from("<H", hdr_b, e_lfanew + 6)[0]
        opt_size = struct.unpack_from("<H", hdr_b, e_lfanew + 20)[0]
        sec_off = e_lfanew + 24 + opt_size
        sections: list[tuple[int, int, int, int]] = []
        for i in range(num_sec):
            s = hdr_b[sec_off + i * 40 : sec_off + (i + 1) * 40]
            vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", s, 8)
            sections.append((vaddr, vsize, raddr, rsize))

        def _rva_to_off(rva: int) -> int:
            for vaddr, vsize, raddr, rsize in sections:
                if vaddr <= rva < vaddr + max(vsize, rsize):
                    return raddr + (rva - vaddr)
            return -1

        for m in matched_methods[:max_methods]:
            r_start = int(m["rva_start"], 16)
            r_end = max(int(m["rva_end"], 16) + 32, r_start + 32)
            f_off = _rva_to_off(r_start)
            code_slice = b""
            if f_off >= 0:
                f_ga.seek(f_off)
                code_slice = f_ga.read(min(r_end - r_start, 4096))
            insns_out: list[str] = []
            if cs is not None and code_slice:
                for insn in cs.disasm(code_slice, r_start):
                    ln = rva_line_map.get(insn.address)
                    ln_tag = f" [L{ln}]" if ln is not None else ""
                    call_comment = ""
                    if insn.mnemonic in ("call", "jmp") and insn.op_str.startswith("0x"):
                        try:
                            tgt_rva = int(insn.op_str, 16)
                            if tgt_rva in rva_to_method_name:
                                call_comment = f" ; -> {rva_to_method_name[tgt_rva]}"
                        except ValueError:
                            pass
                    insns_out.append(f"0x{insn.address:08x}: {insn.mnemonic:8s} {insn.op_str}{ln_tag}{call_comment}")
                    if insn.address >= int(m["rva_end"], 16) and insn.mnemonic in ("ret", "jmp", "int3"):
                        break
            m_copy = dict(m)
            m_copy["instruction_count"] = len(insns_out)
            m_copy["disassembly"] = insns_out
            disassembled.append(m_copy)

    return {
        "total_mapped_csharp_methods": len(rva_map),
        "matched_method_count": len(matched_methods),
        "disassembled_count": len(disassembled),
        "methods": disassembled,
    }


# ==============================================================================
# 7B. COMPLETE DECOMPILATION OF ALL REMAINING GAME FILES (CATEGORY 2)
# ==============================================================================

_UNITY_CLASS_ID_NAMES: dict[int, str] = {
    1: "GameObject",
    4: "Transform",
    13: "InputManager",
    20: "Camera",
    21: "Material",
    23: "MeshRenderer",
    28: "Texture2D",
    33: "MeshFilter",
    43: "Mesh",
    48: "Shader",
    49: "TextAsset",
    54: "Rigidbody",
    65: "BoxCollider",
    74: "AnimationClip",
    82: "AudioSource",
    83: "AudioClip",
    89: "Cubemap",
    91: "AnimatorController",
    95: "Animator",
    104: "RenderSettings",
    108: "Light",
    114: "MonoBehaviour",
    115: "MonoScript",
    128: "Font",
    129: "PlayerSettings",
    141: "BuildSettings",
    142: "AssetBundle",
    150: "PreloadData",
    157: "LightmapSettings",
    212: "SpriteRenderer",
    213: "Sprite",
    222: "CanvasRenderer",
    223: "Canvas",
    224: "RectTransform",
    687078895: "SpriteAtlas",
}


def _parse_serialized_file_v22(path: Path) -> dict[str, Any]:
    """Parse a Unity SerializedFile (v22) container header, serialized type table,
    object table, script table, and external file reference list."""
    data = path.read_bytes()
    if len(data) < 64:
        return {"file": path.name, "size_bytes": len(data), "valid": False}
    hdr_ver = struct.unpack_from(">I", data, 8)[0]
    endian = data[16]
    meta_size = struct.unpack_from(">I", data, 20)[0]
    file_size, data_offset, _ = struct.unpack_from(">QQq", data, 24)
    pos = 48
    try:
        end_s = data.index(b"\x00", pos)
        unity_ver = data[pos:end_s].decode("ascii", errors="replace")
        pos = end_s + 1
        plat = struct.unpack_from("<i", data, pos)[0]
        pos += 4
        has_tree = data[pos] != 0
        pos += 1
        type_cnt = struct.unpack_from("<i", data, pos)[0]
        pos += 4
        types: list[dict[str, Any]] = []
        if not has_tree and 0 <= type_cnt <= 10000:
            for _ in range(type_cnt):
                cid = struct.unpack_from("<i", data, pos)[0]
                is_strip = data[pos + 4]
                script_idx = struct.unpack_from("<h", data, pos + 5)[0]
                pos += 7
                if cid == 114 or cid < 0:
                    script_id = data[pos : pos + 16].hex()
                    pos += 16
                else:
                    script_id = None
                old_hash = data[pos : pos + 16].hex()
                pos += 16
                types.append(
                    {
                        "class_id": cid,
                        "class_name": _UNITY_CLASS_ID_NAMES.get(cid, f"Class_{cid}"),
                        "is_stripped": is_strip,
                        "script_type_index": script_idx,
                        "script_id": script_id,
                        "old_type_hash": old_hash,
                    }
                )
        obj_cnt = 0
        script_cnt = 0
        ext_cnt = 0
        externals: list[dict[str, Any]] = []
        objs_by_class: dict[str, int] = {}
        if not has_tree and len(types) == type_cnt:
            obj_cnt = struct.unpack_from("<i", data, pos)[0]
            pos += 4
            while pos % 4 != 0:
                pos += 1
            for _ in range(obj_cnt):
                _, _, _, tidx = struct.unpack_from("<qQII", data, pos)
                pos += 24
                cname = (
                    types[tidx]["class_name"]
                    if 0 <= tidx < len(types)
                    else f"TypeIdx_{tidx}"
                )
                objs_by_class[cname] = objs_by_class.get(cname, 0) + 1
            script_cnt = struct.unpack_from("<i", data, pos)[0]
            pos += 4 + script_cnt * 12
            ext_cnt = struct.unpack_from("<i", data, pos)[0]
            pos += 4
            for _ in range(ext_cnt):
                e0 = data.index(b"\x00", pos)
                pos = e0 + 1
                guid = data[pos : pos + 16].hex()
                etype = struct.unpack_from("<i", data, pos + 16)[0]
                pos += 20
                e1 = data.index(b"\x00", pos)
                epath = data[pos:e1].decode("utf-8", errors="replace")
                pos = e1 + 1
                externals.append({"path": epath, "guid": guid, "type": etype})
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "file": path.name,
            "size_bytes": len(data),
            "version": hdr_ver,
            "error": str(exc),
        }

    res_s = path.with_suffix(path.suffix + ".resS") if path.suffix else path.parent / (path.name + ".resS")
    return {
        "file": path.name,
        "size_bytes": len(data),
        "ress_file": res_s.name if res_s.exists() else None,
        "ress_size_bytes": res_s.stat().st_size if res_s.exists() else 0,
        "serialized_version": hdr_ver,
        "endianness": "little" if endian == 0 else "big",
        "metadata_size": meta_size,
        "header_file_size": file_size,
        "data_offset": data_offset,
        "unity_version": unity_ver,
        "target_platform": plat,
        "enable_type_tree": has_tree,
        "type_count": type_cnt,
        "object_count": obj_cnt,
        "script_type_count": script_cnt,
        "external_reference_count": ext_cnt,
        "external_references": externals,
        "objects_by_class": dict(sorted(objs_by_class.items(), key=lambda kv: -kv[1])),
    }


def _parse_pe64_summary(path: Path) -> dict[str, Any]:
    """Extract PE64 section layout, export count, and .pdata function count for any Windows DLL/EXE."""
    st_size = path.stat().st_size
    with open(path, "rb") as f:
        hdr = f.read(4096)
        if len(hdr) < 0x100 or hdr[:2] != b"MZ":
            return {"file": path.name, "size_bytes": st_size, "is_pe64": False}
        pe_off = struct.unpack_from("<I", hdr, 0x3C)[0]
        if pe_off + 24 > len(hdr) or hdr[pe_off : pe_off + 4] != b"PE\x00\x00":
            return {"file": path.name, "size_bytes": st_size, "is_pe64": False}
        machine, num_sec, timestamp = struct.unpack_from("<HHI", hdr, pe_off + 4)
        opt_sz = struct.unpack_from("<H", hdr, pe_off + 20)[0]
        opt_off = pe_off + 24
        magic = struct.unpack_from("<H", hdr, opt_off)[0]
        is_pe64 = magic == 0x20B
        dd_off = opt_off + (112 if is_pe64 else 96)
        exp_rva, exp_sz = struct.unpack_from("<II", hdr, dd_off)
        pdata_rva, pdata_sz = struct.unpack_from("<II", hdr, dd_off + 3 * 8)
        sec_off = opt_off + opt_sz
        sections: list[dict[str, Any]] = []
        for i in range(num_sec):
            sh = hdr[sec_off + i * 40 : sec_off + (i + 1) * 40]
            if len(sh) < 40:
                break
            sname = sh[:8].rstrip(b"\x00").decode("ascii", errors="replace")
            vsz, va, rsz, rptr = struct.unpack_from("<IIII", sh, 8)
            sections.append(
                {
                    "name": sname,
                    "virtual_address": f"0x{va:08x}",
                    "virtual_size": vsz,
                    "raw_size": rsz,
                    "raw_ptr": rptr,
                }
            )

        def _rva_to_off(rva: int) -> int:
            for s in sections:
                va = int(s["virtual_address"], 16)
                span = max(s["virtual_size"], s["raw_size"])
                if va <= rva < va + span:
                    return s["raw_ptr"] + (rva - va)
            return -1

        export_count = 0
        sample_exports: list[str] = []
        if exp_rva and exp_sz:
            e_off = _rva_to_off(exp_rva)
            if e_off >= 0:
                f.seek(e_off)
                edir = f.read(40)
                if len(edir) == 40:
                    num_funcs, num_names, _, names_rva, _ = struct.unpack_from("<IIIII", edir, 20)
                    export_count = num_names or num_funcs
                    n_off = _rva_to_off(names_rva)
                    if n_off >= 0 and num_names > 0:
                        f.seek(n_off)
                        n_rvas = struct.unpack_from(f"<{min(8, num_names)}I", f.read(4 * min(8, num_names)))
                        for nrva in n_rvas:
                            so = _rva_to_off(nrva)
                            if so >= 0:
                                f.seek(so)
                                sbytes = f.read(96).split(b"\x00", 1)[0]
                                sample_exports.append(sbytes.decode("ascii", errors="replace"))

        pdata_functions = pdata_sz // 12 if pdata_sz else 0
        return {
            "file": path.name,
            "relative_path": path.name,
            "size_bytes": st_size,
            "is_pe64": is_pe64,
            "machine": f"0x{machine:04x}",
            "timestamp": timestamp,
            "section_count": len(sections),
            "sections": sections,
            "export_count": export_count,
            "sample_exports": sample_exports,
            "pdata_function_count": pdata_functions,
        }


def decompile_all_remaining_game_files(
    fm_install_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Decompile all Category 2 (previously untouched) binary, archive, animation, catalog,
    Unity runtime, and native PE64 files across the entire Football Manager installation:

    1. Complete installation file inventory (every file by extension & top-level directory).
    2. All ``.bundle`` files (`534` in FM27 / `568` in FM26) via `BlocksInfo` + CAB directory nodes.
    3. Unity Addressables binary catalogs (`aa/catalog.bin` & `AddrData/catalog_info.bin`, magic `0x0DE38942` v2),
       `aa/settings.json`, `aa/AddressablesLink/link.xml`, and `fm_Data/manifest.dat` (`BuildVerifierUtilities.ReadManifest`).
    4. `shared/data/sianim/` 3D animation engine:
       - `animations/*.cat` (`CAT\\x00` v38/v37 backward-walked animation clip packages + `STAB` string table),
       - `animations/*.amd` (v4 Motion Matching Databases with 11-byte segment descriptors + frame feature spans),
       - `schemas/*.json` (`41` match action clip schemas),
       - `skeletons/` (`config.xml` + `18` male/female skeleton rig & dev UI JSON definitions).
    5. Unity SerializedFile v22 containers (`globalgamemanagers`, `globalgamemanagers.assets`,
       `resources.assets`, `sharedassets0.assets`, `level0`, `unity default resources`, `unity_builtin_extra`)
       and runtime configs (`RuntimeInitializeOnLoads.json`, `ScriptingAssemblies.json`, `boot.config`, `app.info`).
    6. All 15 native PE64 binaries (`fm.exe`, `UnityPlayer.dll`, `GameAssembly.dll`, and all 12 `Plugins/x86_64/*.dll`).
    7. Database `lang_db.dat` (`400` localized FMF tables), `fmc` (FM Console/Touch database variant), and all historical DB versions (`2300`..`2700`).
    """
    from fm26save.unity_bundle import read_bundle

    root = resolve_fm_install_dir(fm_install_dir)

    # 1. Full Installation File Inventory
    total_files = 0
    total_bytes = 0
    by_ext: dict[str, dict[str, int]] = {}
    by_top_dir: dict[str, dict[str, int]] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        sz = p.stat().st_size
        total_files += 1
        total_bytes += sz
        ext = p.suffix.lower() or "<no_ext>"
        ed = by_ext.setdefault(ext, {"count": 0, "bytes": 0})
        ed["count"] += 1
        ed["bytes"] += sz
        rel_parts = p.relative_to(root).parts
        top_key = rel_parts[0] if len(rel_parts) > 1 else "<root>"
        td = by_top_dir.setdefault(top_key, {"count": 0, "bytes": 0})
        td["count"] += 1
        td["bytes"] += sz

    installation_inventory = {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "by_extension": dict(sorted(by_ext.items(), key=lambda kv: -kv[1]["bytes"])),
        "by_top_directory": dict(sorted(by_top_dir.items(), key=lambda kv: -kv[1]["bytes"])),
    }

    # 2. All .bundle files in fm_Data/StreamingAssets/aa/StandaloneWindows64 + fm_Data/Resources
    aa_bundle_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
    res_bundle_dir = root / "fm_Data/Resources"
    all_bundle_paths = sorted(aa_bundle_dir.glob("*.bundle")) if aa_bundle_dir.exists() else []
    if res_bundle_dir.exists():
        all_bundle_paths.extend(sorted(res_bundle_dir.glob("*.bundle")))

    total_bundle_comp = 0
    total_bundle_uncomp = 0
    total_cab_nodes = 0
    bundles_by_category: dict[str, dict[str, Any]] = {}
    for bp in all_bundle_paths:
        c_sz = bp.stat().st_size
        total_bundle_comp += c_sz
        cat = bp.name.split("_")[0].split("-")[0]
        cat_d = bundles_by_category.setdefault(
            cat,
            {
                "bundle_count": 0,
                "compressed_bytes": 0,
                "uncompressed_bytes": 0,
                "cab_node_count": 0,
                "sample_bundles": [],
            },
        )
        cat_d["bundle_count"] += 1
        cat_d["compressed_bytes"] += c_sz
        try:
            b = read_bundle(bp)
            u_sz = b.uncompressed_size
            total_bundle_uncomp += u_sz
            cat_d["uncompressed_bytes"] += u_sz
            bi = b.blocks_info
            blk_cnt = struct.unpack_from(">I", bi, 16)[0]
            npos = 20 + blk_cnt * 10
            node_cnt = struct.unpack_from(">I", bi, npos)[0]
            npos += 4
            nodes: list[dict[str, Any]] = []
            for _ in range(node_cnt):
                _, n_sz, n_fl = struct.unpack_from(">QQI", bi, npos)
                npos += 20
                end_s = bi.find(b"\x00", npos)
                n_name = bi[npos:end_s].decode("utf-8", errors="replace")
                npos = end_s + 1
                nodes.append({"name": n_name, "size": n_sz, "flags": n_fl})
            total_cab_nodes += len(nodes)
            cat_d["cab_node_count"] += len(nodes)
            if len(cat_d["sample_bundles"]) < 4:
                cat_d["sample_bundles"].append(
                    {
                        "bundle": bp.name,
                        "compressed_bytes": c_sz,
                        "uncompressed_bytes": u_sz,
                        "block_count": len(b.blocks),
                        "cab_nodes": [n["name"] for n in nodes[:4]],
                    }
                )
        except Exception:
            pass

    addressable_bundles_inventory = {
        "total_bundles": len(all_bundle_paths),
        "total_compressed_bytes": total_bundle_comp,
        "total_uncompressed_bytes": total_bundle_uncomp,
        "total_cab_nodes": total_cab_nodes,
        "category_count": len(bundles_by_category),
        "categories": dict(
            sorted(bundles_by_category.items(), key=lambda kv: -kv[1]["uncompressed_bytes"])
        ),
    }

    # 3. Unity Addressables Binary Catalogs (aa/catalog.bin & AddrData/catalog_info.bin) + settings.json + link.xml + manifest.dat
    catalogs_out: dict[str, Any] = {}
    for rel_cat in (
        "fm_Data/StreamingAssets/aa/catalog.bin",
        "fm_Data/StreamingAssets/AddrData/catalog_info.bin",
    ):
        cp = root / rel_cat
        if not cp.exists():
            continue
        raw = cp.read_bytes()
        if len(raw) >= 36:
            magic, ver, keys_off, id_off, inst_off, scene_off, init_off, hash_off = struct.unpack_from(
                "<8I", raw, 0
            )
            keys_byte_len = struct.unpack_from("<I", raw, keys_off - 4)[0] if keys_off >= 4 else 0
            key_cnt = keys_byte_len // 8
            entries_end = id_off - 4
            entry_group_cnt = (
                (entries_end - (keys_off + keys_byte_len)) // 4
                if entries_end >= keys_off + keys_byte_len
                else 0
            )
            id_len = struct.unpack_from("<I", raw, id_off - 4)[0] if id_off >= 4 else 0
            locator_id = (
                raw[id_off : id_off + id_len].decode("utf-8", errors="replace")
                if id_off + id_len <= len(raw)
                else ""
            )
            hash_len = struct.unpack_from("<I", raw, hash_off - 4)[0] if hash_off >= 4 else 0
            build_hash = (
                raw[hash_off : hash_off + hash_len].decode("utf-8", errors="replace")
                if hash_off + hash_len <= len(raw)
                else ""
            )
            blob = raw[hash_off + hash_len :]
            ascii_strs = [
                m.group(0).decode("ascii", errors="ignore")
                for m in re.finditer(rb"[A-Za-z0-9_./\-]{8,200}", blob)
            ]
            bundle_strs = sorted({s for s in ascii_strs if s.endswith(".bundle")})
            catalogs_out[Path(rel_cat).name] = {
                "relative_path": rel_cat,
                "size_bytes": len(raw),
                "magic": f"0x{magic:08x}",
                "version": ver,
                "locator_id": locator_id,
                "build_result_hash": build_hash,
                "key_count": key_cnt,
                "entry_group_count": entry_group_cnt,
                "header_offsets": {
                    "keys_offset": f"0x{keys_off:06x}",
                    "id_offset": f"0x{id_off:06x}",
                    "instance_provider_offset": f"0x{inst_off:06x}",
                    "scene_provider_offset": f"0x{scene_off:06x}",
                    "init_objects_array_offset": f"0x{init_off:06x}",
                    "build_result_hash_offset": f"0x{hash_off:06x}",
                },
                "unique_bundle_references_count": len(bundle_strs),
                "sample_bundle_references": bundle_strs[:25],
            }

    aa_settings_path = root / "fm_Data/StreamingAssets/aa/settings.json"
    aa_settings = (
        json.loads(aa_settings_path.read_text(encoding="utf-8", errors="replace"))
        if aa_settings_path.exists()
        else {}
    )
    link_xml_path = root / "fm_Data/StreamingAssets/aa/AddressablesLink/link.xml"
    link_xml_info: dict[str, Any] = {"exists": link_xml_path.exists()}
    if link_xml_path.exists():
        ltxt = link_xml_path.read_text(encoding="utf-8", errors="replace")
        asm_names = re.findall(r'<assembly\s+fullname="([^"]+)"', ltxt)
        type_names = re.findall(r'<type\s+fullname="([^"]+)"', ltxt)
        link_xml_info = {
            "exists": True,
            "size_bytes": link_xml_path.stat().st_size,
            "assembly_count": len(asm_names),
            "preserved_type_count": len(type_names),
            "sample_assemblies": asm_names[:20],
        }

    # Parse fm_Data/manifest.dat (BuildVerifierUtilities.ReadManifest)
    manifest_dat_path = root / "fm_Data/manifest.dat"
    manifest_dat_info: dict[str, Any] = {"exists": manifest_dat_path.exists()}
    if manifest_dat_path.exists():
        mraw = manifest_dat_path.read_bytes()
        # Detect FM27 25-byte binary MD5 format (u32 path_hash + i32 len=16 + 16B md5 + '\n')
        # vs FM26 37-byte ASCII hex MD5 format (u32 path_hash + 32B ascii_md5 + '\n')
        m_records: list[dict[str, Any]] = []
        rec_fmt = "unknown"
        rec_size = 0
        if len(mraw) >= 25 and len(mraw) % 25 == 0 and struct.unpack_from("<I", mraw, 4)[0] == 16 and mraw[24] == 0x0A:
            rec_fmt = "FM27_25B_binary_md5 (uint32 path_hash + int32 len=16 + 16B md5 + '\\n')"
            rec_size = 25
            for off in range(0, len(mraw), 25):
                phash, hlen = struct.unpack_from("<II", mraw, off)
                md5_hex = mraw[off + 8 : off + 8 + hlen].hex()
                m_records.append({"path_hash": f"0x{phash:08x}", "md5": md5_hex})
        elif len(mraw) >= 37 and len(mraw) % 37 == 0 and mraw[36] == 0x0A:
            rec_fmt = "FM26_37B_ascii_md5 (uint32 path_hash + 32B ascii_md5 + '\\n')"
            rec_size = 37
            for off in range(0, len(mraw), 37):
                phash = struct.unpack_from("<I", mraw, off)[0]
                md5_hex = mraw[off + 4 : off + 36].decode("ascii", errors="replace")
                m_records.append({"path_hash": f"0x{phash:08x}", "md5": md5_hex})
        non_zero = sum(1 for r in m_records if r["path_hash"] != "0x00000000")
        manifest_dat_info = {
            "exists": True,
            "size_bytes": len(mraw),
            "format": rec_fmt,
            "record_size_bytes": rec_size,
            "record_count": len(m_records),
            "non_zero_path_hashes": non_zero,
            "zero_path_hashes": len(m_records) - non_zero,
            "sample_records": m_records[:15],
        }

    # 4. sianim 3D Match Animation Engine (shared/data/sianim/)
    sianim_dir = root / "shared/data/sianim"
    cat_archives: dict[str, Any] = {}
    amd_databases: dict[str, Any] = {}
    action_schemas: list[dict[str, Any]] = []
    skeleton_files: list[dict[str, Any]] = []
    if sianim_dir.exists():
        anim_dir = sianim_dir / "animations"
        if anim_dir.exists():
            for cat_file in sorted(anim_dir.glob("*.cat")):
                cdata = cat_file.read_bytes()
                pos = len(cdata)
                last_u32 = struct.unpack_from("<I", cdata, pos - 4)[0] if pos >= 4 else 0
                stab_strings: list[str] = []
                if 0 < last_u32 < pos and cdata[pos - last_u32 : pos - last_u32 + 4] == b"STAB":
                    stab_start = pos - last_u32
                    raw_strs = cdata[stab_start + 4 : pos - 4].split(b"\x00")
                    if raw_strs and raw_strs[-1] == b"":
                        raw_strs.pop()
                    stab_strings = [s.decode("utf-8", errors="replace") for s in raw_strs]
                    pos = stab_start
                clip_cnt = 0
                tot_sections = 0
                tot_tracks = 0
                cat_ver = struct.unpack_from("<I", cdata, 4)[0] if len(cdata) >= 8 else 0
                while pos > 0:
                    clip_sz = struct.unpack_from("<I", cdata, pos - 4)[0]
                    clip_start = pos - clip_sz
                    if clip_start < 0 or cdata[clip_start : clip_start + 4] != b"CAT\x00":
                        break
                    sec_cnt = cdata[pos - 5]
                    t_base = pos - 5 - sec_cnt * 9
                    tot_tracks += sum(cdata[t_base + i * 9 + 8] for i in range(sec_cnt))
                    tot_sections += sec_cnt
                    clip_cnt += 1
                    pos = clip_start
                stab_cats: dict[str, int] = {}
                for s in stab_strings:
                    pref = s.split("/")[0] if "/" in s else "<root>"
                    stab_cats[pref] = stab_cats.get(pref, 0) + 1
                cat_archives[cat_file.name] = {
                    "size_bytes": len(cdata),
                    "magic": "CAT\\x00",
                    "version": cat_ver,
                    "walked_to_offset": pos,
                    "clip_count": clip_cnt,
                    "total_bone_sections": tot_sections,
                    "total_animation_tracks": tot_tracks,
                    "stab_string_count": len(stab_strings),
                    "stab_categories": dict(sorted(stab_cats.items(), key=lambda kv: -kv[1])),
                    "sample_stab_clip_names": stab_strings[:20],
                }

            for amd_file in sorted(anim_dir.glob("*.amd")):
                adata = amd_file.read_bytes()
                ver = adata[0] if adata else 0
                seg_cnt = struct.unpack_from("<H", adata, 1)[0] if len(adata) >= 3 else 0
                if len(adata) <= 32:
                    amd_databases[amd_file.name] = {
                        "size_bytes": len(adata),
                        "version": ver,
                        "header_hex": adata.hex(),
                        "segment_count": 0,
                    }
                    continue
                segs = [struct.unpack_from("<IIHB", adata, 3 + i * 11) for i in range(seg_cnt)]
                tot_spans = sum(s[1] - s[0] for s in segs)
                rem_bytes = len(adata) - (3 + seg_cnt * 11 + 2)
                amd_databases[amd_file.name] = {
                    "size_bytes": len(adata),
                    "version": ver,
                    "segment_count": seg_cnt,
                    "total_frame_spans": tot_spans,
                    "feature_payload_bytes": rem_bytes,
                    "bytes_per_frame_span": round(rem_bytes / tot_spans, 2) if tot_spans else 0.0,
                    "sample_segments": [
                        {
                            "start_frame": s[0],
                            "end_frame": s[1],
                            "clip_state_id": s[2],
                            "flags": s[3],
                        }
                        for s in segs[:10]
                    ],
                }

        schemas_dir = sianim_dir / "schemas"
        if schemas_dir.exists():
            for sp in sorted(schemas_dir.glob("*.json")):
                try:
                    s_obj = json.loads(sp.read_text(encoding="utf-8", errors="replace"))
                    action_schemas.append(
                        {
                            "file": sp.name,
                            "size_bytes": sp.stat().st_size,
                            "keys": list(s_obj.keys()) if isinstance(s_obj, dict) else [],
                        }
                    )
                except Exception:
                    action_schemas.append({"file": sp.name, "size_bytes": sp.stat().st_size})

        for sk_sub in ("skeletons", "skeletons_dev_ui_data"):
            sk_dir = sianim_dir / sk_sub
            if sk_dir.exists():
                for skp in sorted(sk_dir.rglob("*")):
                    if skp.is_file():
                        skeleton_files.append(
                            {
                                "relative_path": skp.relative_to(sianim_dir).as_posix(),
                                "size_bytes": skp.stat().st_size,
                            }
                        )

    sianim_summary = {
        "cat_archive_count": len(cat_archives),
        "total_cat_clips": sum(c["clip_count"] for c in cat_archives.values()),
        "total_cat_bone_sections": sum(c["total_bone_sections"] for c in cat_archives.values()),
        "total_cat_tracks": sum(c["total_animation_tracks"] for c in cat_archives.values()),
        "cat_archives": cat_archives,
        "amd_database_count": len(amd_databases),
        "total_amd_segments": sum(a.get("segment_count", 0) for a in amd_databases.values()),
        "total_amd_frame_spans": sum(a.get("total_frame_spans", 0) for a in amd_databases.values()),
        "amd_databases": amd_databases,
        "action_schema_count": len(action_schemas),
        "action_schemas": action_schemas,
        "skeleton_file_count": len(skeleton_files),
        "skeleton_files": skeleton_files,
    }

    # 5. Unity SerializedFile v22 Containers & Runtime Configs (fm_Data/)
    serialized_containers: list[dict[str, Any]] = []
    for rel_sf in (
        "fm_Data/globalgamemanagers",
        "fm_Data/globalgamemanagers.assets",
        "fm_Data/resources.assets",
        "fm_Data/sharedassets0.assets",
        "fm_Data/level0",
        "fm_Data/Resources/unity default resources",
        "fm_Data/Resources/unity_builtin_extra",
    ):
        sfp = root / rel_sf
        if sfp.exists():
            serialized_containers.append(_parse_serialized_file_v22(sfp))

    runtime_init_path = root / "fm_Data/RuntimeInitializeOnLoads.json"
    scripting_asm_path = root / "fm_Data/ScriptingAssemblies.json"
    boot_cfg_path = root / "fm_Data/boot.config"
    app_info_path = root / "fm_Data/app.info"

    runtime_init_entries = 0
    if runtime_init_path.exists():
        try:
            ri_obj = json.loads(runtime_init_path.read_text(encoding="utf-8", errors="replace"))
            runtime_init_entries = len(ri_obj.get("root", [])) if isinstance(ri_obj, dict) else 0
        except Exception:
            pass

    scripting_asm_names: list[str] = []
    if scripting_asm_path.exists():
        try:
            sa_obj = json.loads(scripting_asm_path.read_text(encoding="utf-8", errors="replace"))
            scripting_asm_names = sa_obj.get("names", []) if isinstance(sa_obj, dict) else []
        except Exception:
            pass

    boot_cfg_kv: dict[str, str] = {}
    if boot_cfg_path.exists():
        for ln in boot_cfg_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in ln:
                k, v = ln.split("=", 1)
                boot_cfg_kv[k.strip()] = v.strip()

    unity_runtime_containers = {
        "serialized_containers_count": len(serialized_containers),
        "total_serialized_objects": sum(c.get("object_count", 0) for c in serialized_containers),
        "serialized_containers": serialized_containers,
        "runtime_initialize_on_loads_count": runtime_init_entries,
        "scripting_assemblies_count": len(scripting_asm_names),
        "scripting_assemblies": scripting_asm_names,
        "boot_config": boot_cfg_kv,
        "app_info": (
            app_info_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if app_info_path.exists()
            else []
        ),
    }

    # 6. All Native PE64 Binaries (fm.exe, UnityPlayer.dll, GameAssembly.dll, Plugins/x86_64/*.dll)
    pe_paths: list[Path] = []
    for top_pe in ("fm.exe", "UnityPlayer.dll", "GameAssembly.dll", "crashpad_handler.exe"):
        tp = root / top_pe
        if tp.exists():
            pe_paths.append(tp)
    plugins_dir = root / "fm_Data/Plugins/x86_64"
    if plugins_dir.exists():
        pe_paths.extend(sorted(plugins_dir.glob("*.dll")))

    pe_summaries = [_parse_pe64_summary(pp) for pp in pe_paths]
    all_native_pe64_binaries = {
        "binary_count": len(pe_summaries),
        "total_exports": sum(b.get("export_count", 0) for b in pe_summaries),
        "total_pdata_functions": sum(b.get("pdata_function_count", 0) for b in pe_summaries),
        "binaries": pe_summaries,
    }

    # 7. Database lang_db.dat, fmc (Console/Touch DB variant), and all historical DB versions (2300..2700)
    db_root = root / "shared/data/database/db"
    db_versions: list[dict[str, Any]] = []
    lang_db_summary: dict[str, Any] = {}
    fmc_variant_summary: dict[str, Any] = {}
    if db_root.exists():
        for vdir in sorted(db_root.iterdir()):
            if not vdir.is_dir():
                continue
            v_files = [f for f in vdir.rglob("*") if f.is_file()]
            db_versions.append(
                {
                    "version": vdir.name,
                    "file_count": len(v_files),
                    "total_bytes": sum(f.stat().st_size for f in v_files),
                    "subfolders": sorted([d.name for d in vdir.iterdir() if d.is_dir()]),
                }
            )
            for sub in sorted(vdir.iterdir()):
                if not sub.is_dir():
                    continue
                if sub.name.endswith("_fm"):
                    ldb = sub / "lang_db.dat"
                    if ldb.exists():
                        try:
                            import zstandard

                            lraw = ldb.read_bytes()
                            z_magic = b"\x28\xb5\x2f\xfd"
                            z_positions: list[int] = []
                            zp = 0
                            while True:
                                idx = lraw.find(z_magic, zp)
                                if idx == -1:
                                    break
                                z_positions.append(idx)
                                zp = idx + 4
                            dctx = zstandard.ZstdDecompressor()
                            row_counts_17: list[int] = []
                            for fi in range(min(17, len(z_positions))):
                                f_start = z_positions[fi]
                                f_end = z_positions[fi + 1] if fi + 1 < len(z_positions) else len(lraw)
                                dec = dctx.decompress(lraw[f_start:f_end], max_output_size=20_000_000)
                                rc = (
                                    struct.unpack_from("<I", dec, 8)[0]
                                    if len(dec) >= 12 and dec[:6] == b"\x03\x01tad."
                                    else 0
                                )
                                row_counts_17.append(rc)
                            lang_db_summary = {
                                "path": ldb.relative_to(root).as_posix(),
                                "size_bytes": len(lraw),
                                "zstd_frame_count": len(z_positions),
                                "language_count": (len(z_positions) - 1) // 16,
                                "tables_per_language": 16,
                                "nations_count": row_counts_17[0] if len(row_counts_17) > 0 else 0,
                                "competitions_count": row_counts_17[1] if len(row_counts_17) > 1 else 0,
                                "clubs_count": row_counts_17[2] if len(row_counts_17) > 2 else 0,
                                "cities_count": row_counts_17[3] if len(row_counts_17) > 3 else 0,
                                "continents_count": row_counts_17[4] if len(row_counts_17) > 4 else 0,
                                "languages_table_count": row_counts_17[5] if len(row_counts_17) > 5 else 0,
                                "awards_count": row_counts_17[6] if len(row_counts_17) > 6 else 0,
                                "stadiums_count": row_counts_17[7] if len(row_counts_17) > 7 else 0,
                                "regions_count": row_counts_17[8] if len(row_counts_17) > 8 else 0,
                                "descriptions_count": row_counts_17[12] if len(row_counts_17) > 12 else 0,
                                "injuries_count": row_counts_17[13] if len(row_counts_17) > 13 else 0,
                                "total_rows_per_language": sum(row_counts_17[1:17]),
                            }
                        except Exception:
                            pass
                elif sub.name.endswith("_fmc"):
                    fmc_files = sorted([f for f in sub.iterdir() if f.is_file()])
                    fmc_dt = sub / "non_pl_hist_dt.dat"
                    fmc_dt_rows = (fmc_dt.stat().st_size - 8) // 24 if fmc_dt.exists() and fmc_dt.stat().st_size >= 8 else 0
                    fmc_variant_summary = {
                        "folder": sub.relative_to(root).as_posix(),
                        "file_count": len(fmc_files),
                        "total_bytes": sum(f.stat().st_size for f in fmc_files),
                        "non_pl_hist_dt_rows": fmc_dt_rows,
                        "files": [{"name": f.name, "size_bytes": f.stat().st_size} for f in fmc_files],
                    }

    return {
        "installation_inventory": installation_inventory,
        "addressable_bundles_inventory": addressable_bundles_inventory,
        "addressable_catalogs_and_manifest": {
            "catalogs": catalogs_out,
            "settings_json": aa_settings,
            "addressables_link_xml": link_xml_info,
            "manifest_dat": manifest_dat_info,
        },
        "sianim_animation_engine": sianim_summary,
        "unity_runtime_containers": unity_runtime_containers,
        "all_native_pe64_binaries": all_native_pe64_binaries,
        "database_variants_and_lang_db": {
            "db_version_count": len(db_versions),
            "db_versions": db_versions,
            "lang_db_dat": lang_db_summary,
            "fmc_console_variant": fmc_variant_summary,
        },
    }


# ==============================================================================
# 8. ONE-SHOT FULL DECOMPILED CODEBASE DUMPER (JSON + C# STUBS)
# ==============================================================================


def dump_decompiled_codebase(
    fm_install_dir: str | os.PathLike[str] | None = None,
    output_dir: str | os.PathLike[str] = "docs/decompiled_engine",
) -> dict[str, Any]:
    """Run all binary decompilation passes on ``global-metadata.dat``, ``GameAssembly.dll``, ``game_plugin.dll``,
    ``il2cpp.usym``, all 13 ``.fmf`` archives, standalone XML/JSON/DBC configs, and UnityFS UI ``.bundle`` files,
    writing JSON schemas + full C# decompiled codebase headers to ``output_dir``."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    meta_data = decompile_global_metadata(fm_install_dir)
    ga_data = decompile_gameassembly_bindings(fm_install_dir)
    usym_data = decompile_usym_symbols(fm_install_dir, max_records=2000)
    method_rva_map: dict[int, dict[str, Any]] = usym_data.pop("_method_rva_map", {})
    tables_data = extract_engine_lookup_tables(fm_install_dir)
    gp_data = decompile_game_plugin_exports(fm_install_dir)
    fmf_all_data = extract_all_fmf_and_config_archives(fm_install_dir)
    ui_bundles_data = decompile_unity_ui_bundles(fm_install_dir)
    remaining_data = decompile_all_remaining_game_files(fm_install_dir)

    # Attach il2cpp.usym RVA ranges & source file/line spans onto every method in meta_data["types"]
    if method_rva_map:
        for t in meta_data["types"]:
            for m in t["methods"]:
                rm = method_rva_map.get(m["method_index"])
                if rm:
                    m["rva_start"] = rm["rva_start"]
                    m["rva_end"] = rm["rva_end"]
                    if rm.get("source_file"):
                        m["source_file"] = rm["source_file"]
                    if rm.get("line_start") is not None:
                        m["line_start"] = rm["line_start"]
                        m["line_end"] = rm["line_end"]

    # 1. Write properties_and_contexts.json
    (out_path / "properties_and_contexts.json").write_text(
        json.dumps(
            {
                "counts": ga_data["counts"],
                "properties": ga_data["properties"],
                "contexts": ga_data["contexts"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # 2. Write entity_reference_graph.json
    (out_path / "entity_reference_graph.json").write_text(
        json.dumps(
            {
                "core_db_table_entities": ga_data["core_db_table_entities"],
                "reference_classes": ga_data["reference_classes"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # 3. Write enums_and_structs.json (all FM/SI/Assembly-CSharp enums and types)
    fm_si_types = [
        t
        for t in meta_data["types"]
        if any(k in t["image"] for k in ("FM", "SI.", "Assembly-CSharp", "SceneLoadTest"))
    ]
    (out_path / "enums_and_structs.json").write_text(
        json.dumps(
            {
                "counts": meta_data["counts"],
                "enums": meta_data["enums"],
                "fm_si_types_count": len(fm_si_types),
                "fm_si_types": fm_si_types,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # 4. Write engine_lookup_tables.json
    (out_path / "engine_lookup_tables.json").write_text(
        json.dumps(tables_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 5. Write usym_source_tree.json
    (out_path / "usym_source_tree.json").write_text(
        json.dumps(usym_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 6. Write game_plugin_native_exports.json
    (out_path / "game_plugin_native_exports.json").write_text(
        json.dumps(gp_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 7. Write all_fmf_configs_and_filters.json
    (out_path / "all_fmf_configs_and_filters.json").write_text(
        json.dumps(fmf_all_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 8. Write unity_ui_bundles_decompiled.json
    (out_path / "unity_ui_bundles_decompiled.json").write_text(
        json.dumps(ui_bundles_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 8B. Write all_remaining_files_decompiled.json
    (out_path / "all_remaining_files_decompiled.json").write_text(
        json.dumps(remaining_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 9. Generate C# stub file DecompiledReferences.cs for all 892 Reference entities
    cs_lines: list[str] = [
        "// Auto-decompiled from GameAssembly.dll (x86-64) + global-metadata.dat (IL2CPP v31/v39)",
        "// Generated by fm26save.binary_decompiler",
        "using System;",
        "using System.Collections.Generic;",
        "",
        "namespace FM.Decompiled.References",
        "{",
    ]
    for cls_name, info in sorted(ga_data["reference_classes"].items()):
        bases = ", ".join(b for b in info["derives_from"] if b != cls_name)
        inherit_clause = f" : {bases}" if bases else ""
        db_comment = (
            f" // Core DB Table #{info['db_table_index']} ({info['entity_fourcc']})"
            if info["is_core_db_table"]
            else f" // FourCC: {info['entity_fourcc']}"
        )
        cs_lines.append(f"    /// <summary>Entity ID: {info['entity_id_hex']}{db_comment}</summary>")
        cs_lines.append(f"    public class {cls_name}{inherit_clause}")
        cs_lines.append("    {")
        cs_lines.append(f"        public const uint EntityId = {info['entity_id_hex']};")
        if info["contexts"]:
            cs_lines.append(f"        // Accepted Contexts ({len(info['contexts'])}): {', '.join(info['contexts'])}")
        if info["child_entity_references"]:
            cs_lines.append(
                f"        // Child Entity Refs ({len(info['child_entity_references'])}): {', '.join(info['child_entity_references'])}"
            )
        for p in info["properties"]:
            safe_p = re.sub(r"[^A-Za-z0-9_]", "_", p)
            param_tag = " // [Parameterized]" if p in info["parameterized_properties"] else ""
            cs_lines.append(f"        public object {safe_p} {{ get; }}{param_tag}")
        cs_lines.append("    }")
        cs_lines.append("")
    cs_lines.append("}")
    (out_path / "DecompiledReferences.cs").write_text("\n".join(cs_lines), encoding="utf-8")

    # 10. Generate full C# codebase file DecompiledAllGameAssemblies.cs for all 5,350+ FM/SI/Assembly-CSharp types
    all_cs: list[str] = [
        "// Complete Decompiled C# Type, Enum, Field, Property & Method Definitions for Football Manager",
        "// Extracted from global-metadata.dat (IL2CPP v31/v39) + GameAssembly.dll + il2cpp.usym",
        "using System;",
        "",
    ]
    for t in fm_si_types:
        img = t["image"]
        ns = t["namespace"] or "Global"
        tname = re.sub(r"[^A-Za-z0-9_<>]", "_", t["name"])
        kind = "enum" if t["is_enum"] else ("struct" if t["is_valuetype"] else "class")
        all_cs.append(f"// Assembly: {img} (TypeIndex: {t['type_index']})")
        all_cs.append(f"namespace {ns}")
        all_cs.append("{")
        all_cs.append(f"    public {kind} {tname}")
        all_cs.append("    {")
        if t["is_enum"]:
            for f in t["fields"]:
                if f["name"] == "value__":
                    continue
                safe_fn = re.sub(r"[^A-Za-z0-9_]", "_", f["name"])
                dv = f.get("default_value", 0)
                all_cs.append(f"        {safe_fn} = {dv},")
        else:
            for f in t["fields"]:
                safe_fn = re.sub(r"[^A-Za-z0-9_]", "_", f["name"])
                dv_part = f" = {f['default_value']}" if "default_value" in f else ""
                all_cs.append(f"        public object {safe_fn}{dv_part}; // TypeIdx={f['type_index']} Token={f['token']}")
            for p in t["properties"]:
                safe_pn = re.sub(r"[^A-Za-z0-9_]", "_", p)
                all_cs.append(f"        public object {safe_pn} {{ get; set; }}")
            for m in t["methods"]:
                safe_mn = re.sub(r"[^A-Za-z0-9_]", "_", m["name"])
                p_sig = ", ".join(f"object {re.sub(r'[^A-Za-z0-9_]', '_', pn) or f'p{i}'}" for i, pn in enumerate(m["parameters"]))
                rva_info = (
                    f" RVA={m['rva_start']}..{m['rva_end']}"
                    + (f" Src={Path(m['source_file']).name}:{m.get('line_start')}" if m.get("source_file") else "")
                    if "rva_start" in m
                    else ""
                )
                all_cs.append(f"        public object {safe_mn}({p_sig}) => null; // MethodIdx={m['method_index']} Token={m['token']}{rva_info}")
        all_cs.append("    }")
        all_cs.append("}")
        all_cs.append("")
    (out_path / "DecompiledAllGameAssemblies.cs").write_text("\n".join(all_cs), encoding="utf-8")

    files_written = [
        "properties_and_contexts.json",
        "entity_reference_graph.json",
        "enums_and_structs.json",
        "engine_lookup_tables.json",
        "usym_source_tree.json",
        "game_plugin_native_exports.json",
        "all_fmf_configs_and_filters.json",
        "unity_ui_bundles_decompiled.json",
        "all_remaining_files_decompiled.json",
        "DecompiledReferences.cs",
        "DecompiledAllGameAssemblies.cs",
    ]

    # 11. manifest.json: which installation / build the dump was taken from (for reproducibility)
    root = resolve_fm_install_dir(fm_install_dir)
    ga_file = root / "GameAssembly.dll"
    meta_file = root / "fm_Data/il2cpp_data/Metadata/global-metadata.dat"

    def _file_info(p: Path) -> dict[str, Any]:
        if not p.exists():
            return {"exists": False}
        st = p.stat()
        return {
            "exists": True,
            "size_bytes": st.st_size,
            "modified": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            "sha1": hashlib.sha1(p.read_bytes()).hexdigest(),
        }

    manifest = {
        "generator": "fm26save.binary_decompiler.dump_decompiled_codebase",
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "fm_install_dir": str(root),
        "game": "FM27" if "27" in root.name else ("FM26" if "26" in root.name else root.name),
        "source_files": {
            "GameAssembly.dll": _file_info(ga_file),
            "global-metadata.dat": _file_info(meta_file),
        },
        "outputs": {
            name: (out_path / name).stat().st_size for name in files_written if (out_path / name).exists()
        },
    }
    (out_path / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    files_written.append("manifest.json")

    return {
        "output_dir": str(out_path.resolve()),
        "fm_install_dir": str(root),
        "files_written": files_written,
        "summary": {
            "metadata_counts": meta_data["counts"],
            "bindings_counts": ga_data["counts"],
            "usym_source_files": usym_data["source_file_count"],
            "usym_symbols": usym_data["symbol_count"],
            "usym_mapped_csharp_methods": usym_data.get("mapped_csharp_method_count", 0),
            "game_plugin_exports": gp_data["game_plugin_dll"]["export_count"],
            "game_plugin_pdata_functions": gp_data["game_plugin_dll"].get("pdata_function_table", {}).get("valid_code_functions", 0),
            "game_plugin_action_contributors": gp_data["game_plugin_dll"].get("action_contributor_vtables_count", 0),
            "game_plugin_search_filter_vtables": gp_data["game_plugin_dll"].get("search_filter_vtables_count", 0),
            "fmf_archives_count": len(fmf_all_data["fmf_archives_inventory"]),
            "person_search_filters_count": len(fmf_all_data["person_search_filters"]),
            "non_pl_hist_rows": fmf_all_data.get("non_player_career_history", {}).get("dt_row_count", 0),
            "summary_dat_clubs": fmf_all_data.get("summary_dat", {}).get("club_summary_record_count", 0),
            "ui_bundles_decompiled": ui_bundles_data["bundle_count"],
            "ui_extracted_asset_paths": ui_bundles_data["total_extracted_asset_paths"],
            "ui_unique_binding_paths": ui_bundles_data["total_unique_ui_binding_paths"],
            "ui_table_factories": ui_bundles_data.get("table_factory_count", 0),
            "ui_table_views": ui_bundles_data.get("table_view_count", 0),
            "total_installation_files": remaining_data["installation_inventory"]["total_files"],
            "total_bundles_inventoried": remaining_data["addressable_bundles_inventory"]["total_bundles"],
            "total_cab_nodes": remaining_data["addressable_bundles_inventory"]["total_cab_nodes"],
            "sianim_cat_clips": remaining_data["sianim_animation_engine"]["total_cat_clips"],
            "sianim_amd_segments": remaining_data["sianim_animation_engine"]["total_amd_segments"],
            "manifest_dat_records": remaining_data["addressable_catalogs_and_manifest"]["manifest_dat"].get("record_count", 0),
            "unity_serialized_objects": remaining_data["unity_runtime_containers"]["total_serialized_objects"],
            "native_pe64_binaries": remaining_data["all_native_pe64_binaries"]["binary_count"],
        },
    }
