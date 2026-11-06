import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from annotate_sorting_usym import dump_annotated, pe, meta, hdr, rva_to_method_name, rva_to_end, image_base, va_to_off, types_off, methods_off, get_mstr
import UnityPy
from fm26save.binary_decompiler import resolve_fm_install_dir

# 1. Check all StreamedTableFactory assets in ui-tablefactories_assets_all.bundle for sort paths!
root = resolve_fm_install_dir()
aa_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"
tf_bundle = aa_dir / "ui-tablefactories_assets_all.bundle"
env = UnityPy.load(str(tf_bundle))

print("=== 1. Inspect m_rowData sort paths across ALL TableFactories in ui-tablefactories_assets_all.bundle ===")
with_binding_prefix = []
without_binding_prefix = []
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        if "m_rowData" in tree and "m_parameters" in tree:
            name = tree.get("m_Name", "")
            params = tree.get("m_parameters", [])
            sorts = []
            for rd in tree.get("m_rowData", []):
                s = rd.get("m_sort", "")
                if s:
                    sorts.append((rd.get("m_column", ""), s))
            if sorts:
                has_binding = any(s.startswith("binding.") for _, s in sorts)
                if has_binding:
                    with_binding_prefix.append((name, params, sorts))
                else:
                    without_binding_prefix.append((name, params, sorts))

print(f"TableFactories WITH 'binding.' prefix in m_sort ({len(with_binding_prefix)}):")
for name, params, sorts in with_binding_prefix:
    print(f"  - {name}: params={params[:3]} sorts={sorts[:4]}")

print(f"\nTableFactories WITHOUT 'binding.' prefix in m_sort ({len(without_binding_prefix)}):")
for name, params, sorts in without_binding_prefix[:25]:
    print(f"  - {name}: params={params[:3]} sorts={sorts[:4]}")
