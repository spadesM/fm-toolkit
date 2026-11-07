"""Render a publishable *structure-only* Markdown report from a local ``decompile-binaries --mode dump`` output.

The dump directory (``docs/decompiled_engine/...``) is git-ignored because it contains full type listings
extracted from the game. This module turns it into a compact, regenerable description of the **object
model** - assemblies, counts, the ``*Reference`` entity graph (class name, FourCC id, inheritance,
property *counts*, child entity references), registered contexts and UI bundle inventory - without
reproducing method signatures, field lists or other code-level detail.

CLI::

    fm-toolkit decompile-binaries --mode report --out-dir docs/decompiled_engine/FM27
    # -> docs/object_model/FM27_OBJECT_MODEL.md   (override with --report-path)
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

__all__ = ["render_object_model_markdown", "write_object_model_report"]


def _load(dump_dir: Path, name: str) -> Any:
    p = dump_dir / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _md_escape(s: str) -> str:
    return str(s).replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")


def _fourcc(info: dict[str, Any]) -> str:
    fc = info.get("entity_fourcc", "")
    hx = info.get("entity_id_hex", "")
    return f"`{hx}`" if fc == hx or not fc else f"`{hx}` (`{_md_escape(fc)}`)"


def render_object_model_markdown(dump_dir: str | Path) -> str:
    dump_dir = Path(dump_dir)
    manifest = _load(dump_dir, "manifest.json") or {}
    props = _load(dump_dir, "properties_and_contexts.json") or {}
    graph = _load(dump_dir, "entity_reference_graph.json") or {}
    enums = _load(dump_dir, "enums_and_structs.json") or {}
    usym = _load(dump_dir, "usym_source_tree.json") or {}
    ui = _load(dump_dir, "unity_ui_bundles_decompiled.json") or {}
    tables = _load(dump_dir, "engine_lookup_tables.json") or {}
    plugin = _load(dump_dir, "game_plugin_native_exports.json") or {}
    fmf = _load(dump_dir, "all_fmf_configs_and_filters.json") or {}

    game = manifest.get("game") or ("FM27" if "27" in json.dumps(usym.get("usym_path", "")) else "FM26")
    src = manifest.get("source_files", {})
    ga = src.get("GameAssembly.dll", {})
    out: list[str] = []
    w = out.append

    w(f"# {game} Obje Modeli (otomatik üretilmiş yapı özeti)")
    w("")
    w("> Bu dosya `fm-toolkit decompile-binaries --mode report` ile, yerelde üretilmiş (git'e girmeyen) "
      "`decompile-binaries --mode dump` çıktısından **otomatik** üretilir. Elle düzenlemeyin; yeniden üretin.")
    w("> Yalnızca **yapı bilgisi** içerir (sınıf/varlık adları, FourCC kimlikleri, kalıtım, sayılar, ilişkiler). "
      "Metod imzaları, alan listeleri ve kod yer almaz. Ayrıntı için: "
      "[DECOMPILED_ENGINE_REHBERI_TR.md](../DECOMPILED_ENGINE_REHBERI_TR.md).")
    w("")
    w("## 1. Kaynak")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| Oyun | **{game}** |")
    if manifest:
        w(f"| Üretim zamanı | {manifest.get('generated_at', '?')} |")
    if ga.get("exists"):
        w(f"| `GameAssembly.dll` | {ga['size_bytes']:,} bayt, {ga.get('modified', '?')}, SHA1 `{ga.get('sha1', '?')}` |")
    md = src.get("global-metadata.dat", {})
    if md.get("exists"):
        w(f"| `global-metadata.dat` | {md['size_bytes']:,} bayt, SHA1 `{md.get('sha1', '?')}` |")
    if not manifest:
        w("| Not | Bu döküm `manifest.json` içermiyor (eski sürümle üretilmiş); kaynak yolu `usym_source_tree.json` içinden tahmin edildi. |")
    w("")

    # 2. counts
    c = enums.get("counts", {})
    bc = props.get("counts", {})
    w("## 2. Genel sayılar")
    w("")
    w("| Öğe | Adet |")
    w("|---|---:|")
    for k, label in [("images", "Assembly (image)"), ("types", "Tip (TypeDefinition)"), ("enums", "Enum"),
                     ("fields", "Alan"), ("methods", "Metod"), ("properties", "C# property"),
                     ("parameters", "Parametre"), ("string_literals", "String literal")]:
        if k in c:
            w(f"| {label} | {c[k]:,} |")
    for k, label in [("registered_properties", "Kayıtlı binding property (FourCC)"),
                     ("registered_contexts", "Kayıtlı binding context (FourCC)"),
                     ("reference_entities", "`*Reference` varlık sınıfı"),
                     ("core_db_table_entities", "Çekirdek DB tablosu varlığı (`0x4442xxxx`)")]:
        if k in bc:
            w(f"| {label} | {bc[k]:,} |")
    if usym:
        w(f"| `il2cpp.usym` sembol kaydı | {usym.get('symbol_count', 0):,} |")
        if usym.get("mapped_csharp_method_count"):
            w(f"| `il2cpp.usym` RVA-eşlenmiş C# metodu | {usym.get('mapped_csharp_method_count', 0):,} |")
        w(f"| `il2cpp.usym` kaynak dosya yolu | {usym.get('source_file_count', 0):,} |")
    gp_dll = plugin.get("game_plugin_dll", {})
    if gp_dll.get("exists"):
        w(f"| `game_plugin.dll` native export | {gp_dll.get('export_count', 0):,} |")
        pdt = gp_dll.get("pdata_function_table", {})
        if pdt.get("valid_code_functions"):
            w(f"| `game_plugin.dll` `.pdata` C++ fonksiyonu | {pdt['valid_code_functions']:,} ({pdt.get('total_code_bytes', 0):,} bayt) |")
        if gp_dll.get("action_contributor_vtables_count"):
            w(f"| `game_plugin.dll` `ActionContributor` vtable sınıfı | {gp_dll['action_contributor_vtables_count']:,} |")
        if gp_dll.get("search_filter_vtables_count"):
            w(f"| `game_plugin.dll` `SearchFilter` vtable sınıfı | {gp_dll['search_filter_vtables_count']:,} |")
    nph = fmf.get("non_player_career_history", {})
    if nph.get("dt_row_count"):
        w(f"| `non_pl_hist_dt.dat` personel kariyer geçmişi satırı (24B) | {nph['dt_row_count']:,} |")
    sdat = fmf.get("summary_dat", {})
    if sdat.get("club_summary_record_count"):
        w(f"| `summary.dat` kulüp özet kaydı (25B) | {sdat['club_summary_record_count']:,} |")
    if ui.get("table_factory_count"):
        w(f"| UI `TableFactory` sınıfı (`ui-tablefactories`) | {ui['table_factory_count']:,} |")
        w(f"| UI `TableFactory` sütun `binding.*` yolu | {ui.get('table_factory_sort_binding_count', 0):,} |")
        w(f"| UI `TableView` / `TableSettings` şablonu (`ui-tableviews`) | {ui.get('table_view_count', 0):,} |")
    w("")

    # 3. assemblies
    types = enums.get("fm_si_types", [])
    if types:
        agg: dict[str, Counter] = defaultdict(Counter)
        for t in types:
            a = agg[t["image"]]
            a["types"] += 1
            a["enum" if t["is_enum"] else ("struct" if t["is_valuetype"] else "class")] += 1
            a["fields"] += t.get("field_count", 0)
            a["methods"] += t.get("method_count", 0)
            a["properties"] += t.get("property_count", 0)
        w("## 3. FM / SI assembly'leri")
        w("")
        w("| Assembly | Tip | class | struct | enum | Alan | Metod | Property |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|")
        for img, a in sorted(agg.items(), key=lambda kv: -kv[1]["types"]):
            w(f"| `{img}` | {a['types']:,} | {a['class']:,} | {a['struct']:,} | {a['enum']:,} | {a['fields']:,} | {a['methods']:,} | {a['properties']:,} |")
        w("")

    # 4. core DB entities
    core = graph.get("core_db_table_entities", [])
    if core:
        w("## 4. Çekirdek veritabanı tablosu varlıkları (`0x4442xxxx` = `\"DB\\0\\xNN\"`)")
        w("")
        w("Oyun veritabanının ana tabloları UI/binding katmanında bu `*Reference` sınıflarıyla temsil edilir. "
          "`Çocuk varlıklar`: bu varlığın property'lerinin döndürdüğü diğer varlık tipleri.")
        w("")
        w("| # | Sınıf | Kimlik | Türediği | Property | Parametreli | Context | Çocuk varlıklar |")
        w("|---:|---|---|---|---:|---:|---:|---|")
        for e in sorted(core, key=lambda x: x.get("db_table_index") or 0):
            der = [d for d in e.get("derives_from", []) if d != e["class_name"]]
            kids = e.get("child_entity_references", [])
            kid_s = ", ".join(f"`{k}`" for k in kids[:12]) + (f" … (+{len(kids) - 12})" if len(kids) > 12 else "")
            w(f"| {e.get('db_table_index')} | `{e['class_name']}` | `{e['entity_id_hex']}` | "
              f"{', '.join(f'`{d}`' for d in der) or '–'} | {e.get('property_count', 0):,} | "
              f"{len(e.get('parameterized_properties', [])):,} | {len(e.get('contexts', [])):,} | {kid_s or '–'} |")
        w("")

    # 5. reference class index
    refs = graph.get("reference_classes", {})
    if refs:
        by_asm = Counter(r.get("assembly", "?") for r in refs.values())
        w("## 5. `*Reference` varlık sınıfı dizini")
        w("")
        w("Her satır, UI'nin bağlanabildiği (binding) bir varlık tipidir. `Kimlik` = `get_ID` döndürdüğü 32-bit FourCC. "
          "Assembly dağılımı: " + ", ".join(f"`{a}` {n}" for a, n in by_asm.most_common()) + ".")
        w("")
        w("| Sınıf | Kimlik | Türediği | Property | Çocuk varlık |")
        w("|---|---|---|---:|---:|")
        for name, r in sorted(refs.items()):
            der = [d for d in r.get("derives_from", []) if d != name]
            w(f"| `{_md_escape(name)}` | {_fourcc(r)} | {', '.join(f'`{_md_escape(d)}`' for d in der) or '–'} | "
              f"{r.get('property_count', 0):,} | {len(r.get('child_entity_references', [])):,} |")
        w("")
        # most connected
        top = sorted(refs.values(), key=lambda r: -r.get("property_count", 0))[:25]
        w("### 5.1 En çok property'ye sahip 25 varlık")
        w("")
        w("| Sınıf | Property | Çocuk varlık |")
        w("|---|---:|---:|")
        for r in top:
            w(f"| `{_md_escape(r['class_name'])}` | {r.get('property_count', 0):,} | {len(r.get('child_entity_references', [])):,} |")
        w("")

    # 6. contexts
    ctxs = props.get("contexts", {})
    if ctxs:
        w("## 6. Kayıtlı binding context'leri")
        w("")
        w("Context'ler, parametreli property'lere (ör. bir takım veya tarih bağlamında hesaplanan değerler) verilen anahtarlardır.")
        w("")
        w("| Context | FourCC |")
        w("|---|---|")
        for k, v in sorted(ctxs.items(), key=lambda kv: kv[1]["name"].lower()):
            w(f"| `{_md_escape(v['name'])}` | `{k}` |")
        w("")

    # 7. property registry per assembly
    pr = props.get("properties", {})
    if pr:
        per = Counter(v.get("assembly", "?") for v in pr.values())
        w("## 7. Binding property kayıt defteri")
        w("")
        w(f"Toplam **{len(pr):,}** FourCC ↔ property adı eşlemesi (`PropertyRegistration.Initialise`). "
          "Tam liste yerel `properties_and_contexts.json` dosyasındadır. Assembly dağılımı:")
        w("")
        w("| Assembly | Property |")
        w("|---|---:|")
        for a, n in per.most_common():
            w(f"| `{a}` | {n:,} |")
        w("")

    # 8. enums per assembly
    en = enums.get("enums", {})
    if en:
        per = Counter(v.get("image", "?") for v in en.values())
        w("## 8. Enum dağılımı")
        w("")
        w("| Assembly | Enum |")
        w("|---|---:|")
        for a, n in per.most_common(20):
            w(f"| `{a}` | {n:,} |")
        w("")

    # 9. UI bundles
    if ui.get("bundles"):
        w("## 9. Unity UI bundle envanteri")
        w("")
        w(f"{ui.get('bundle_count', 0)} bundle, {ui.get('total_extracted_asset_paths', 0):,} asset yolu, "
          f"{ui.get('total_unique_ui_binding_paths', 0):,} benzersiz UI binding yolu.")
        if ui.get("table_factory_count"):
            w(f"Ayrıca `ui-tablefactories_assets_all.bundle` içinde **{ui['table_factory_count']:,}** `TableFactory` "
              f"ve **{ui.get('table_factory_sort_binding_count', 0):,}** `binding.*` sütun bağlaması; "
              f"`ui-tableviews_assets_all.bundle` içinde **{ui.get('table_view_count', 0):,}** `TableView`/`TableSettings` şablonu yer alır.")
        w("")
        w("| Bundle | Sıkıştırılmış | Açılmış | Asset yolu | Binding yolu |")
        w("|---|---:|---:|---:|---:|")
        for b, d in sorted(ui["bundles"].items()):
            w(f"| `{b}` | {d.get('compressed_size_bytes', 0):,} | {d.get('decompressed_size_bytes', 0):,} | "
              f"{d.get('asset_count', 0):,} | {d.get('binding_path_count', 0):,} |")
        w("")
        if ui.get("table_factories"):
            w("### 9.1 `TableFactory` sınıfları (`ui-tablefactories_assets_all.bundle`)")
            w("")
            w(", ".join(f"`{tf}`" for tf in ui["table_factories"]))
            w("")

    # 10. usym source tree
    files = usym.get("source_files", [])
    if files:
        grp: Counter = Counter()
        for f in files:
            parts = [p for p in f.replace("\\", "/").split("/") if p and p != "."]
            key = "/".join(parts[:3]) if parts and parts[0] in ("Library", "Packages", "Assets") else "/".join(parts[:2])
            if "TeamCity" in f:
                i = parts.index("work") + 2 if "work" in parts else 0
                key = "…/" + "/".join(parts[i:i + 3])
            grp[key] += 1
        w("## 10. `il2cpp.usym` kaynak ağacı (klasör bazında dosya sayısı)")
        w("")
        w("| Klasör | Dosya |")
        w("|---|---:|")
        for k, n in grp.most_common(30):
            w(f"| `{_md_escape(k)}` | {n:,} |")
        w("")

    # 11. C++ Native Engine (game_plugin.dll) & Database / FMF Tables
    w("## 11. C++ Native Motor (`game_plugin.dll`) ve Veritabanı / FMF Tabloları")
    w("")
    if gp_dll.get("exists"):
        pdt = gp_dll.get("pdata_function_table", {})
        w(f"- **`game_plugin.dll`**: `{gp_dll.get('size_bytes', 0):,}` bayt, `{gp_dll.get('export_count', 0)}` adlandırılmış export, "
          f"`.pdata` istisna dizininde **`{pdt.get('valid_code_functions', 0):,}`** C++ fonksiyonu (`{pdt.get('total_code_bytes', 0):,}` bayt makine kodu).")
        acs = gp_dll.get("action_contributor_vtables", [])
        if acs:
            w(f"- **`ActionContributor` vtable sınıfları ({len(acs)} adet)**: "
              + ", ".join(f"`{a['fourcc']}`" for a in acs[:40])
              + (f" … (+{len(acs) - 40})" if len(acs) > 40 else "") + ".")
        sfs = gp_dll.get("search_filter_vtables", [])
        if sfs:
            w(f"- **`SearchFilter` native vtable sınıfları ({len(sfs)} adet)**: "
              + ", ".join(f"`{s['fourcc']}`" for s in sfs) + ".")
    if nph.get("dt_row_count"):
        w(f"- **`non_pl_hist_{{index,id,dt}}.dat`** (`{nph.get('db_folder', '')}`): "
          f"`{nph.get('person_index_count', 0):,}` personel indeksi, `{nph.get('id_node_count', 0):,}` bağlı liste düğümü (`8` bayt), "
          f"**`{nph['dt_row_count']:,}`** kariyer geçmişi satırı (`24` bayt `<IHHHHHHBBBBi`).")
    if sdat.get("club_summary_record_count"):
        w(f"- **`summary.dat`** (`{sdat.get('path', '')}`): "
          f"`{sdat.get('continent_count', 0)}` kıta, `{sdat.get('nation_count', 0)}` ülke, "
          f"**`{sdat['club_summary_record_count']:,}`** kulüp özet kaydı (`25` bayt `\\xff\\xff\\xff\\xff\\x09`).")
    lgen = fmf.get("lang_db_general_dat", {})
    if lgen.get("zstd_frame_count"):
        w(f"- **`lang_db_general.dat`**: `{lgen['zstd_frame_count']}` Zstd çerçevesi (`{lgen.get('language_block_count', 0)}` dil × `16` tablo: "
          f"`{lgen.get('generic_competition_overrides', 0)}` turnuva, `{lgen.get('generic_club_overrides', 0)}` kulüp, "
          f"`{lgen.get('generic_award_overrides', 0)}` ödül, `{lgen.get('generic_stadium_overrides', 0)}` stadyum jenerik ad tablosu).")
    cfmf = fmf.get("constants_fmf", {})
    if cfmf:
        w("- **`constants.fmf`**: " + ", ".join(f"`{k}`" for k in cfmf) + ".")
    if tables:
        w("- **`engine_lookup_tables.json`**: " + ", ".join(f"`{k}`" for k in tables) + ".")
    if fmf:
        inv = fmf.get("fmf_archives_inventory", {})
        w(f"- **`all_fmf_configs_and_filters.json`**: {len(inv)} `.fmf` arşivi envanteri, "
          f"{len(fmf.get('person_search_filters', []))} oyuncu arama filtresi ve ayar/mağaza/versus XML'leri.")
    w("")
    return "\n".join(out)


def write_object_model_report(dump_dir: str | Path, report_path: str | Path | None = None) -> dict[str, Any]:
    dump_dir = Path(dump_dir)
    md = render_object_model_markdown(dump_dir)
    if report_path is None:
        manifest = _load(dump_dir, "manifest.json") or {}
        game = manifest.get("game") or "FM"
        report_path = Path("docs/object_model") / f"{game}_OBJECT_MODEL.md"
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(md + "\n", encoding="utf-8")
    return {"report_path": str(report_path.resolve()), "bytes": len(md.encode("utf-8")), "dump_dir": str(dump_dir)}
